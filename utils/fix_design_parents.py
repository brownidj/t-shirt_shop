"""
Self-healing script for design products in Oscar 4.1.

This script:
 - Finds all products whose UPC begins with design prefixes.
 - Forces them to be PARENT products.
 - Ensures they have no parent assigned.
 - Leaves child variants unchanged.
 - Prints a clean summary of what was updated.

Run with:
    python3 manage.py shell < utils/fix_design_parents.py
"""

from django.db import transaction
from django.db.models import Q
from oscar.apps.catalogue.models import Product

# Adjust these prefixes if you add new design conventions
DESIGN_PREFIXES = ("A_", "P_", "P_T", "P_C")


def find_design_parents():
    """Return all non-child design products based on UPC prefixes."""
    q = Q()
    for prefix in DESIGN_PREFIXES:
        q |= Q(upc__startswith=prefix)

    return (
        Product.objects
        .filter(q)
        .exclude(structure=Product.CHILD)
        .order_by("id")
    )


@transaction.atomic
def fix_design_parents():
    print("🔍 Scanning for design products...\n")

    design_products = find_design_parents()

    if not design_products.exists():
        print("❌ No design products found.")
        return

    updated = 0
    skipped = 0

    for product in design_products:
        if product.structure == Product.PARENT and product.parent_id is None:
            skipped += 1
            continue

        product.structure = Product.PARENT
        product.parent = None
        product.save()

        print(f"🔧 FIXED: {product.upc} → structure=PARENT")
        updated += 1

    print("\n====== SUMMARY ======")
    print(f"PARENT products updated: {updated}")
    print(f"Already correct: {skipped}")
    print("=====================\n")


# Execute when run via manage.py shell redirection
fix_design_parents()