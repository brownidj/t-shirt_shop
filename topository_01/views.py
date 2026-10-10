import io
import json
import logging
import os
from importlib import import_module
from hashlib import sha256
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.http import HttpResponse, Http404, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from oscar.apps.customer.views import (
    AccountAuthView as OscarAccountAuthView,
    AccountRegistrationView as OscarAccountRegistrationView,
)
from oscar.apps.catalogue.models import (
    AttributeOption,
    AttributeOptionGroup,
    Product,
    ProductAttribute,
    ProductAttributeValue,
    ProductImage,
)
from oscar.apps.partner.models import Partner, StockRecord
from oscar.apps.catalogue.views import ProductDetailView as OscarProductDetailView
from oscar.apps.order.utils import OrderCreator
from oscar.apps.shipping.methods import FixedPrice
from oscar.core import prices
from oscar.core.loading import get_model
from PIL import Image, ImageChops
from django.conf import settings

from .forms import (
    CustomerRegistrationForm,
    DesignRequestForm,
    UsernameOrEmailAuthenticationForm,
)
from .strategy import Selector


logger = logging.getLogger(__name__)
Basket = get_model("basket", "Basket")
Country = get_model("address", "Country")
Order = get_model("order", "Order")
ShippingAddress = get_model("order", "ShippingAddress")
UserAddress = get_model("address", "UserAddress")
WishlistLine = get_model("wishlists", "Line")


class AccountAuthView(OscarAccountAuthView):
    login_form_class = UsernameOrEmailAuthenticationForm
    registration_form_class = CustomerRegistrationForm


class AccountRegistrationView(OscarAccountRegistrationView):
    form_class = CustomerRegistrationForm


def _stripe():
    if not settings.STRIPE_SECRET_KEY:
        raise RuntimeError("Stripe is not configured")
    stripe = import_module("stripe")
    stripe.api_key = settings.STRIPE_SECRET_KEY
    return stripe


def _stripe_value(value, key, default=None):
    """Read a value from either Stripe's mapping or object-style responses."""
    if value is None:
        return default
    if isinstance(value, dict):
        return value.get(key, default)
    return getattr(value, key, default)


def _money_from_cents(amount):
    return Decimal(amount or 0) / Decimal("100")


def _stripe_shipping_details(session):
    """Support both current and earlier Stripe Checkout Session responses."""
    collected = _stripe_value(session, "collected_information")
    return _stripe_value(collected, "shipping_details") or _stripe_value(
        session, "shipping_details"
    )


def _default_shipping_address(user):
    """Return the shopper's preferred saved delivery address, if available."""
    addresses = user.addresses.select_related("country")
    return addresses.filter(is_default_for_shipping=True).first() or addresses.order_by(
        "-num_orders_as_shipping_address", "-date_created"
    ).first()


def _stripe_customer_for_user(stripe, user):
    """Create or update a Stripe Customer from a shopper's saved delivery address."""
    address = _default_shipping_address(user)
    if not address or not user.email:
        return None

    name = " ".join(part for part in (address.first_name, address.last_name) if part)
    customer_data = {
        "email": user.email,
        "name": name,
        "metadata": {"topository_user_id": str(user.id)},
        "shipping": {
            "name": name,
            "phone": address.phone_number or None,
            "address": {
                "line1": address.line1,
                "line2": address.line2 or None,
                "city": address.line3 or "",
                "state": address.state or "",
                "postal_code": address.postcode,
                "country": address.country.iso_3166_1_a2,
            },
        },
    }
    customers = stripe.Customer.list(email=user.email, limit=100)
    for customer in _stripe_value(customers, "data", []):
        if _stripe_value(_stripe_value(customer, "metadata", {}), "topository_user_id") == str(
            user.id
        ):
            stripe.Customer.modify(_stripe_value(customer, "id"), **customer_data)
            return _stripe_value(customer, "id")
    customer = stripe.Customer.create(**customer_data)
    return _stripe_value(customer, "id")


