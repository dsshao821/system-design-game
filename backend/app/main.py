from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from app import db, seed
from app.api import challenges_router, runs_router, scores_router

app = FastAPI(title="System Design Game API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    db.init_db()
    seed.seed_challenges_if_empty()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": "System Design Game API",
        "health": "/health",
        "docs": "/docs",
    }


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    return Response(status_code=204)


app.include_router(challenges_router)
app.include_router(runs_router)
app.include_router(scores_router)
