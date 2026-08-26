import re


def slugify(text, existing_slugs) -> str:
    """generates unique slugs for idol"""
    base = text.lower().strip()
    base = re.sub(r"[^a-z0-9\s-]", "", base)
    base = re.sub(r"\s+", "-", base)
    slug = base
    counter = 2
    while slug in existing_slugs:
        slug = f"{base}-{counter}"
        counter += 1
    return slug