def _create_order_from_stripe_session(session):
    """Create one Oscar order for a paid Checkout Session, idempotently."""
    if _stripe_value(session, "payment_status") != "paid":
        return None

    session_id = _stripe_value(session, "id")
    metadata = _stripe_value(session, "metadata", {}) or {}
    basket_id = _stripe_value(metadata, "basket_id")
    if not session_id or not basket_id:
        raise ValueError("Stripe Checkout Session is missing order metadata")

    order_number = f"stripe-{session_id}"
    existing = Order.objects.filter(number=order_number).first()
    if existing:
        return existing

    try:
        basket = Basket.objects.get(pk=int(basket_id))
    except (Basket.DoesNotExist, TypeError, ValueError) as exc:
        raise ValueError("Stripe Checkout Session references an unknown basket") from exc

    shipping = _stripe_shipping_details(session)
    address = _stripe_value(shipping, "address")
    if not address:
        raise ValueError("Stripe Checkout Session has no delivery address")

    country_code = _stripe_value(address, "country")
    try:
        country = Country.objects.get(iso_3166_1_a2=country_code)
    except Country.DoesNotExist as exc:
        raise ValueError("Stripe Checkout Session has an unsupported delivery country") from exc

    customer = _stripe_value(session, "customer_details")
    customer_name = _stripe_value(shipping, "name") or _stripe_value(customer, "name", "")
    name_parts = customer_name.strip().split(maxsplit=1)
    shipping_address = ShippingAddress(
        first_name=name_parts[0] if name_parts else "",
        last_name=name_parts[1] if len(name_parts) > 1 else "",
        line1=_stripe_value(address, "line1") or "",
        line2=_stripe_value(address, "line2") or "",
        line3=_stripe_value(address, "city") or "",
        state=_stripe_value(address, "state") or "",
        postcode=_stripe_value(address, "postal_code") or "",
        country=country,
        phone_number=_stripe_value(customer, "phone") or "",
    )

    currency = (_stripe_value(session, "currency") or "aud").upper()
    shipping_cost = _stripe_value(_stripe_value(session, "shipping_cost"), "amount_total", 0)
    shipping_amount = _money_from_cents(shipping_cost)
    total = _money_from_cents(_stripe_value(session, "amount_total"))
    shipping_charge = prices.Price(
        currency=currency, excl_tax=shipping_amount, incl_tax=shipping_amount
    )
    order_total = prices.Price(currency=currency, excl_tax=total, incl_tax=total)
    shipping_method = FixedPrice(
        charge_excl_tax=shipping_amount, charge_incl_tax=shipping_amount
    )
    shipping_method.name = "Standard shipping"
    shipping_method.code = "stripe-standard-shipping"

    user = None
    user_id = _stripe_value(metadata, "user_id")
    if user_id:
        user = get_user_model().objects.filter(pk=user_id).first()
    # Webhooks run without Oscar's basket middleware, so attach the same
    # purchase strategy that is normally provided by a browser request.
    basket.strategy = Selector().strategy(user=user)

    # The address must be saved before it can be attached to the Oscar order.
    shipping_address.save()
    if user and user.is_authenticated:
        try:
            user_address = user.addresses.get(hash=shipping_address.generate_hash())
        except UserAddress.DoesNotExist:
            user_address = UserAddress(user=user)
            shipping_address.populate_alternative_model(user_address)
        user_address.num_orders_as_shipping_address += 1
        user_address.save()
    try:
        order = OrderCreator().place_order(
            user=user,
            order_number=order_number,
            basket=basket,
            shipping_address=shipping_address,
            shipping_method=shipping_method,
            shipping_charge=shipping_charge,
            total=order_total,
            guest_email=_stripe_value(customer, "email") or _stripe_value(session, "customer_email", ""),
        )
    except IntegrityError:
        # Stripe can deliver the same completed event more than once.
        order = Order.objects.get(number=order_number)
    else:
        basket.submit()
    return order


