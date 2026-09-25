from oscar.apps.dashboard.vouchers.views import (
    VoucherSetDetailView as OscarVoucherSetDetailView,
)


class VoucherSetDetailView(OscarVoucherSetDetailView):
    """Keep voucher-set result pages within the site-wide page-size limit."""

    paginate_by = 8
