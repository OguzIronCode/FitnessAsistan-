"""UI widgets package for the DesktopApp PoC.

Exports lightweight QWidget stubs used by the PoC `MainWindow`.
"""
from .dashboard import DashboardWidget
from .profile import ProfileWidget
from .workout import WorkoutWidget
from .nutrition import NutritionWidget
from .ai import AIWidget
from .analytics import AnalyticsWidget

__all__ = [
    "DashboardWidget",
    "ProfileWidget",
    "WorkoutWidget",
    "NutritionWidget",
    "AIWidget",
    "AnalyticsWidget",
]