@require_POST
def stripe_checkout(request):
    """Start a hosted Stripe Checkout session from server-side basket prices."""
    if request.basket.is_empty:
        return redirect("basket:summary")
    try:
        stripe = _stripe()
    except RuntimeError:
        messages.error(request, "Online payments are not configured yet.")
        return redirect("basket:summary")
    line_items = []
    for line in request.basket.all_lines():
        price = line.price_incl_tax or line.price_excl_tax
        if price is None:
            messages.error(request, "One or more basket items cannot be priced.")
            return redirect("basket:summary")
        line_items.append({"price_data": {"currency": "aud", "unit_amount": int((price * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)), "product_data": {"name": line.description}, "tax_behavior": "inclusive"}, "quantity": line.quantity})
    checkout_data = {
        "mode": "payment",
        "line_items": line_items,
        "shipping_address_collection": {"allowed_countries": ["AU"]},
        "shipping_options": [{"shipping_rate_data": {"display_name": "Standard shipping", "type": "fixed_amount", "fixed_amount": {"amount": settings.STRIPE_SHIPPING_CENTS, "currency": "aud"}, "tax_behavior": "inclusive"}}],
        "metadata": {
            "basket_id": str(request.basket.id),
            "user_id": str(request.user.id) if request.user.is_authenticated else "",
        },
        "client_reference_id": str(request.basket.id),
        "success_url": request.build_absolute_uri(reverse("stripe_checkout_success")) + "?session_id={CHECKOUT_SESSION_ID}",
        "cancel_url": request.build_absolute_uri(reverse("stripe_checkout_cancel")),
    }
    try:
        if request.user.is_authenticated:
            customer_id = _stripe_customer_for_user(stripe, request.user)
            if customer_id:
                checkout_data["customer"] = customer_id
            else:
                checkout_data["customer_email"] = request.user.email
        session = stripe.checkout.Session.create(**checkout_data)
    except stripe.StripeError:
        messages.error(request, "Stripe could not start checkout. Please try again.")
        return redirect("basket:summary")
    request.basket.freeze()
    request.session["stripe_checkout_session_id"] = session.id
    request.session["stripe_checkout_basket_id"] = request.basket.id
    return redirect(session.url)


def stripe_checkout_success(request):
    try:
        session = _stripe().checkout.Session.retrieve(request.GET.get("session_id", ""))
    except Exception:
        return HttpResponseBadRequest("We could not confirm this Stripe payment.")
    if session.id != request.session.get("stripe_checkout_session_id"):
        return HttpResponseBadRequest("We could not confirm this Stripe payment.")
    try:
        order = _create_order_from_stripe_session(session)
    except Exception:
        logger.exception("Could not create an order from Stripe Checkout Session %s", session.id)
        return render(request, "topository/stripe_success.html", {"paid": False})
    if order:
        request.session.pop("stripe_checkout_session_id", None)
        request.session.pop("stripe_checkout_basket_id", None)
    return render(request, "topository/stripe_success.html", {"paid": bool(order)})


def stripe_checkout_cancel(request):
    """Restore the basket when the shopper leaves Stripe Checkout unpaid."""
    basket_id = request.session.pop("stripe_checkout_basket_id", None)
    request.session.pop("stripe_checkout_session_id", None)
    if basket_id:
        basket = Basket.objects.filter(pk=basket_id, status=Basket.FROZEN).first()
        if basket:
            basket.thaw()
    return redirect("basket:summary")


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """Record paid Checkout Sessions even when the shopper never returns."""
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET
    if not webhook_secret:
        logger.error("Received a Stripe webhook but STRIPE_WEBHOOK_SECRET is not configured")
        return HttpResponse(status=503)
    try:
        event = _stripe().Webhook.construct_event(
            request.body, request.headers.get("Stripe-Signature", ""), webhook_secret
        )
    except Exception:
        logger.warning("Rejected an invalid Stripe webhook")
        return HttpResponseBadRequest("Invalid Stripe webhook")

    if event["type"] in {"checkout.session.completed", "checkout.session.async_payment_succeeded"}:
        try:
            _create_order_from_stripe_session(event["data"]["object"])
        except Exception:
            logger.exception("Could not process Stripe webhook %s", event.get("id"))
            return HttpResponse(status=500)
    return HttpResponse(status=200)


KIDS_STAPLE_TEE_COLOURS = frozenset(
    {
        "Army", "Black", "Bone", "Bright Royal", "Burgundy",
        "Carolina Blue", "Charcoal", "Charity Pink", "Cobalt", "Ecru",
        "Forest Green", "Gold", "Grey Marle", "Kelly Green", "Navy",
        "Orange", "Petrol Blue", "Pink", "Purple", "Red", "Sage",
        "Walnut", "White",
    }
)

KIDS_STAPLE_TEE_SIZES = frozenset({"2", "4", "6"})
ADULT_TEE_SIZES = frozenset({"XS", "S", "M", "L", "XL", "2XL", "3XL", "4XL"})

# These are retail prices for a printed garment, independent of colour or
# size.  Fulfilment is print-on-demand, so variants are made only after a
# customer chooses one rather than being held as physical stock.
TSHIRT_STYLE_PRICES = {
    "AS-5001": Decimal("55.00"),
    "AS-4001": Decimal("50.00"),
    "AS-3005": Decimal("45.00"),
}

