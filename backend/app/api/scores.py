from fastapi import APIRouter

from app import db
from app.schemas import BestScore

router = APIRouter(tags=["scores"])


@router.get("/best-scores", response_model=list[BestScore])
def list_best_scores() -> list[BestScore]:
    return [BestScore(**score) for score in db.list_best_scores()]

