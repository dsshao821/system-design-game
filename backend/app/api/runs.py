from fastapi import APIRouter, HTTPException, Query

from app import db
from app.schemas import Graph, RunRecord, RunRequest, RunResult
from app.services.scoring import score_run
from app.services.simulation import run_simulation_for_graph

router = APIRouter(prefix="/runs", tags=["runs"])


def _validate_graph(graph: Graph) -> None:
    if not graph.nodes:
        raise HTTPException(status_code=400, detail="Graph must include at least one node")

    node_ids = [node.id for node in graph.nodes]
    if len(node_ids) != len(set(node_ids)):
        raise HTTPException(status_code=400, detail="Node IDs must be unique")

    node_set = set(node_ids)
    for edge in graph.edges:
        if edge.source not in node_set or edge.target not in node_set:
            raise HTTPException(
                status_code=400,
                detail=f"Edge references unknown node(s): {edge.source} -> {edge.target}",
            )


def _to_run_result(run: dict) -> RunResult:
    return RunResult(
        run_id=run["id"],
        challenge_slug=run["challenge_slug"],
        seed=run["seed"],
        metrics=run["metrics"],
        score=run["score"],
        created_at=run["created_at"],
    )


def _to_run_record(run: dict) -> RunRecord:
    return RunRecord(
        run_id=run["id"],
        challenge_slug=run["challenge_slug"],
        seed=run["seed"],
        graph=run["graph"],
        metrics=run["metrics"],
        score=run["score"],
        created_at=run["created_at"],
    )


@router.post("/evaluate", response_model=RunResult)
def evaluate_run(payload: RunRequest) -> RunResult:
    challenge = db.get_challenge(payload.challenge_slug)
    if challenge is None:
        raise HTTPException(status_code=404, detail="Challenge not found")

    _validate_graph(payload.graph)

    metrics = run_simulation_for_graph(payload.graph, payload.seed)
    score = score_run(challenge, payload.graph, metrics)

    run_id = db.insert_run(
        challenge_slug=payload.challenge_slug,
        graph=payload.graph.model_dump(),
        seed=payload.seed,
        metrics=metrics.model_dump(),
        score=score.model_dump(),
    )
    db.upsert_best_score(payload.challenge_slug, score.total, run_id)

    saved_run = db.get_run(run_id)
    if saved_run is None:
        raise HTTPException(status_code=500, detail="Failed to load saved run")

    return _to_run_result(saved_run)


@router.get("", response_model=list[RunRecord])
def list_runs(
    challenge_slug: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
) -> list[RunRecord]:
    return [_to_run_record(run) for run in db.list_runs(challenge_slug=challenge_slug, limit=limit)]


@router.get("/{run_id}", response_model=RunRecord)
def get_run(run_id: int) -> RunRecord:
    run = db.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return _to_run_record(run)