TSHIRT_STYLE_NAMES = {
    "AS-5001": "Men's Tee",
    "AS-4001": "Women's Tee",
    "AS-3005": "Kid's Tee",
}

MENS_STAPLE_TEE_COLOURS = frozenset(
    {
        "Aqua", "Arctic Blue", "Army", "Asphalt Marle", "Atlantic", "Autumn",
        "Berry", "Black", "Bone", "Bright Royal", "Bubblegum", "Burgundy",
        "Butter", "Camel", "Cardinal", "Carolina Blue", "Charcoal", "Charity Pink",
        "Charlotte", "Chestnut", "Citrus", "Clay", "Coal", "Cobalt", "Cocoa",
        "Copper", "Coral", "Cypress", "Dark Chocolate", "Ecru", "Eucalyptus",
        "Fire", "Fog Blue", "Forest Green", "Forest Marle", "Forest Marle - 567C",
        "Gold", "Granite", "Grey Marle", "Hydro", "Indigo", "Jade", "Kelly Green",
        "Khaki", "Kiwi", "Lapis", "Lemon", "Lemonade", "Light Grey", "Lime",
        "Mauve", "Midnight Blue", "Mineral", "Moss", "Mushroom", "Mustard",
        "Natural", "Navy", "Orange", "Orchid", "Pale Blue", "Pale Pink",
        "Petrol Blue", "Pine Green", "Pink", "Pistachio", "Plum", "Powder",
        "Purple", "Red", "Rose", "Safari", "Sage", "Sand", "Seafoam", "Shadow",
        "Slate Blue", "Smoke", "Sunset", "Tan", "Teal", "Topaz", "Walnut",
        "White", "Yellow",
    }
)

WOMENS_MAPLE_TEE_COLOURS = frozenset(
    {
        "Army", "Asphalt Marle", "Atlantic", "Autumn", "Berry", "Black",
        "Bone", "Bright Royal", "Bubblegum", "Burgundy", "Butter", "Camel",
        "Cardinal", "Carolina Blue", "Charcoal", "Charity Pink", "Chestnut",
        "Clay", "Coal", "Cobalt", "Copper", "Coral", "Ecru", "Eucalyptus",
        "Fire", "Forest Green", "Fuchsia", "Grey Marle", "Hydro", "Indigo",
        "Jade", "Lavender", "Lime", "Mauve", "Midnight Blue", "Mineral",
        "Mushroom", "Mustard", "Natural", "Navy", "Orange", "Orchid",
        "Pale Blue", "Pale Pink", "Petrol Blue", "Pine Green", "Pink",
        "Pistachio", "Plum", "Powder", "Purple", "Red", "Rose", "Sage",
        "Sand", "Seafoam", "Tan", "Walnut", "White", "Yellow",
    }
)


def slideshow_home(request):
    """Show catalogue artwork, linked to its corresponding product page."""
    slides = []
    for product_image in ProductImage.objects.select_related("product").order_by("original"):
        if not product_image.original:
            continue

        image_path = Path(product_image.original.path)
        slides.append(
            {
                # Cache-bust edited artwork so a slideshow refresh never shows
                # an earlier image with stale borders or other old pixels.
                "url": f"{product_image.original.url}?v={image_path.stat().st_mtime_ns}",
                "alt": product_image.product.title,
                "product_url": product_image.product.get_absolute_url(),
            }
        )
    return render(request, "topository/home.html", {"slides": slides})


def configured_product_detail(request, product_slug, pk):
    """Return a configured basket item to its parent design and selections."""
    product = get_object_or_404(Product, pk=pk)
    if product.is_child and product.parent_id:
        def option_text(attribute_code):
            value = getattr(product.attr, attribute_code, None)
            return value.option if hasattr(value, "option") else str(value or "")

        selections = {
            "style": option_text("tshirt_style"),
            "colour": option_text("colour"),
            "size": option_text("size"),
        }
        if all(selections.values()):
            line_id = request.basket.lines.filter(product=product).values_list("pk", flat=True).first()
            if line_id:
                selections["line"] = line_id
            return redirect(f"{product.parent.get_absolute_url()}?{urlencode(selections)}")

    return OscarProductDetailView.as_view()(request, product_slug=product_slug, pk=pk)


