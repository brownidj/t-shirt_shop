from django.contrib import admin
from django.apps import apps
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from . import views

oscar_app = apps.get_app_config("oscar")

urlpatterns = [
    path("", views.slideshow_home, name="slideshow-home"),
    path("request-a-design/", views.request_design, name="request_design"),
    path("checkout/stripe/", views.stripe_checkout, name="stripe_checkout"),
    path("checkout/stripe/success/", views.stripe_checkout_success, name="stripe_checkout_success"),
    path("checkout/stripe/cancel/", views.stripe_checkout_cancel, name="stripe_checkout_cancel"),
    path("checkout/stripe/webhook/", views.stripe_webhook, name="stripe_webhook"),
    path(
        "basket/transfer-to-wishlist/",
        views.transfer_basket_line_to_wishlist,
        name="basket_transfer_to_wishlist",
    ),
    path("accounts/login/", views.AccountAuthView.as_view()),
    path("accounts/register/", views.AccountRegistrationView.as_view()),
    path("admin/", admin.site.urls),
    # Include Oscar without an outer namespace so child namespaces (e.g. 'dashboard') stay top-level

    # Dynamic T-shirt preview image
    path(
        "tshirt-preview/<int:product_id>/",
        views.tshirt_preview,
        name="tshirt_preview",
    ),
    path(
        "configured-tshirt/<int:product_id>/add/",
        views.add_configured_tshirt,
        name="configured_tshirt_add",
    ),
    re_path(
        r"^catalogue/(?P<product_slug>[\w-]*)_(?P<pk>\d+)/$",
        views.configured_product_detail,
        name="configured_product_detail",
    ),

    path("", include(oscar_app.urls[0])),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
