from pathlib import Path
from django.urls import reverse_lazy
from oscar.defaults import OSCAR_DASHBOARD_NAVIGATION as OSCAR_DEFAULT_DASHBOARD_NAVIGATION
from oscar.defaults import *  # noqa
import os

BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = os.environ.get("DJANGO_DEBUG", "True").lower() == "true"

# During local development, show transactional emails in the runserver console
# instead of trying to contact a local SMTP server.  Production continues to
# use Django's SMTP backend and must be configured with a real mail provider.
if DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "dev-change-me"
    else:
        raise RuntimeError("DJANGO_SECRET_KEY must be set in production")
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get(
        "DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1"
    ).split(",")
    if host.strip()
]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTHENTICATION_BACKENDS = ["topository_01.auth_backends.UsernameOrEmailBackend"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.flatpages",

    # Oscar core
    "oscar.config.Shop",
    "oscar.apps.analytics.apps.AnalyticsConfig",
    "oscar.apps.checkout.apps.CheckoutConfig",
    "oscar.apps.address.apps.AddressConfig",
    "oscar.apps.shipping.apps.ShippingConfig",
    "oscar.apps.catalogue.apps.CatalogueConfig",
    "oscar.apps.catalogue.reviews.apps.CatalogueReviewsConfig",
    "oscar.apps.communication.apps.CommunicationConfig",
    "oscar.apps.partner.apps.PartnerConfig",
    "oscar.apps.basket.apps.BasketConfig",
    "oscar.apps.payment.apps.PaymentConfig",
    "oscar.apps.offer.apps.OfferConfig",
    "oscar.apps.order.apps.OrderConfig",
    "oscar.apps.customer.apps.CustomerConfig",
    "topository_01.search.apps.SearchConfig",
    "oscar.apps.voucher.apps.VoucherConfig",
    "oscar.apps.wishlists.apps.WishlistsConfig",
    "topository_01.dashboard.apps.DashboardConfig",
    "oscar.apps.dashboard.reports.apps.ReportsDashboardConfig",
    "oscar.apps.dashboard.users.apps.UsersDashboardConfig",
    "oscar.apps.dashboard.orders.apps.OrdersDashboardConfig",
    "oscar.apps.dashboard.catalogue.apps.CatalogueDashboardConfig",
    "oscar.apps.dashboard.offers.apps.OffersDashboardConfig",
    "oscar.apps.dashboard.partners.apps.PartnersDashboardConfig",
    "oscar.apps.dashboard.pages.apps.PagesDashboardConfig",
    "oscar.apps.dashboard.ranges.apps.RangesDashboardConfig",
    "oscar.apps.dashboard.reviews.apps.ReviewsDashboardConfig",
    "oscar.apps.dashboard.vouchers.apps.VouchersDashboardConfig",
    "oscar.apps.dashboard.communications.apps.CommunicationsDashboardConfig",
    "oscar.apps.dashboard.shipping.apps.ShippingDashboardConfig",

    # Third-party Oscar depends on
    "widget_tweaks",
    "haystack",
    "treebeard",
    "sorl.thumbnail",
    "django_tables2",
    "topository_01"
]
SITE_ID = 1

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "oscar.apps.basket.middleware.BasketMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "topository_01.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],   # where you’ll override Oscar templates later

    "APP_DIRS": True,
    "OPTIONS": {
        "context_processors": [
            "django.template.context_processors.debug",
            "django.template.context_processors.request",
            "django.contrib.auth.context_processors.auth",
            "django.contrib.messages.context_processors.messages",
            # Oscar extras:
            "oscar.apps.search.context_processors.search_form",
            "oscar.apps.checkout.context_processors.checkout",
            "oscar.apps.communication.notifications.context_processors.notifications",
            "oscar.core.context_processors.metadata",
        ],
    },
}]

WSGI_APPLICATION = "topository_01.wsgi.application"

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}

STATIC_URL = "/static/"
STATICFILES_DIRS = [
    BASE_DIR / "static",
    ]
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Rendered shirt previews are costly image composites.  The cache key in the
# view includes source file timestamps, so changed artwork automatically bypasses
# entries before this 10-day timeout.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "topository-preview-cache",
        "TIMEOUT": 60 * 60 * 24 * 10,
        "OPTIONS": {"MAX_ENTRIES": 128},
    }
}