@login_required
@require_POST
def transfer_basket_line_to_wishlist(request):
    """Move one of the current shopper's basket lines to their wishlist."""
    line_id = request.POST.get("line_id", "")
    if not line_id.isdigit():
        raise Http404("Basket line not found")

    with transaction.atomic():
        line = get_object_or_404(
            request.basket.lines.select_related("product").select_for_update(),
            pk=int(line_id),
        )
        wishlist = request.user.wishlists.order_by("date_created").first()
        if wishlist is None:
            wishlist = request.user.wishlists.create()

        wishlist_line, created = wishlist.lines.get_or_create(
            product=line.product,
            defaults={"title": line.description, "quantity": line.quantity},
        )
        if not created:
            wishlist_line.quantity += line.quantity
            wishlist_line.save(update_fields=["quantity"])

        line_description = line.description
        line.delete()
        request.basket.reset_offer_applications()

    messages.success(request, f"'{line_description}' was transferred to your wishlist.")
    return redirect("basket:summary")


@login_required
def wishlist_view(request):
    """Show the current shopper's default wishlist."""
    wishlist = request.user.wishlists.order_by("date_created").first()
    wishlist_lines = ()
    if wishlist is not None:
        wishlist_lines = wishlist.lines.filter(product__isnull=False).select_related(
            "product", "product__product_class"
        )
    return render(
        request,
        "topository/wishlist.html",
        {"wishlist": wishlist, "wishlist_lines": wishlist_lines},
    )


@login_required
@require_POST
def add_wishlist_line_to_cart(request, line_id):
    """Transfer a saved T-shirt to the current basket."""
    with transaction.atomic():
        wishlist_line = get_object_or_404(
            WishlistLine.objects.select_related("product", "wishlist").select_for_update(),
            pk=line_id,
            wishlist__owner=request.user,
        )
        product = wishlist_line.product
        quantity = wishlist_line.quantity
        wishlist_line.delete()
        request.basket.add_product(product, quantity=quantity)

    messages.success(request, f"{product.title} was moved to your cart.")
    return redirect("wishlist")


@login_required
@require_POST
def remove_wishlist_line(request, line_id):
    """Remove one saved item from the current shopper's wishlist."""
    wishlist_line = get_object_or_404(
        WishlistLine.objects.select_related("wishlist"),
        pk=line_id,
        wishlist__owner=request.user,
    )
    title = wishlist_line.get_title()
    wishlist_line.delete()
    messages.success(request, f"{title} was removed from your wishlist.")
    return redirect("wishlist")


@login_required
@require_POST
def update_wishlist_line_quantity(request, line_id):
    """Update a saved quantity, removing the line when it reaches zero."""
    wishlist_line = get_object_or_404(
        WishlistLine.objects.select_related("wishlist"),
        pk=line_id,
        wishlist__owner=request.user,
    )
    try:
        quantity = int(request.POST.get("quantity", ""))
    except (TypeError, ValueError):
        messages.error(request, "Enter a whole-number quantity.")
        return redirect("wishlist")

    if quantity < 0:
        messages.error(request, "Quantity cannot be negative.")
    elif quantity == 0:
        title = wishlist_line.get_title()
        wishlist_line.delete()
        messages.success(request, f"{title} was removed from your wishlist.")
    else:
        wishlist_line.quantity = quantity
        wishlist_line.save(update_fields=["quantity"])
        messages.success(request, "Wishlist quantity updated.")
    return redirect("wishlist")


def request_design(request):
    """Collect a shopper's request for a new T-shirt design."""
    if request.method == "POST":
        form = DesignRequestForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Thank you. Your design request has been received.")
            return redirect("request_design")
    else:
        form = DesignRequestForm()
    return render(request, "topository/request_design.html", {"form": form})


# ---- Helper functions copied from your script ----

def hex_to_rgb(hex_colour):
    hex_colour = hex_colour.strip().lstrip("#")
    return (
        int(hex_colour[0:2], 16),
        int(hex_colour[2:4], 16),
        int(hex_colour[4:6], 16),
    )


