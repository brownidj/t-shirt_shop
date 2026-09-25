"""
Generate variant products for each design parent.

Oscar 4.1 compatible:
 - Uses AttributeOptionGroup / AttributeOption
 - Uses ProductAttributeValue
 - No OptionValue model (does not exist)
"""

from decimal import Decimal

from oscar.apps.catalogue.models import (
    Product,
    ProductClass,
    ProductAttribute,
    ProductAttributeValue,
    AttributeOptionGroup,
    AttributeOption,
)
from oscar.apps.partner.models import Partner, StockRecord



# ------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------

DESIGN_UPCS = [
    "A_HU_01",
    "P_CPR_S",
    "P_TD_02",
    "P_TDF_01",
]

TSHIRT_STYLE_UPC = "AS-5001"

PRICE = Decimal("45.00")
PARTNER_NAME = "Topository Fulfilment"
DEFAULT_STOCK = 9999

SIZES = ["XSM", "SML", "MED", "LGE", "XLG", "2XL", "3XL"]


# ------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------

def get_design_parents():
    """Return parent product objects for selected UPCs."""
    qs = Product.objects.filter(upc__in=DESIGN_UPCS)
    return list(qs)


def get_tshirt_style():
    """Return the T-shirt style product (AS-5001)."""
    try:
        return Product.objects.get(upc=TSHIRT_STYLE_UPC)
    except Product.DoesNotExist:
        raise RuntimeError(f"🔥 T-shirt style {TSHIRT_STYLE_UPC} not found!")


def get_colour_group():
    """Get the AttributeOptionGroup for colours."""
    try:
        return AttributeOptionGroup.objects.get(name="T-shirt Colours")
    except AttributeOptionGroup.DoesNotExist:
        raise RuntimeError("🔥 AttributeOptionGroup 'T-shirt Colours' not found!")


def get_colour_options(colour_group):
    """Return dict of AttributeOptions keyed by name."""
    return {opt.option: opt for opt in colour_group.options.all()}


def get_or_create_partner():
    partner, _ = Partner.objects.get_or_create(name=PARTNER_NAME)
    return partner


# ------------------------------------------------------------
# MAIN GENERATOR
# ------------------------------------------------------------

def generate_variants():
    print("🔍 Fetching data…")

    parents = get_design_parents()
    style = get_tshirt_style()
    colour_group = get_colour_group()
    colours = get_colour_options(colour_group)
    partner = get_or_create_partner()

    # Fetch attribute definitions
    attr_style = ProductAttribute.objects.get(code="tshirt_style")
    attr_colour = ProductAttribute.objects.get(code="selected_colour")
    attr_size = ProductAttribute.objects.get(code="selected_size")

    print(f"🎨 Found {len(colours)} colour options.")
    print(f"👕 Found {len(parents)} design parents.")
    print(f"📦 Using partner: {partner.name}")

    for parent in parents:
        print(f"\n==============================")
        print(f"✨ Generating variants for {parent.upc} ({parent.title})")
        print("==============================")

        for colour_name, colour_obj in colours.items():
            for size in SIZES:

                variant_upc = f"{parent.upc}-{TSHIRT_STYLE_UPC}-{colour_name}-{size}"

                # Avoid duplicates
                existing = Product.objects.filter(parent=parent, upc=variant_upc).first()
                if existing:
                    print(f"⚠ Skipping existing variant {variant_upc}")
                    continue

                # Create child product
                child = Product.objects.create(
                    parent=parent,
                    structure=Product.CHILD,
                    upc=variant_upc,
                    title=f"{parent.title} ({colour_name}, {size})",
                    product_class=style.product_class,  # inherits T-shirt class
                )

                # ---- Assign attributes ----
                ProductAttributeValue.objects.create(
                    product=child,
                    attribute=attr_style,
                    value_text=TSHIRT_STYLE_UPC,
                )
                ProductAttributeValue.objects.create(
                    product=child,
                    attribute=attr_colour,
                    value_option=colour_obj,
                )
                ProductAttributeValue.objects.create(
                    product=child,
                    attribute=attr_size,
                    value_text=size,
                )

                # ---- Create StockRecord ----
                partner_sku = variant_upc  # guaranteed unique
                StockRecord.objects.create(
                    product=child,
                    partner=partner,
                    partner_sku=partner_sku,
                    price=PRICE,
                    num_in_stock=DEFAULT_STOCK,
                )

                print(f"✔ Created {variant_upc}")

    print("\n🎉 DONE — All variants generated successfully!")


# ------------------------------------------------------------
# RUN SCRIPT
# ------------------------------------------------------------

if __name__ == "__main__":
    generate_variants()