from core.models import UserProfile

Role = UserProfile.Role


def _role(user):
    if not user.is_authenticated:
        return None
    if user.is_superuser:
        return Role.ADMIN
    return user.profile.role


def is_member(user):
    """True kalau user udah login."""
    return _role(user) is not None