def tint_shirt(base_img, mask_img, rgb_colour):
    """
    Tint the shirt while retaining restrained, colour-aware fabric detail.

    The base image already contains its photographic folds and seams.  Apply
    one shading pass only: pale garments get subtle shadows, while dark
    garments retain more definition without being brightened into chalky
    highlights.
    """
    if base_img.size != mask_img.size:
        raise ValueError("Base shirt and mask images must be the same size.")

    # Base greyscale luminance – this encodes the folds/seams nicely
    base_l = base_img.convert("L")            # 0..255 per pixel
    base_l_data = base_l.load()

    # Original tinted shirt (no design yet)
    base_rgba = base_img.convert("RGBA")
    mask_l = mask_img.convert("L")
    solid_colour = Image.new("RGBA", base_rgba.size, rgb_colour + (255,))
    tinted_full = ImageChops.multiply(base_rgba, solid_colour)
    tinted_data = tinted_full.load()

    width, height = tinted_full.size
    shirt_luminance = (
        0.299 * rgb_colour[0]
        + 0.587 * rgb_colour[1]
        + 0.114 * rgb_colour[2]
    ) / 255.0

    # Keep pale colours clean while retaining more shape in dark garments.
    # This modulation only darkens; it cannot produce a highlight lighter
    # than the selected garment colour.
    shadow_strength = 0.08 + 0.18 * (1.0 - shirt_luminance)

    # Apply a single, restrained fold/shadow pass within the shirt area.
    for y in range(height):
        for x in range(width):
            r, g, b, a = tinted_data[x, y]

            # Skip fully transparent pixels
            if a == 0:
                continue

            # Luminance from the original base shirt (0..255)
            lum = base_l_data[x, y] / 255.0

            factor = 1.0 - shadow_strength * (1.0 - lum)

            nr = int(max(0, min(255, r * factor)))
            ng = int(max(0, min(255, g * factor)))
            nb = int(max(0, min(255, b * factor)))
            tinted_data[x, y] = (nr, ng, nb, a)

    # Finally, mask this enhanced shirt into transparency
    transparent = Image.new("RGBA", base_rgba.size, (0, 0, 0, 0))
    return Image.composite(tinted_full, transparent, mask_l)


def place_design_on_shirt(shirt_img, design_img, side_margin_frac, chest_y_frac):
    sw, sh = shirt_img.size
    dw, dh = design_img.size

    # Scale design to fit between left/right margins
    avail_w = int(sw * (1 - 2 * side_margin_frac))
    if avail_w <= 0:
        raise ValueError("side_margin_frac too large; no space for design.")

    scale = avail_w / float(dw)
    target_w = avail_w
    target_h = int(dh * scale)

    resized = design_img.resize((target_w, target_h), Image.LANCZOS)
    if resized.mode != "RGBA":
        resized = resized.convert("RGBA")

    # Centre the print on the shirt silhouette, not merely on the image canvas.
    # This keeps the design aligned when individual shirt photos have different
    # transparent margins or slightly off-centre photography.
    alpha_bbox = shirt_img.getchannel("A").getbbox()
    if alpha_bbox:
        shirt_left, _, shirt_right, _ = alpha_bbox
        shirt_centre_x = (shirt_left + shirt_right) / 2
    else:
        shirt_centre_x = sw / 2
    x = round(shirt_centre_x - (target_w / 2))
    y = int(sh * chest_y_frac)

    # Start from tinted shirt
    base_rgba = shirt_img.convert("RGBA")
    composed = base_rgba.copy()
    composed.paste(resized, (x, y), resized)

    return composed


# ---- Main dynamic preview renderer ----

