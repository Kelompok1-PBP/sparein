from core.models import UserProfile

Role = UserProfile.Role


def _role(user):
    if not user.is_authenticated:
        return None
    if user.is_superuser:
        return Role.ADMIN
    return user.profile.role
