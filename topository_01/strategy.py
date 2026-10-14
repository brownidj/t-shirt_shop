"""Oscar purchasing rules for Topository's print-on-demand garments."""

from oscar.apps.partner import strategy

from .models import FulfilmentSupplier


class PrintOnDemandAvailability(strategy.StockRequired):
    """Treat products fulfilled by our print partner as made-to-order."""

    def availability_policy(self, product, stockrecord):
        if stockrecord:
            try:
                if stockrecord.partner.fulfilment_supplier.active:
                    return strategy.Available()
            except FulfilmentSupplier.DoesNotExist:
                # Legacy non-POD stock records use normal Oscar rules.
                pass
        return super().availability_policy(product, stockrecord)


class Default(
    strategy.UseFirstStockRecord,
    PrintOnDemandAvailability,
    strategy.NoTax,
    strategy.Structured,
):
    """Use normal Oscar rules except for made-to-order stock records."""


class Selector(strategy.Selector):
    def strategy(self, request=None, user=None, **kwargs):
        return Default(request)