def tshirt_preview(request, product_id):
    """Render a configured shirt preview without requiring a saved variant."""
    product = get_object_or_404(Product, pk=product_id)

    # These attributes may be plain strings or AttributeOption instances
    raw_colour = request.GET.get("colour") or getattr(product.attr, "colour", None)
    raw_style = request.GET.get("style") or getattr(product.attr, "tshirt_style", None)

    # Normalise colour to a simple string (for lookup in colours_parsed.json)
    if raw_colour is None:
        colour = ""
    elif hasattr(raw_colour, "option"):
        # AttributeOption.option is the human-readable name
        colour = raw_colour.option
    else:
        colour = str(raw_colour)

    # Normalise style to a simple string (usually a UPC-like code such as AS-5001)
    if raw_style is None:
        style = ""
    elif hasattr(raw_style, "option"):
        style = raw_style.option
    else:
        style = str(raw_style)

    if not colour or not style:
        raise Http404("Style or colour missing")

    # Convert colour → hex using colours_parsed.json
    json_path = os.path.join(settings.BASE_DIR, "static", "topository", "colours_parsed.json")
    with open(json_path, "r") as f:
        colour_map = json.load(f)

    key = colour.strip().lower().replace(" ", "_")
    if key not in colour_map:
        raise Http404("Unknown colour: " + key)

    hex_colour = colour_map[key]

    # Load base + mask for style
    style_dir = os.path.join(settings.BASE_DIR, "static", "topository", "tshirts", style)
    base_path = os.path.join(style_dir, f"{style}_base.png")
    mask_path = os.path.join(style_dir, f"{style}_mask.png")

    if not os.path.exists(base_path) or not os.path.exists(mask_path):
        raise Http404("Missing base/mask image for style " + style)

    base = Image.open(base_path)
    mask = Image.open(mask_path)

    # Resolve the parent (design) product and its primary image
    parent = product.parent or product

    primary_image_attr = getattr(parent, "primary_image", None)
    if callable(primary_image_attr):
        # In Oscar 4.1 primary_image is a method returning a ProductImage
        primary_image_model = primary_image_attr()
    else:
        # If it ever becomes a simple attribute, handle that too
        primary_image_model = primary_image_attr

    # Always use the original uploaded file, not any processed/thumbnail version
    if not primary_image_model or not getattr(primary_image_model, "original", None):
        raise Http404("No original primary image found for parent product")

    design_path = primary_image_model.original.path
    source_signature = "|".join(
        str(os.stat(path).st_mtime_ns) for path in (base_path, mask_path, design_path)
    )
    cache_key = "tshirt-preview:" + sha256(
        f"{parent.pk}|{style}|{colour}|{source_signature}".encode()
    ).hexdigest()
    cached_preview = cache.get(cache_key)
    if cached_preview is not None:
        return HttpResponse(cached_preview, content_type="image/png")

    design = Image.open(design_path)

    rgb = hex_to_rgb(hex_colour)

    tinted = tint_shirt(base, mask, rgb)
    final = place_design_on_shirt(tinted, design, 0.31, 0.28)

    # Background white behind transparency
    bg = Image.new("RGBA", final.size, (249,249,249,255))
    out = Image.alpha_composite(bg, final)

    buffer = io.BytesIO()
    out.save(buffer, format="PNG")
    preview_bytes = buffer.getvalue()
    cache.set(cache_key, preview_bytes, timeout=60 * 60 * 24 * 10)

    return HttpResponse(preview_bytes, content_type="image/png")


