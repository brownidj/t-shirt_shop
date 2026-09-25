# utils/delete_variants.py
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "topository_01.settings")
django.setup()

from oscar.core.loading import get_model

Product = get_model("catalogue", "Product")

# Use parent UPC instead of ID
PARENT_UPC = "P_TD_02"   # History of the Universe

def delete_variants():
    try:
        parent = Product.objects.get(upc=PARENT_UPC, structure=Product.PARENT)
    except Product.DoesNotExist:
        print(f"❌ No parent product with UPC '{PARENT_UPC}'")
        return

    children = Product.objects.filter(parent=parent)
    total = children.count()
    print(f"Found {total} child variants under parent '{parent.title}'")

    if total == 0:
        print("Nothing to delete.")
        return

    confirm = input(
        f"⚠ Are you sure you want to delete ALL {total} child products for UPC {PARENT_UPC}? (yes/no): "
    )

    if confirm.lower() != "yes":
        print("Cancelled.")
        return

    deleted = 0
    for child in children:
        print(f"🗑 Deleting {child.title} (ID={child.id})")
        child.delete()
        deleted += 1

    print(f"\n✅ Done. Deleted {deleted} variant products.")

if __name__ == "__main__":
    delete_variants()