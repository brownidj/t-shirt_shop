"""Expose Oscar's product index from the project search-app override.

Haystack discovers indexes through installed applications.  This project
replaces Oscar's search app to customise its forms, so it must re-export the
standard Oscar index under the replacement application's module path.
"""

from oscar.apps.search.search_indexes import ProductIndex

__all__ = ["ProductIndex"]
