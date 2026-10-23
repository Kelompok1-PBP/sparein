from decimal import Decimal

from .models import CategoryImpactProfile, ImpactEstimate, RepairLog

DEFAULT_MASS_KG = Decimal("0.30")
DEFAULT_REPLACEMENT_COST = 2_000_000


def profile_values(device):
    category = device.category
    for _ in range(10):  
        if category is None:
            break
        profile = CategoryImpactProfile.objects.filter(category=category).first()
        if profile:
            return profile.avg_mass_kg, profile.replacement_cost
        category = category.parent
    return DEFAULT_MASS_KG, DEFAULT_REPLACEMENT_COST


def sync_impact(log):
    device = log.device or (log.guide.device if log.guide_id else None)
    if log.status != RepairLog.Status.SUCCEEDED or device is None:
        ImpactEstimate.objects.filter(log=log).delete()
        return None
    mass, replacement = profile_values(device)
    estimate, _ = ImpactEstimate.objects.update_or_create(
        log=log,
        defaults={
            "waste_avoided_kg": mass,
            "cost_avoided": max(replacement - log.cost_spent, 0),
        },
    )
    return estimate
