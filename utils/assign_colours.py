import django
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "topository_01.settings")
django.setup()

from oscar.core.loading import get_model

Product = get_model('catalogue', 'Product')
Attribute = get_model('catalogue', 'ProductAttribute')
AttributeOption = get_model('catalogue', 'AttributeOption')

# ---- EDIT THIS LIST FOR YOUR T-SHIRT STYLE ----
COLOURS_TO_ASSIGN = [
    "Arctic Blue", "Army", "Atlantic", "Autumn", "Berry", "Black", "Bone",
    "Bright Royal", "Bubblegum", "Burgundy", "Camel", "Cardinal",
    "Carolina Blue", "Charcoal", "Charity Pink", "Charlotte", "Chestnut",
    "Citrus", "Clay", "Coal", "Cobalt", "Copper", "Coral", "Cypress",
    "Dark Chocolate", "Ecru", "Eucalyptus", "Fire", "Fog Blue",
    "Forest Green", "Gold", "Granite", "Grey Marle", "Hydro", "Jade",
    "Kelly Green", "Khaki", "Kiwi", "Lapis", "Lemonade", "Light Grey",
    "Lime", "Mauve", "Midnight Blue", "Mineral", "Moss", "Mushroom",
    "Mustard", "Natural", "Navy", "Orange", "Orchid", "Pale Blue",
    "Pale Pink", "Petrol Blue", "Pine Green", "Pink", "Pistachio", "Plum",
    "Powder", "Purple", "Red", "Safari", "Sage", "Sand", "Seafoam",
    "Shadow", "Slate Blue", "Smoke", "Sunset", "Topaz", "Walnut",
    "White", "Yellow", "cocoa"
]

# ---- SELECT YOUR PRODUCT BY UPC OR ID ----
UPC = "AS-5001"

product = Product.objects.get(upc=UPC)
print(f"Updating colours for: {product.title}")

# get the product attribute definition
attr = Attribute.objects.get(code="available_colours")
option_group = attr.option_group

# convert colour names → AttributeOption objects
options = []
for colour in COLOURS_TO_ASSIGN:
    opt, created = AttributeOption.objects.get_or_create(
        group=option_group,
        option=colour
    )
    if created:
        print(f"🆕 Created missing colour '{colour}' in option group '{option_group.name}'")
    options.append(opt)

# assign option objects
product.attr.available_colours = options
product.save()

print(f"✓ Updated {len(options)} colours for {product.title}.")