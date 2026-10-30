from decimal import Decimal

from .models import CategoryImpactProfile, ImpactEstimate, RepairLog

DEFAULT_MASS_KG = Decimal("0.30")
DEFAULT_REPLACEMENT_COST = 2_000_000


def log_device(log):
    return log.device or (log.guide.device if log.guide_id else None)


def find_profile(device):
    category = device.category
    for _ in range(10):  
        if category is None:
            break
        profile = CategoryImpactProfile.objects.filter(category=category).first()
        if profile:
            return profile
        category = category.parent
    return None


def profile_values(device):
    profile = find_profile(device)
    if profile:
        return profile.avg_mass_kg, profile.replacement_cost
    return DEFAULT_MASS_KG, DEFAULT_REPLACEMENT_COST


def impact_basis(device):
    profile = find_profile(device) if device else None
    return profile.category.name if profile else None


def sync_impact(log):
    device = log_device(log)
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
