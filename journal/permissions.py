from core.permissions import is_member


def can_use_journal(user):
    return is_member(user)
