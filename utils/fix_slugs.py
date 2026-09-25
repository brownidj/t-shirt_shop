import os
import django
from django.utils.text import slugify

# Initialise Django when running as a standalone script:
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "topository_01.settings")
django.setup()

from oscar.apps.catalogue.models import Product

# --------------------------------------------------
# CONFIG
# --------------------------------------------------

# If True, only print what would change – no DB writes.
DRY_RUN = False


def is_design_parent(product):
    """Heuristic to detect design parents (adjust as needed)."""
    # Your design UPCs start with A_ or P_
    return (
            product.structure == Product.PARENT
            and product.upc
            and (product.upc.startswith("A_") or product.upc.startswith("P_"))
    )


def ensure_unique_slug(product, base_slug):
    """Ensure the slug is unique across all products."""
    slug = base_slug
    counter = 2

    while Product.objects.filter(slug=slug).exclude(id=product.id).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1

    return slug


def fix_child_slugs(parent):
    """
    Fix slugs for all children of a given parent.

    Uses the child title to generate the slug, with a fallback that
    incorporates the parent slug and child id to guarantee uniqueness.
    """
    children = parent.children.all()
    changed = 0

    for c in children:
        base = slugify(c.title)
        if not base:
            base = f"{slugify(parent.title) or parent.slug}-{c.id}"

        new_slug = ensure_unique_slug(c, base)

        if c.slug == new_slug:
            # Already consistent
            continue

        print(f"    → Child {c.id} ({c.upc or 'no UPC'}):")
        print(f"        OLD: {c.slug}")
        print(f"        NEW: {new_slug}")

        if not DRY_RUN:
            c.slug = new_slug
            c.save()

        changed += 1

    return changed


def fix_slugs():
    parents = Product.objects.filter(structure=Product.PARENT)

    print(f"Found {parents.count()} parent products.")
    if DRY_RUN:
        print("DRY_RUN is ON – no changes will be written.\n")

    parents_changed = 0
    children_changed_total = 0

    for p in parents:
        if not is_design_parent(p):
            continue

        # ----- Fix parent slug -----
        new_slug_base = slugify(p.title) or (p.upc.lower() if p.upc else "")
        if not new_slug_base:
            # If we somehow have neither title nor UPC usable, skip safely
            print(f"⚠ Skipping {p.id}: cannot derive slug from title/UPC.")
            continue

        new_slug = ensure_unique_slug(p, new_slug_base)

        if p.slug == new_slug:
            print(f"✓ {p.upc}: parent slug OK → '{p.slug}'")
        else:
            print(f"→ Fixing parent slug for {p.upc}:")
            print(f"    OLD: {p.slug}")
            print(f"    NEW: {new_slug}")

            if not DRY_RUN:
                p.slug = new_slug
                p.save()

            parents_changed += 1

        # ----- Fix child slugs for this parent -----
        child_changed = fix_child_slugs(p)
        if child_changed:
            print(f"    ✅ Updated {child_changed} child slug(s) for {p.upc}")
        children_changed_total += child_changed

    print("\nDone.")
    print(f"Updated {parents_changed} parent slug(s).")
    print(f"Updated {children_changed_total} child slug(s).")
    if DRY_RUN:
        print("Note: DRY_RUN was ON – no changes were actually saved.")


if __name__ == "__main__":
    fix_slugs()