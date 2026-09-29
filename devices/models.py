from django.utils.text import slugify


def unique_slug(model, value):
    base = slugify(value)[:200] or "item"
    slug, n = base, 2
    while model.objects.filter(slug=slug).exists():
        slug, n = f"{base}-{n}", n + 1
    return slug
