#!/usr/bin/env python3
import sys
from decimal import Decimal

from django.db import transaction
from oscar.core.loading import get_model

# Oscar models
Product = get_model("catalogue", "Product")
ProductAttribute = get_model("catalogue", "ProductAttribute")
ProductAttributeValue = get_model("catalogue", "ProductAttributeValue")
Partner = get_model("partner", "Partner")
StockRecord = get_model("partner", "StockRecord")

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

# List of design UPCs to generate variants for
DESIGN_UPCS = [
    "A_HU_01",
    # "P_CPR_S",
    # "P_TD_02",
    # "P_TDF_01",
]

TSHIRT_PRODUCT_CLASS_NAME = "T-shirt"
STYLE_ATTRIBUTE = "selected_style"
COLOUR_ATTRIBUTE = "selected_colour"
SIZE_ATTRIBUTE = "selected_size"

PARTNER_NAME = "Topository Fulfilment"
DEFAULT_PRICE = Decimal("45.00")
DEFAULT_CURRENCY = "AUD"
DEFAULT_STOCK = 9999


# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def get_partner():
    partner, _ = Partner.objects.get_or_create(name=PARTNER_NAME)
    return partner


def get_variant_attributes():
    """Ensure the 3 variant attributes exist (style, colour, size)."""
    attrs = {}
    for code, name in [
        (STYLE_ATTRIBUTE, "Selected T-shirt Style"),
        (COLOUR_ATTRIBUTE, "Selected Colour"),
        (SIZE_ATTRIBUTE, "Selected Size"),
    ]:
        pa, _ = ProductAttribute.objects.get_or_create(
            code=code,
            defaults={"name": name, "type": "text"},
        )
        attrs[code] = pa
    return attrs


def get_designs():
    """Return only the specific design UPCs requested."""
    designs = list(Product.objects.filter(
        upc__in=DESIGN_UPCS,
        structure=Product.PARENT
    ))

    missing = set(DESIGN_UPCS) - {d.upc for d in designs}
    if missing:
        print("⚠ WARNING: Missing design UPCs:", ", ".join(missing))

    if not designs:
        print("❌ No valid design parents found.")
        sys.exit(1)

    print(f"→ Found {len(designs)} design parents to process.")
    for d in designs:
        print(f"   - {d.upc}: {d.title}")

    return designs


def get_tshirt_styles():
    """Return all standalone T-shirt style products."""
    styles = Product.objects.filter(
        structure=Product.STANDALONE,
        product_class__name=TSHIRT_PRODUCT_CLASS_NAME,
    )
    if not styles.exists():
        print(f"❌ No standalone T-shirt styles found (ProductClass='{TSHIRT_PRODUCT_CLASS_NAME}').")
        sys.exit(1)

    print(f"→ Found {styles.count()} T-shirt styles.")
    return styles


def make_partner_sku(design_upc, style_upc, colour, size):
    colour_code = colour.replace(" ", "-")
    size_code = size.replace(" ", "-")
    return f"{design_upc}-{style_upc}-{colour_code}-{size_code}"


def create_child_variant(parent, style, colour, size, attrs, partner):
    """Create one variant child product."""
    sku = make_partner_sku(parent.upc, style.upc, colour, size)

    if StockRecord.objects.filter(partner=partner, partner_sku=sku).exists():
        print(f"   • SKIP already exists: {sku}")
        return

    child = Product.objects.create(
        title=f"{parent.title} – {style.upc} – {colour} – {size}",
        structure=Product.CHILD,
        parent=parent,
        product_class=parent.product_class,
    )

    # Assign style/colour/size attributes
    ProductAttributeValue.objects.create(
        product=child,
        attribute=attrs[STYLE_ATTRIBUTE],
        value_text=style.upc,
    )
    ProductAttributeValue.objects.create(
        product=child,
        attribute=attrs[COLOUR_ATTRIBUTE],
        value_text=colour,
    )
    ProductAttributeValue.objects.create(
        product=child,
        attribute=attrs[SIZE_ATTRIBUTE],
        value_text=size,
    )

    # Create stock record
    StockRecord.objects.create(
        product=child,
        partner=partner,
        partner_sku=sku,
        price_excl_tax=DEFAULT_PRICE,
        price_currency=DEFAULT_CURRENCY,
        num_in_stock=DEFAULT_STOCK,
    )

    print(f"   ✓ Created {child.title}")


# --------------------------------------------------
# MAIN VARIANT GENERATOR
# --------------------------------------------------

@transaction.atomic
def generate_variants():
    print("========================================")
    print(" GENERATING T-SHIRT VARIANTS (UPC LIST)")
    print("========================================")

    partner = get_partner()
    attrs = get_variant_attributes()
    designs = get_designs()
    styles = get_tshirt_styles()

    for parent in designs:
        print(f"\n→ GENERATING for {parent.upc}: {parent.title}")

        for style in styles:
            available_colours = getattr(style.attr, "available_colours", [])
            available_sizes = getattr(style.attr, "available_sizes", [])

            if not available_colours or not available_sizes:
                print(f"   ⚠ Style {style.upc} missing colours or sizes — skipping.")
                continue

            for colour in available_colours:
                for size in available_sizes:
                    create_child_variant(parent, style, colour, size, attrs, partner)

    print("\n✓ DONE!")


if __name__ == "__main__":
    generate_variants()