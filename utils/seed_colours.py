from oscar.core.loading import get_model

AttributeOptionGroup = get_model('catalogue', 'AttributeOptionGroup')
AttributeOption = get_model('catalogue', 'AttributeOption')

# === master colour set (add to this anytime ===)
COLOURS = [
    "Army", "Arctic Blue", "Atlantic", "Autumn", "Berry", "Black", "Bone", "Bright Royal",
    "Bubblegum", "Burgundy", "Camel", "Cardinal", "Carolina Blue", "Charcoal", "Charity Pink",
    "Charlotte", "Chestnut", "Citrus", "Clay", "Coal", "Cobalt", "Copper", "Coral", "Cypress",
    "Dark Chocolate", "Ecru", "Eucalyptus", "Fire", "Forest Green", "Gold", "Granite", "Grey Marle",
    "Hydro", "Jade", "Kelly Green", "Khaki", "Lapis", "Lemon", "Lemonade", "Light Grey", "Lime",
    "Mauve", "Midnight Blue", "Mineral", "Mushroom", "Mustard", "Natural", "Navy", "Orange",
    "Pale Blue", "Pale Pink", "Petrol Blue", "Pine Green", "Pink", "Pistachio", "Plum", "Powder",
    "Purple", "Red", "Rose", "Safari", "Sage", "Sand", "Seafoam", "Slate Blue", "Smoke", "Topaz",
    "Walnut", "White", "Yellow"
]

# Create or get the T-shirt Colours group
group, created = AttributeOptionGroup.objects.get_or_create(
    code="tshirt_colours",
    defaults={"name": "T-shirt Colours"}
)
print(f"{'Created' if created else 'Found existing'} group: {group.name}")

# Fetch existing colour names (case-insensitive)
existing = set(
    AttributeOption.objects.filter(group=group)
    .values_list("option", flat=True)
)

added = []
skipped = []

for colour in COLOURS:
    if colour in existing:
        skipped.append(colour)
    else:
        AttributeOption.objects.create(group=group, option=colour)
        added.append(colour)

# Print summary
print("\n✅ Done seeding T-shirt colours.")
if added:
    print("🆕 Added:", ", ".join(added))
if skipped:
    print("⏩ Skipped existing:", ", ".join(skipped))