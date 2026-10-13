from django.db import migrations


TERMS_OF_SALE = """
<h2>About us</h2>
<p><strong>topository</strong> is the business name of <strong>David James Browning</strong>, sole trader (ABN 16 205 166 811). Contact us at <a href="mailto:info@tshirts.topository.org">info@tshirts.topository.org</a>.</p>
<h2>Products and availability</h2>
<p>We make reasonable efforts to display product details, colours, garment styles and prices accurately. Screens and print processes can display colours differently; minor variation between a screen preview and finished garment may occur. Please check the applicable size guide before ordering. Garment measurements may vary by up to 2 cm. Products are subject to availability. If an option is unavailable, we will offer an alternative, wait for stock, or refund the unavailable item.</p>
<h2>Prices and payment</h2>
<p>Prices are in Australian dollars and include GST where applicable. Delivery and other unavoidable charges are shown before you place an order. Payment is processed by Stripe through hosted checkout; we do not receive or store full card numbers.</p>
<h2>Production and delivery</h2>
<p>Garments are printed to order by our Australian production partner. Production normally takes approximately <strong>10 business days</strong>; delivery time is additional. Timeframes are estimates and may be affected by stock availability, carriers, weather, public holidays or events outside our reasonable control. We currently deliver only to Australian addresses.</p>
<h2>Cancellations, returns and remedies</h2>
<p>Because products are made to order, changes or cancellation may be possible only before production begins. Once production has begun, we do not offer cancellations, changes, refunds or exchanges for change of mind, including an incorrect size, colour, garment, style or quantity selected by the shopper. See our <a href="/returns-refunds-cancellations/">Returns, Refunds and Cancellations Policy</a> for details.</p>
<h2>Australian Consumer Law</h2>
<p>Nothing in these Terms excludes, restricts or modifies any consumer guarantee, right or remedy under the Australian Consumer Law that cannot lawfully be excluded, restricted or modified.</p>
<h2>Site use and intellectual property</h2>
<p>You are responsible for activity under your account and must keep account credentials confidential. Unless stated otherwise, site designs, text, photographs and logos are owned by or licensed to topository and may not be reproduced or exploited without written permission.</p>
<h2>Governing law</h2>
<p>These Terms are governed by the laws of Australia and Queensland. Applicable consumer-protection laws continue to apply.</p>
"""

RETURNS_POLICY = """
<p><strong>topository</strong> is the business name of David James Browning, sole trader (ABN 16 205 166 811). For help with an order, email <a href="mailto:info@tshirts.topository.org">info@tshirts.topository.org</a>.</p>
<h2>Made-to-order products</h2>
<p>Our garments are printed to order by an Australian production partner. Production normally takes approximately <strong>10 business days</strong>; delivery time is additional.</p>
<h2>Cancellations and change-of-mind returns</h2>
<p>Contact us promptly if you need to change or cancel an order. We may be able to help before production begins. Once production has begun, an order cannot be cancelled or changed. We do not offer returns, refunds or exchanges for change of mind, including an incorrect size, colour, garment, style or quantity selected by the shopper.</p>
<h2>Normal variation</h2>
<p>Colours may vary slightly between screens, garments and print processes. Garment measurements may vary by up to 2 cm. Direct-to-garment printing can leave temporary pre-treatment or press marks that should disappear after the first wash when care instructions are followed. Minor variations of these kinds are not, by themselves, faults.</p>
<h2>Faulty, damaged or incorrect products</h2>
<p>If an item is faulty, damaged, misprinted, or materially different from your order, email us with your order number, photographs and a description of the issue. Please contact us within <strong>14 days of receiving your order</strong> where reasonably possible. This helps us investigate promptly; it is not a deadline that limits rights under the Australian Consumer Law.</p>
<p>Please do not return an item until we provide instructions. If a fault is confirmed, we will provide the remedy required by law and reimburse reasonable return-postage costs where appropriate.</p>
<h2>Australian Consumer Law</h2>
<p>Nothing in this policy excludes, restricts or modifies any consumer guarantee, right or remedy available under the Australian Consumer Law. For a major failure, you may be entitled to choose a refund or replacement. For a minor failure, we may repair or replace the product within a reasonable time, or otherwise provide the remedy required by law.</p>
"""

PRIVACY_POLICY = """
<p>This Privacy Policy explains how <strong>topository</strong>, the business name of David James Browning, sole trader (ABN 16 205 166 811), handles personal information. For privacy questions or requests, email <a href="mailto:info@tshirts.topository.org">info@tshirts.topository.org</a>.</p>
<h2>Information we collect</h2>
<p>We collect account details (name, username, email address and password hash), delivery details, order history, payment status and Stripe identifiers, wish-list, basket and recently viewed product information, communications and design requests, and marketing consent where you opt in. We may also collect technical information such as IP address, browser details, server logs and necessary cookie information.</p>
<h2>How we use information</h2>
<p>We use information to administer accounts, process payment, orders and delivery, provide support, meet legal and tax record-keeping requirements, investigate faults or fraud, respond to enquiries, operate and secure the shop, and send marketing only with consent or where otherwise permitted by law.</p>
<h2>Who receives information</h2>
<p>We disclose information only where reasonably needed: to Stripe for payment, to Garment Printing Group for production and fulfilment, to delivery carriers, and to technology providers that host, maintain or secure the shop. We may disclose information where required or authorised by law. Stripe and other technology providers may process information outside Australia. We do not sell personal information.</p>
<h2>Cookies</h2>
<p>The shop uses necessary cookies and sessions for login, the shopping basket and recently viewed products. Basket and recently viewed-product cookies normally last up to seven days. Disabling cookies may prevent parts of the shop from working. Non-essential analytics or advertising cookies are not currently used.</p>
<h2>Access, correction and complaints</h2>
<p>You may request access to, or correction of, your personal information by email. We may need to verify your identity. If you are dissatisfied with our response, you may be able to complain to the Office of the Australian Information Commissioner.</p>
"""


def create_legal_pages(apps, schema_editor):
    flat_page = apps.get_model("flatpages", "FlatPage")
    site, _ = apps.get_model("sites", "Site").objects.get_or_create(
        pk=1,
        defaults={"domain": "tshirts.topository.org", "name": "topository"},
    )
    pages = (
        ("/terms-of-sale/", "Terms of Sale", TERMS_OF_SALE),
        ("/returns-refunds-cancellations/", "Returns & Refunds", RETURNS_POLICY),
        ("/privacy-policy/", "Privacy Policy", PRIVACY_POLICY),
    )
    for url, title, content in pages:
        page, _ = flat_page.objects.update_or_create(
            url=url,
            defaults={
                "title": title,
                "content": content,
                "enable_comments": False,
                "registration_required": False,
                "template_name": "flatpages/default.html",
            },
        )
        page.sites.add(site)


def remove_legal_pages(apps, schema_editor):
    flat_page = apps.get_model("flatpages", "FlatPage")
    flat_page.objects.filter(
        url__in=(
            "/terms-of-sale/",
            "/returns-refunds-cancellations/",
            "/privacy-policy/",
        )
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("flatpages", "0001_initial"),
        ("sites", "0002_alter_domain_unique"),
        ("topository_01", "0003_set_default_first_names"),
    ]

    operations = [migrations.RunPython(create_legal_pages, remove_legal_pages)]
