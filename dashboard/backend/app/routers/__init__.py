"""API routers for the dashboard backend."""

from .health import router as health_router
from .traces import router as traces_router
from .aiai import router as aiai_router
from .supervision import router as supervision_router

__all__ = [
    "health_router",
    "traces_router",
    "aiai_router",
    "supervision_router",
]
