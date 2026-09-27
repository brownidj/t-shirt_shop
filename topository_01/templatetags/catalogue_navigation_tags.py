from django import template

from oscar.apps.catalogue.models import Product


register = template.Library()


@register.simple_tag(takes_context=True)
def design_navigation(context):
    """Return adjacent public designs from the displayed product's category."""
    product = context["product"]
    category = product.get_categories().first()
    navigation = {"category": category, "previous": None, "next": None}

    if not category or product.product_class.name != "Designs":
        return navigation

    designs = list(
        Product.objects.filter(
            categories=category,
            product_class__name="Designs",
            parent__isnull=True,
            is_public=True,
        ).order_by("title", "pk")
    )
    try:
        position = next(
            index for index, design in enumerate(designs) if design.pk == product.pk
        )
    except StopIteration:
        return navigation

    if len(designs) > 1:
        navigation["previous"] = designs[(position - 1) % len(designs)]
        navigation["next"] = designs[(position + 1) % len(designs)]
    return navigation
