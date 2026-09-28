from django.contrib import admin
from django.apps import apps
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

oscar_app = apps.get_app_config("oscar")

urlpatterns = [
    path("", views.slideshow_home, name="slideshow-home"),
    path("request-a-design/", views.request_design, name="request_design"),
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

    path("", include(oscar_app.urls[0])),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
