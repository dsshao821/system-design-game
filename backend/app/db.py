from __future__ import annotations

from contextlib import contextmanager
import json
import os
import sqlite3
from pathlib import Path
from typing import Any, Iterator

DB_PATH = Path(os.getenv("SDG_DB_PATH", Path(__file__).resolve().parent / "system_design_game.db"))


@contextmanager
def _connection() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def _dumps(payload: Any) -> str:
    return json.dumps(payload, separators=(",", ":"), sort_keys=True)


def _loads(raw: str) -> Any:
    return json.loads(raw)


def init_db() -> None:
    with _connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS challenges (
                slug TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                requirements_json TEXT NOT NULL,
                hints_json TEXT NOT NULL,
                required_node_types_json TEXT NOT NULL,
                reliability_features_json TEXT NOT NULL,
                target_throughput INTEGER NOT NULL,
                target_latency_p95_ms INTEGER NOT NULL,
                budget_monthly_usd REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                challenge_slug TEXT NOT NULL,
                graph_json TEXT NOT NULL,
                seed INTEGER NOT NULL,
                metrics_json TEXT NOT NULL,
                score_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
                FOREIGN KEY(challenge_slug) REFERENCES challenges(slug)
            );

            CREATE TABLE IF NOT EXISTS best_scores (
                challenge_slug TEXT PRIMARY KEY,
                total REAL NOT NULL,
                run_id INTEGER NOT NULL,
                updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
                FOREIGN KEY(challenge_slug) REFERENCES challenges(slug),
                FOREIGN KEY(run_id) REFERENCES runs(id)
            );

            CREATE INDEX IF NOT EXISTS idx_runs_challenge_created_at
            ON runs(challenge_slug, created_at DESC);
            """
        )
        conn.commit()


def count_challenges() -> int:
    with _connection() as conn:
        row = conn.execute("SELECT COUNT(*) AS total FROM challenges").fetchone()
    return int(row["total"]) if row else 0


def upsert_challenge(challenge: dict[str, Any]) -> None:
    with _connection() as conn:
        conn.execute(
            """
            INSERT INTO challenges (
                slug,
                title,
                difficulty,
                requirements_json,
                hints_json,
                required_node_types_json,
                reliability_features_json,
                target_throughput,
                target_latency_p95_ms,
                budget_monthly_usd
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(slug) DO UPDATE SET
                title = excluded.title,
                difficulty = excluded.difficulty,
                requirements_json = excluded.requirements_json,
                hints_json = excluded.hints_json,
                required_node_types_json = excluded.required_node_types_json,
                reliability_features_json = excluded.reliability_features_json,
                target_throughput = excluded.target_throughput,
                target_latency_p95_ms = excluded.target_latency_p95_ms,
                budget_monthly_usd = excluded.budget_monthly_usd
            """,
            (
                challenge["slug"],
                challenge["title"],
                challenge["difficulty"],
                _dumps(challenge["requirements"]),
                _dumps(challenge.get("hints", [])),
                _dumps(challenge.get("required_node_types", [])),
                _dumps(challenge.get("reliability_features", [])),
                int(challenge["target_throughput"]),
                int(challenge["target_latency_p95_ms"]),
                float(challenge["budget_monthly_usd"]),
            ),
        )
        conn.commit()


def _challenge_row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "slug": row["slug"],
        "title": row["title"],
        "difficulty": row["difficulty"],
        "requirements": _loads(row["requirements_json"]),
        "hints": _loads(row["hints_json"]),
        "required_node_types": _loads(row["required_node_types_json"]),
        "reliability_features": _loads(row["reliability_features_json"]),
        "target_throughput": row["target_throughput"],
        "target_latency_p95_ms": row["target_latency_p95_ms"],
        "budget_monthly_usd": row["budget_monthly_usd"],
    }


def list_challenges() -> list[dict[str, Any]]:
    with _connection() as conn:
        rows = conn.execute(
            """
            SELECT slug, title, difficulty, requirements_json, hints_json,
                   required_node_types_json, reliability_features_json,
                   target_throughput, target_latency_p95_ms, budget_monthly_usd
            FROM challenges
            ORDER BY slug
            """
        ).fetchall()
    return [_challenge_row_to_dict(row) for row in rows]


def get_challenge(slug: str) -> dict[str, Any] | None:
    with _connection() as conn:
        row = conn.execute(
            """
            SELECT slug, title, difficulty, requirements_json, hints_json,
                   required_node_types_json, reliability_features_json,
                   target_throughput, target_latency_p95_ms, budget_monthly_usd
            FROM challenges
            WHERE slug = ?
            """,
            (slug,),
        ).fetchone()
    if row is None:
        return None
    return _challenge_row_to_dict(row)


def insert_run(
    challenge_slug: str,
    graph: dict[str, Any],
    seed: int,
    metrics: dict[str, Any],
    score: dict[str, Any],
) -> int:
    with _connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO runs (
                challenge_slug,
                graph_json,
                seed,
                metrics_json,
                score_json
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                challenge_slug,
                _dumps(graph),
                seed,
                _dumps(metrics),
                _dumps(score),
            ),
        )
        conn.commit()
        return int(cursor.lastrowid)


def _run_row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "challenge_slug": row["challenge_slug"],
        "graph": _loads(row["graph_json"]),
        "seed": row["seed"],
        "metrics": _loads(row["metrics_json"]),
        "score": _loads(row["score_json"]),
        "created_at": row["created_at"],
    }


def list_runs(challenge_slug: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
    query = """
        SELECT id, challenge_slug, graph_json, seed, metrics_json, score_json, created_at
        FROM runs
    """
    params: tuple[Any, ...]
    if challenge_slug:
        query += " WHERE challenge_slug = ?"
        params = (challenge_slug, limit)
        query += " ORDER BY created_at DESC, id DESC LIMIT ?"
    else:
        params = (limit,)
        query += " ORDER BY created_at DESC, id DESC LIMIT ?"

    with _connection() as conn:
        rows = conn.execute(query, params).fetchall()

    return [_run_row_to_dict(row) for row in rows]


def get_run(run_id: int) -> dict[str, Any] | None:
    with _connection() as conn:
        row = conn.execute(
            """
            SELECT id, challenge_slug, graph_json, seed, metrics_json, score_json, created_at
            FROM runs
            WHERE id = ?
            """,
            (run_id,),
        ).fetchone()
    if row is None:
        return None
    return _run_row_to_dict(row)


def upsert_best_score(challenge_slug: str, total: float, run_id: int) -> None:
    with _connection() as conn:
        existing = conn.execute(
            "SELECT total FROM best_scores WHERE challenge_slug = ?",
            (challenge_slug,),
        ).fetchone()

        if existing is None:
            conn.execute(
                """
                INSERT INTO best_scores (challenge_slug, total, run_id)
                VALUES (?, ?, ?)
                """,
                (challenge_slug, total, run_id),
            )
        elif total > float(existing["total"]):
            conn.execute(
                """
                UPDATE best_scores
                SET total = ?, run_id = ?, updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
                WHERE challenge_slug = ?
                """,
                (total, run_id, challenge_slug),
            )
        conn.commit()


def list_best_scores() -> list[dict[str, Any]]:
    with _connection() as conn:
        rows = conn.execute(
            """
            SELECT challenge_slug, total, run_id, updated_at
            FROM best_scores
            ORDER BY total DESC
            """
        ).fetchall()
    return [
        {
            "challenge_slug": row["challenge_slug"],
            "total": float(row["total"]),
            "run_id": int(row["run_id"]),
            "updated_at": row["updated_at"],
        }
        for row in rows
    ]
