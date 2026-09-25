# utils/update_prices.py
import os
from decimal import Decimal

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "topository_01.settings")
django.setup()

from oscar.core.loading import get_model

Product = get_model("catalogue", "Product")
StockRecord = get_model("partner", "StockRecord")

# List of parent UPCs whose variants' prices should be updated
PARENT_UPCS = [
    "A_HU_01",
    "P_TD_01",
    "P_TD_02",
    "P_TDF_01",
    "P_CPR_S",
]

NEW_PRICE = Decimal("45.00")


def update_prices():
    """
    Update the price of all StockRecords for all variant products
    whose parent UPC is in PARENT_UPCS.
    """
    missing_variants = []
    total_parents = 0
    total_variants = 0
    total_records = 0

    for parent_upc in PARENT_UPCS:
        try:
            parent = Product.objects.get(upc=parent_upc, structure=Product.PARENT)
        except Product.DoesNotExist:
            print(f"❌ No parent product with UPC={parent_upc}")
            continue

        total_parents += 1
        children = Product.objects.filter(parent=parent)
        num_children = children.count()
        total_variants += num_children

        print(f"\nParent {parent_upc} – '{parent.title}': {num_children} variants")

        for child in children:
            records = StockRecord.objects.filter(product=child)

            # If there are no stock records, note that this variant was not updated
            if not records.exists():
                print(
                    f"⚠ No stock records for variant '{child.title}' "
                    f"(id={child.id}, upc={child.upc}) – NOT UPDATED"
                )
                missing_variants.append(child)
                continue

            for record in records:
                # Oscar 4.1: use the `price` field, not `price_excl_tax`
                if hasattr(record, "price"):
                    record.price = NEW_PRICE

                if hasattr(record, "price_currency") and not record.price_currency:
                    record.price_currency = "AUD"

                record.save()
                total_records += 1
                print(f"✓ Updated {child.title} -> {NEW_PRICE} {record.price_currency}")

    if missing_variants:
        print("\nThe following variants had no stock records and were NOT updated:")
        for v in missing_variants:
            print(f" - {v.title} (id={v.id}, upc={v.upc})")
    else:
        print("\nAll variants had at least one stock record updated.")

    print(
        f"\nDone. Updated {total_records} stock records "
        f"across {total_parents} parent(s) and {total_variants} variant(s)."
    )


if __name__ == "__main__":
    update_prices()