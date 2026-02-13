"""API route package for System Design Game backend."""
from app.api.challenges import router as challenges_router
from app.api.runs import router as runs_router
from app.api.scores import router as scores_router

__all__ = ["challenges_router", "runs_router", "scores_router"]
