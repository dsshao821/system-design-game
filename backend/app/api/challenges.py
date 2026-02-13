from fastapi import APIRouter, HTTPException

from app import db
from app.schemas import Challenge

router = APIRouter(prefix="/challenges", tags=["challenges"])


@router.get("", response_model=list[Challenge])
def list_challenges() -> list[Challenge]:
    return [Challenge(**challenge) for challenge in db.list_challenges()]


@router.get("/{slug}", response_model=Challenge)
def get_challenge(slug: str) -> Challenge:
    challenge = db.get_challenge(slug)
    if challenge is None:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return Challenge(**challenge)

