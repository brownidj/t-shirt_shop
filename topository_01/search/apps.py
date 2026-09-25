from oscar.apps.search.apps import SearchConfig as OscarSearchConfig


class SearchConfig(OscarSearchConfig):
    """Use the project search forms while retaining Oscar's search URLs."""

    name = "topository_01.search"
