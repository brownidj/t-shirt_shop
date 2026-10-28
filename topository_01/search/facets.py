"""Keep catalogue pagination tied to designs that still exist and are public."""
from oscar.apps.search.facets import *  # noqa: F401,F403
from oscar.apps.search.facets import base_sqs as oscar_base_sqs
from oscar.core.loading import get_model


def base_sqs():
    Product = get_model("catalogue", "Product")
    # Stale index entries otherwise consume page slots even though render_product
    # cannot display them. Apply this before counts and pagination, not in HTML.
    visible_ids = list(
        Product.objects.filter(
            is_public=True, structure__in=[Product.STANDALONE, Product.PARENT]
        ).values_list("pk", flat=True)
    )
    return oscar_base_sqs().models(Product).filter(django_id__in=visible_ids)
