import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "topository_01.settings")
django.setup()

from oscar.core.loading import get_model

Product = get_model('catalogue', 'Product')

UPCS = ["P_TD_0","P_TD_02", "P_TD_02", "P_TDF_01", "P_CPR_S", "A_HU_01"]  # add more design UPCs here

for upc in UPCS:
    try:
        p = Product.objects.get(upc=upc)
    except Product.DoesNotExist:
        print(f"❌ No product with UPC {upc}")
        continue

    p.structure = Product.PARENT
    p.save()
    print(f"✓ Updated {p.title} (UPC={upc}) to PARENT")