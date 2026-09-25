from oscar.apps.dashboard.apps import DashboardConfig as OscarDashboardConfig


class DashboardConfig(OscarDashboardConfig):
    """Enable project-level overrides for Oscar dashboard views."""

    name = "topository_01.dashboard"
