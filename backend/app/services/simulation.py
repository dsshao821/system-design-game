from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from app.schemas import Graph, Metrics

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SIM_ENGINE_SRC = _REPO_ROOT / "sim-engine" / "src"
if _SIM_ENGINE_SRC.exists():
    sim_path = str(_SIM_ENGINE_SRC)
    if sim_path not in sys.path:
        sys.path.append(sim_path)

try:
    from runner import run_simulation as _run_engine_simulation  # type: ignore
except Exception:  # pragma: no cover - fallback handles local-only use
    _run_engine_simulation = None


def _safe_positive_int(raw: Any, default: int = 1) -> int:
    try:
        parsed = int(raw)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _stable_graph_payload(graph: Graph) -> str:
    nodes = sorted(
        [{"id": node.id, "type": node.type, "config": node.config} for node in graph.nodes],
        key=lambda item: item["id"],
    )
    edges = sorted(
        [{"source": edge.source, "target": edge.target, "mode": edge.mode} for edge in graph.edges],
        key=lambda item: (item["source"], item["target"], item["mode"]),
    )
    return json.dumps({"nodes": nodes, "edges": edges}, separators=(",", ":"), sort_keys=True)


def _run_engine(seed: int) -> dict[str, float]:
    if _run_engine_simulation is None:
        return {
            "throughput_rps": float(1000 + seed % 250),
            "latency_p95_ms": float(45 + seed % 12),
            "availability_pct": 99.0,
        }

    result = _run_engine_simulation(seed=seed)
    if is_dataclass(result):
        payload = asdict(result)
    elif isinstance(result, dict):
        payload = result
    elif hasattr(result, "__dict__"):
        payload = vars(result)
    else:
        payload = {}

    return {
        "throughput_rps": float(payload.get("throughput_rps", 1200)),
        "latency_p95_ms": float(payload.get("latency_p95_ms", 48)),
        "availability_pct": float(payload.get("availability_pct", 99.2)),
    }


def run_simulation_for_graph(graph: Graph, seed: int) -> Metrics:
    stable_payload = _stable_graph_payload(graph)
    graph_hash = int(hashlib.sha256(stable_payload.encode("utf-8")).hexdigest()[:8], 16)
    combined_seed = seed + (graph_hash % 10000)
    base = _run_engine(combined_seed)

    node_counts = Counter(node.type for node in graph.nodes)
    node_count = len(graph.nodes)
    edge_count = len(graph.edges)

    replicated_critical = 0
    single_points = 0
    for node in graph.nodes:
        replicas = _safe_positive_int(node.config.get("replicas"), default=1)
        if node.type in {"api", "db"} and replicas >= 2:
            replicated_critical += 1
        if node.type in {"api", "db"} and replicas == 1:
            single_points += 1

    throughput = int(
        base["throughput_rps"]
        + node_counts["api"] * 140
        + node_counts["cache"] * 90
        + node_counts["queue"] * 60
        + node_counts["cdn"] * 75
        - node_counts["db"] * 25
        - node_counts["object_store"] * 20
    )
    throughput = max(200, throughput)

    latency = int(
        max(
            12.0,
            base["latency_p95_ms"]
            + node_counts["db"] * 5
            - node_counts["cache"] * 7
            - node_counts["cdn"] * 8
            + max(0, node_count - 6) * 2
            + edge_count,
        )
    )

    availability = (
        base["availability_pct"]
        + node_counts["lb"] * 0.12
        + replicated_critical * 0.08
        - single_points * 0.15
    )
    availability = min(99.99, max(95.0, availability))

    base_costs = {
        "lb": 60,
        "api": 120,
        "db": 250,
        "cache": 90,
        "queue": 80,
        "cdn": 110,
        "object_store": 70,
    }
    monthly_cost = 0.0
    for node in graph.nodes:
        replicas = _safe_positive_int(node.config.get("replicas"), default=1)
        shards = _safe_positive_int(node.config.get("shards"), default=1)
        multiplier = replicas * (shards if node.type == "db" else 1)
        monthly_cost += base_costs.get(node.type, 100) * multiplier

    monthly_cost += edge_count * 8

    return Metrics(
        throughput_rps=throughput,
        latency_p95_ms=latency,
        availability_pct=round(availability, 2),
        monthly_cost_usd=round(monthly_cost, 2),
    )