# --- Search backend for Oscar (django-haystack) ---
# Use the simple in-memory backend for development so you don't need to run a search service.
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.whoosh_backend.WhooshEngine',
        'PATH': BASE_DIR / 'whoosh_index',
    },
}

HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'

# --- Oscar overrides (defaults loaded above via `from oscar.defaults import *`) ---
OSCAR_SHOP_NAME = "Topository"
OSCAR_SHOP_TAGLINE = "Knowledge worth wearing"

# Address & slug behaviour
OSCAR_REQUIRED_ADDRESS_FIELDS = ["first_name", "last_name", "line1", "city"]
OSCAR_DYNAMIC_CLASS_LOADER = "oscar.core.loading.default_class_loader"
OSCAR_SLUG_ALLOW_UNICODE = False
OSCAR_SLUG_MAP = {}
OSCAR_SLUG_BLACKLIST = []
OSCAR_SLUG_FUNCTION = "oscar.core.utils.default_slugifier"

# Media / images
OSCAR_DELETE_IMAGE_FILES = False
OSCAR_MISSING_IMAGE_URL = STATIC_URL + "oscar/img/noimage.png"
OSCAR_MISSING_IMAGE_THUMBNAIL_URL = STATIC_URL + "oscar/img/noimage.png"

# Search facets (keep empty for now)
OSCAR_SEARCH_FACETS = {"fields": {}, "queries": {}}

# Locale & pagination
OSCAR_DEFAULT_CURRENCY = "AUD"
OSCAR_DEFAULT_COUNTRY = "AU"
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
STRIPE_SHIPPING_CENTS = 1000
OSCAR_PARTNER_STRATEGY = "topository_01.strategy.Selector"
OSCAR_PRODUCTS_PER_PAGE = 9
OSCAR_OFFERS_PER_PAGE = 8
OSCAR_OFFERS_IMPLEMENTED_TYPES = ()
OSCAR_REVIEWS_PER_PAGE = 3
OSCAR_MODERATE_REVIEWS = False
OSCAR_EMAILS_PER_PAGE = 8
OSCAR_ORDERS_PER_PAGE = 8
OSCAR_ADDRESSES_PER_PAGE = 8
OSCAR_NOTIFICATIONS_PER_PAGE = 8
OSCAR_DASHBOARD_ITEMS_PER_PAGE = 8
# Number of stock alerts to show per page in the dashboard
OSCAR_STOCK_ALERTS_PER_PAGE = 8

# Dashboard navigation: use Oscar's default structure
OSCAR_DASHBOARD_NAVIGATION = OSCAR_DEFAULT_DASHBOARD_NAVIGATION

# Recently viewed & basket cookies
OSCAR_RECENTLY_VIEWED_COOKIE_NAME = "oscar_history"
OSCAR_RECENTLY_VIEWED_COOKIE_LIFETIME = 60 * 60 * 24 * 7  # 7 days
OSCAR_RECENTLY_VIEWED_COOKIE_SECURE = False
OSCAR_RECENTLY_VIEWED_PRODUCTS = 20
OSCAR_BASKET_COOKIE_OPEN = "oscar_open_basket"
OSCAR_BASKET_COOKIE_SAVED = "oscar_saved_basket"
OSCAR_BASKET_COOKIE_LIFETIME = 60 * 60 * 24 * 7  # 7 days
OSCAR_BASKET_COOKIE_SECURE = False

# Alerts, redirects, feature flags
OSCAR_EAGER_ALERTS = False
OSCAR_ACCOUNTS_REDIRECT_URL = "customer:profile-view"
OSCAR_HOMEPAGE = reverse_lazy("slideshow-home")
OSCAR_HIDDEN_FEATURES = []
OSCAR_ALLOW_ANON_CHECKOUT = True

# Where to send users after login/logout (keeps beginners from landing on /accounts/profile/)
LOGIN_REDIRECT_URL = "/accounts/"
LOGOUT_REDIRECT_URL = "/"
LOGIN_URL = "/accounts/login/"
