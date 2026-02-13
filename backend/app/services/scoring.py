from __future__ import annotations

from typing import Any

from app.schemas import Graph, Metrics, ScoreBreakdown


def _safe_positive_int(raw: Any, default: int = 1) -> int:
    try:
        parsed = int(raw)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def score_run(challenge: dict[str, Any], graph: Graph, metrics: Metrics) -> ScoreBreakdown:
    explanations: list[str] = []
    node_types = {node.type for node in graph.nodes}

    required_node_types = challenge.get("required_node_types", [])
    missing_required = [node_type for node_type in required_node_types if node_type not in node_types]
    requirements_coverage = 1.0
    if required_node_types:
        requirements_coverage = (len(required_node_types) - len(missing_required)) / len(required_node_types)
    requirements_score = round(35 * requirements_coverage, 2)

    if missing_required:
        explanations.append(f"Missing core components: {', '.join(missing_required)}.")

    reliability_features = challenge.get("reliability_features", [])
    missing_reliability = [feature for feature in reliability_features if feature not in node_types]
    reliability_feature_ratio = 1.0
    if reliability_features:
        reliability_feature_ratio = (len(reliability_features) - len(missing_reliability)) / len(
            reliability_features
        )

    replicated_critical = any(
        node.type in {"api", "db"} and _safe_positive_int(node.config.get("replicas"), default=1) >= 2
        for node in graph.nodes
    )
    replication_ratio = 1.0 if replicated_critical else 0.0
    reliability_ratio = min(1.0, 0.75 * reliability_feature_ratio + 0.25 * replication_ratio)
    reliability_score = round(25 * reliability_ratio, 2)

    if missing_reliability:
        explanations.append(f"Reliability features missing: {', '.join(missing_reliability)}.")
    if not replicated_critical:
        explanations.append("No replicated API/DB components detected; this creates single points of failure.")

    target_throughput = int(challenge.get("target_throughput", 2000))
    target_latency = int(challenge.get("target_latency_p95_ms", 80))

    throughput_ratio = min(metrics.throughput_rps / max(target_throughput, 1), 1.0)
    latency_ratio = min(target_latency / max(metrics.latency_p95_ms, 1), 1.0)
    performance_ratio = min(1.0, 0.6 * throughput_ratio + 0.4 * latency_ratio)
    performance_score = round(25 * performance_ratio, 2)

    if metrics.throughput_rps < target_throughput:
        explanations.append(
            f"Throughput target missed ({metrics.throughput_rps} < {target_throughput} rps)."
        )
    if metrics.latency_p95_ms > target_latency:
        explanations.append(
            f"Latency target missed ({metrics.latency_p95_ms}ms > {target_latency}ms p95)."
        )

    budget = float(challenge.get("budget_monthly_usd", 1500.0))
    if metrics.monthly_cost_usd <= budget:
        cost_ratio = 1.0
    else:
        cost_ratio = max(0.0, budget / max(metrics.monthly_cost_usd, 1.0))
    cost_score = round(15 * cost_ratio, 2)

    if metrics.monthly_cost_usd > budget:
        explanations.append(
            f"Budget exceeded (${metrics.monthly_cost_usd:.2f} > ${budget:.2f} monthly)."
        )

    if not explanations:
        explanations.append("Design meets baseline challenge requirements.")

    total = round(requirements_score + reliability_score + performance_score + cost_score, 2)

    return ScoreBreakdown(
        total=total,
        requirements=requirements_score,
        reliability=reliability_score,
        performance=performance_score,
        cost=cost_score,
        explanations=explanations,
    )

