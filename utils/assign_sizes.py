import django
import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "topository_01.settings")
django.setup()

from oscar.core.loading import get_model

Product = get_model('catalogue', 'Product')
Attribute = get_model('catalogue', 'ProductAttribute')
AttributeOption = get_model('catalogue', 'AttributeOption')

# ---- EDIT THIS LIST FOR YOUR T-SHIRT STYLE ----
SIZES_TO_ASSIGN = [
    "XSM", "SML", "MED", "LGE", "XLG", "2XL", "3XL",
]

# ---- SELECT YOUR PRODUCT BY UPC OR ID ----
UPC = "AS-4010"  # change to AS-4010, AS-5051, etc. as needed

product = Product.objects.get(upc=UPC)
print(f"Updating sizes for: {product.title}")

# get the product attribute definition
try:
    attr = Attribute.objects.get(code="available_sizes")
except Attribute.DoesNotExist:
    print("❌ ERROR: ProductAttribute with code 'available_sizes' does not exist.")
    print("➡ Fix this in Dashboard → Catalogue → Product Types → T-shirt → Add an attribute named 'Available Sizes' with code 'available_sizes', type 'Multi Option', bound to your 'T-shirt Sizes' option group.")
    sys.exit(1)
option_group = attr.option_group

# convert size names → AttributeOption objects, auto-creating missing ones
options = []
for size in SIZES_TO_ASSIGN:
    opt, created = AttributeOption.objects.get_or_create(
        group=option_group,
        option=size,
    )
    if created:
        print(f"🆕 Created missing size '{size}' in option group '{option_group.name}'")
    options.append(opt)

# assign option objects
product.attr.available_sizes = options
product.save()

print(f"✓ Updated {len(options)} sizes for {product.title}.")