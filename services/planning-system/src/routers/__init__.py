"""
Planning System Service routers package.

This package contains FastAPI routers for the Planning System service.
"""

# Import all routers here for easy access from main.py
from .plans import router as plans
from .tasks import router as tasks
from .dependencies import router as dependencies
from .forecasts import router as forecasts
from .optimization import router as optimization
