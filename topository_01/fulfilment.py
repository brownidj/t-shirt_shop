"""Private, staff-initiated print fulfilment email support."""

from pathlib import Path

from django.conf import settings
from django.core.mail import EmailMessage


def _product_attributes(product):
    """Return configured style, colour and size values for a shirt product."""
    values = {}
    if product is None:
        return values
    for value in product.attribute_values.select_related("attribute", "value_option"):
        text = value.value_as_text
        values[value.attribute.code] = str(text) if text is not None else ""
    return values


def artwork_for_line(line):
    """Find the non-public, print-ready artwork master for an order line.

    Artwork is indexed by the parent design UPC, e.g. ``cambroernid-02.png``.
    We never fall back to the public catalogue image: a fulfilment request must
    fail visibly until a print-grade master has been stored privately.
    """
    product = line.product
    design = getattr(product, "parent", None) or product
    upc = getattr(design, "upc", "")
    if not upc:
        return None
    matches = sorted(Path(settings.PRIVATE_DESIGN_ARTWORK_ROOT).glob(f"{upc}.*"))
    return next((path for path in matches if path.is_file()), None)


def fulfilment_lines(order):
    """Prepare supplier-only line specifications and their master artwork."""
    lines = []
    for line in order.lines.select_related("product", "product__parent"):
        attributes = _product_attributes(line.product)
        lines.append(
            {
                "title": line.title,
                "quantity": line.quantity,
                "style": attributes.get("tshirt_style", "Not recorded"),
                "colour": attributes.get("colour", "Not recorded"),
                "size": attributes.get("size", "Not recorded"),
                "artwork": artwork_for_line(line),
            }
        )
    return lines


def build_fulfilment_email(order):
    """Build the internal-only request to Garment Printing Group.

    The caller must check both the configured recipient and artwork before
    sending.  No shopper email address, shop retail price, or supplier price is
    included in the message.
    """
    recipient = settings.FULFILMENT_RECIPIENT.strip()
    if not recipient:
        raise ValueError("FULFILMENT_RECIPIENT has not been configured")

    lines = fulfilment_lines(order)
    missing_artwork = [line["title"] for line in lines if line["artwork"] is None]
    if missing_artwork:
        raise ValueError(
            "No private print-ready artwork is available for: " + ", ".join(missing_artwork)
        )

    address = order.shipping_address
    address_lines = [
        address.name,
        address.line1,
        address.line2,
        address.line3,
        address.state,
        address.postcode,
        getattr(address.country, "name", "Australia"),
    ]
    destination = "\n".join(line for line in address_lines if line)
    if address.phone_number:
        destination += f"\nPhone: {address.phone_number}"

    item_lines = []
    for line in lines:
        item_lines.extend(
            [
                f"- {line['quantity']} × {line['title']}",
                f"  Garment: {line['style']}; colour: {line['colour']}; size: {line['size']}",
                f"  Attached artwork: {line['artwork'].name}",
            ]
        )

    body = "\n".join(
        [
            f"Fulfilment request for Topository order {order.number}",
            "",
            "Please send a finished T-shirt design preview to Topository for approval before production.",
            "",
            "Items to produce:",
            *item_lines,
            "",
            "Delivery instruction: send the finished product by normal delivery to the shopper:",
            destination,
            "",
            "Invoice instruction: send the invoice to Topository at info@tshirts.topository.org only.",
            "Do not include Garment Printing Group pricing, invoice details, or supplier correspondence in any shopper communication or delivery.",
        ]
    )
    email = EmailMessage(
        subject=f"Topository fulfilment request — order {order.number}",
        body=body,
        from_email=settings.FULFILMENT_FROM_EMAIL,
        to=[recipient],
        reply_to=["info@tshirts.topository.org"],
    )
    for line in lines:
        email.attach_file(line["artwork"])
    return email
