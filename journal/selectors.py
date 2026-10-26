from django.db.models import Count, Sum

from .models import ImpactEstimate, RepairLog


def logs_for(user):
    return RepairLog.objects.filter(user=user).select_related(
        "guide", "device", "impact"
    )


def _totals(qs):
    data = qs.aggregate(
        count=Count("pk"), waste=Sum("waste_avoided_kg"), cost=Sum("cost_avoided")
    )
    return {
        "repairs": data["count"],
        "waste_avoided_kg": data["waste"] or 0,
        "cost_avoided": data["cost"] or 0,
    }


def user_impact_summary(user):
    return _totals(ImpactEstimate.objects.filter(log__user=user))


def site_impact_totals():
    return _totals(ImpactEstimate.objects.all())
