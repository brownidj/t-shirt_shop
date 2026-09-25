from django import forms
from django.utils.translation import gettext_lazy as _

from oscar.apps.search.forms import (
    BrowseCategoryForm as OscarBrowseCategoryForm,
    CategoryForm as OscarCategoryForm,
    SearchForm as OscarSearchForm,
)


SORT_BY_CHOICES = [
    (OscarSearchForm.TITLE_A_TO_Z, _("Title A - Z")),
    (OscarSearchForm.NEWEST, _("Newest")),
    (OscarSearchForm.TOP_RATED, _("Customer rating")),
    (OscarSearchForm.RELEVANCY, _("Relevancy")),
]


def sort_by_field():
    """Return the storefront's deliberately small list of sort choices."""
    return forms.ChoiceField(
        label=_("Sort by"), choices=SORT_BY_CHOICES, widget=forms.Select(), required=False
    )


class SearchForm(OscarSearchForm):
    SORT_BY_CHOICES = SORT_BY_CHOICES
    sort_by = sort_by_field()


class AlphabeticalCatalogueOrderMixin:
    """Make catalogue browsing alphabetical unless a shopper chooses a sort."""

    def search(self):
        sqs = super().search()
        if self.is_valid() and not self.cleaned_data.get("sort_by"):
            return sqs.order_by(self.SORT_BY_MAP[self.TITLE_A_TO_Z])
        return sqs


class BrowseCategoryForm(AlphabeticalCatalogueOrderMixin, OscarBrowseCategoryForm):
    SORT_BY_CHOICES = SORT_BY_CHOICES
    sort_by = sort_by_field()


class CategoryForm(AlphabeticalCatalogueOrderMixin, OscarCategoryForm):
    SORT_BY_CHOICES = SORT_BY_CHOICES
    sort_by = sort_by_field()
