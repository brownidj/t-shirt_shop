from oscar.apps.search.views.base import BaseSearchView as OscarBaseSearchView


class BaseSearchView(OscarBaseSearchView):
    def get_paginate_by(self, queryset):
        # The browser measures the space for complete rows. Keep the request
        # bounded and retain normal pagination when JavaScript is unavailable.
        try:
            return max(1, min(48, int(self.request.GET.get("per_page", self.paginate_by))))
        except (TypeError, ValueError):
            return self.paginate_by
