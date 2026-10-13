"""Private, staff-initiated print fulfilment email support."""

from pathlib import Path

from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import timezone

from .models import FulfilmentRequest


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


def build_fulfilment_email(request):
    """Build the internal-only request to Garment Printing Group.

    The caller must check both the selected contact and artwork before
    sending.  No shopper email address, shop retail price, or supplier price is
    included in the message.
    """
    order = request.order
    if request.supplier is None or not request.supplier.supports_blind_shipping:
        raise ValueError("Choose an active supplier approved for blind shipping")
    if request.contact is None or request.contact.supplier_id != request.supplier_id:
        raise ValueError("Choose a named contact for the selected supplier")

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
            "Items to produce:",
            *item_lines,
            "",
            "Delivery address:",
            destination,
            "",
            "Instructions:",
            request.special_instructions,
        ]
    )
    email = EmailMessage(
        subject=f"Topository fulfilment request — order {order.number}",
        body=body,
        from_email=settings.FULFILMENT_FROM_EMAIL,
        to=[request.contact.email],
        reply_to=["info@tshirts.topository.org"],
    )
    for line in lines:
        email.attach_file(line["artwork"])
    return email


def ensure_fulfilment_request(order):
    """Create the supplier-neutral internal request for a paid order."""
    from .models import FulfilmentContact, FulfilmentSupplier

    supplier = FulfilmentSupplier.objects.filter(
        active=True, supports_blind_shipping=True
    ).order_by("name").first()
    contact = None
    if supplier:
        contact = FulfilmentContact.objects.filter(
            supplier=supplier, active=True
        ).order_by("-is_default", "name").first()
    request, _ = FulfilmentRequest.objects.get_or_create(
        order=order, defaults={"supplier": supplier, "contact": contact}
    )
    return request


def mark_request_sent(request):
    request.status = FulfilmentRequest.STATUS_REQUEST_SENT
    request.request_sent_at = timezone.now()
    request.save(update_fields=("status", "request_sent_at", "updated_at"))
