from core.permissions import is_admin, is_contributor


def can_create(user):
    return is_contributor(user)


def can_edit(user, guide):
    return is_admin(user) or (is_contributor(user) and guide.author_id == user.pk)


def can_delete(user, guide):
    return is_admin(user) or (user.is_authenticated and guide.author_id == user.pk)