@require_POST
def add_configured_tshirt(request, product_id, *, save_to_wishlist=False):
    """Create a requested T-shirt variant only when it is added to a basket."""
    design = get_object_or_404(Product, pk=product_id, product_class__name="Designs")
    style_code = request.POST.get("style", "").strip()
    colour = request.POST.get("colour", "").strip()
    size = request.POST.get("size", "").strip()
    basket_line_id = request.POST.get("line", "").strip()

    if not style_code or not colour or not size:
        raise Http404("Choose a style, colour and size before adding to basket")
    if style_code not in TSHIRT_STYLE_PRICES:
        raise Http404("Unknown T-shirt style")

    colour_key = colour.lower().replace(" ", "_")
    colour_map_path = os.path.join(
        settings.BASE_DIR, "static", "topository", "colours_parsed.json"
    )
    with open(colour_map_path, "r") as colour_file:
        colour_map = json.load(colour_file)
    if colour_key not in colour_map:
        raise Http404("Unknown colour")
    if style_code == "AS-5001" and colour not in MENS_STAPLE_TEE_COLOURS:
        raise Http404("That colour is not available for the Men's Staple Tee")
    if style_code == "AS-3005" and colour not in KIDS_STAPLE_TEE_COLOURS:
        raise Http404("That colour is not available for the Kid's Staple Tee")
    if style_code == "AS-4001" and colour not in WOMENS_MAPLE_TEE_COLOURS:
        raise Http404("That colour is not available for the Women's Staple Tee")

    valid_sizes = (
        KIDS_STAPLE_TEE_SIZES if style_code == "AS-3005" else ADULT_TEE_SIZES
    )
    if size not in valid_sizes:
        raise Http404("Unknown size")

    style = get_object_or_404(Product, upc=style_code, product_class__name="T-shirt")
    base_path = settings.BASE_DIR / "static" / "topository" / "tshirts" / style_code / f"{style_code}_base.png"
    if not base_path.exists():
        raise Http404("Unknown T-shirt style")

    with transaction.atomic():
        design = Product.objects.select_for_update().get(pk=design.pk)
        if design.is_standalone:
            design.structure = Product.PARENT
            design.save(update_fields=["structure"])

        sku = f"{design.upc}-{style_code}-{colour.replace(' ', '-')}-{size}"
        attributes = {
            attribute.code: attribute
            for attribute in ProductAttribute.objects.filter(
                product_class=style.product_class,
                code__in={"tshirt_style", "colour", "size"},
            )
        }

        def option_for(group_name, value):
            group = get_object_or_404(AttributeOptionGroup, name=group_name)
            option, _ = AttributeOption.objects.get_or_create(
                group=group, option=value
            )
            return option

        options = {
            "tshirt_style": option_for("T-shirt Style", style_code),
            "colour": option_for("T-shirt Colours", colour),
            "size": option_for("T-shirt Sizes", size),
        }

        matching_children = Product.objects.filter(
            parent=design, product_class=style.product_class
        )
        for code, option in options.items():
            matching_children = matching_children.filter(
                attribute_values__attribute=attributes[code],
                attribute_values__value_option=option,
            )
        child = matching_children.first()
        created = child is None
        if created:
            child = Product.objects.create(
                parent=design,
                upc=sku,
                title=f"{design.title} – {TSHIRT_STYLE_NAMES[style_code]} – {colour} – {size}",
                structure=Product.CHILD,
                product_class=style.product_class,
            )
            for code, option in options.items():
                ProductAttributeValue.objects.create(
                    product=child, attribute=attributes[code], value_option=option
                )

        # Keep the one price per style in the database as the source of truth
        # for checkout.  A null quantity denotes print-on-demand stock; the
        # custom Oscar strategy marks this fulfilment partner as always
        # available rather than decrementing an invented inventory count.
        partner, _ = Partner.objects.get_or_create(name="Topository Fulfilment")
        StockRecord.objects.update_or_create(
            product=child,
            partner=partner,
            defaults={
                "partner_sku": sku,
                "price": TSHIRT_STYLE_PRICES[style_code],
                "price_currency": "AUD",
                "num_in_stock": None,
            },
        )

    if save_to_wishlist:
        wishlist = request.user.wishlists.order_by("date_created").first()
        if wishlist is None:
            wishlist = request.user.wishlists.create()
        wishlist.add(child)
        messages.success(request, f"{child.title} was added to your wishlist.")
        return redirect("wishlist")

    basket_line = None
    if basket_line_id.isdigit():
        basket_line = request.basket.lines.filter(pk=int(basket_line_id)).first()

    if basket_line:
        old_price = (
            basket_line.price_incl_tax
            if basket_line.price_incl_tax is not None
            else basket_line.price_excl_tax
        )
        stock_info = request.basket.get_stock_info(child, [])
        new_price = (
            stock_info.price.incl_tax
            if stock_info.price.is_tax_known
            else stock_info.price.excl_tax
        )
        basket_line.product = child
        basket_line.stockrecord = stock_info.stockrecord
        basket_line.price_excl_tax = stock_info.price.excl_tax
        basket_line.price_incl_tax = (
            stock_info.price.incl_tax if stock_info.price.is_tax_known else None
        )
        basket_line.price_currency = stock_info.price.currency
        basket_line.tax_code = stock_info.price.tax_code
        basket_line.save(
            update_fields=[
                "product",
                "stockrecord",
                "price_excl_tax",
                "price_incl_tax",
                "price_currency",
                "tax_code",
            ]
        )
        request.basket.reset_offer_applications()
        if old_price is not None and old_price != new_price:
            messages.warning(
                request,
                f"The price of your '{design.title} t-shirt' has changed from "
                f"A${old_price:.2f} to A${new_price:.2f} since you changed "
                "the t-shirt style",
            )
    else:
        request.basket.add_product(child, quantity=1)
        messages.success(request, f"{child.title} was added to your cart.")

    # Keep the shopper on the design page after adding a shirt. The cart is
    # opened explicitly through the cart icon in the primary navigation.
    selections = {
        "style": style_code,
        "colour": colour,
        "size": size,
    }
    if basket_line_id:
        selections["line"] = basket_line_id
    return redirect(f"{design.get_absolute_url()}?{urlencode(selections)}")


@login_required
@require_POST
def add_configured_tshirt_to_wishlist(request, product_id):
    """Save the current default or selected T-shirt variant to a wishlist."""
    return add_configured_tshirt(request, product_id, save_to_wishlist=True)
