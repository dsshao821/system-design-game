from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

NodeType = Literal["lb", "api", "db", "cache", "queue", "cdn", "object_store"]
EdgeMode = Literal["sync", "async"]


class Node(BaseModel):
    id: str = Field(..., min_length=1)
    type: NodeType
    config: dict[str, Any] = Field(default_factory=dict)


class Edge(BaseModel):
    source: str = Field(..., min_length=1)
    target: str = Field(..., min_length=1)
    mode: EdgeMode = "sync"


class Graph(BaseModel):
    nodes: list[Node] = Field(default_factory=list)
    edges: list[Edge] = Field(default_factory=list)


class Challenge(BaseModel):
    slug: str
    title: str
    difficulty: str
    requirements: list[str]
    hints: list[str] = Field(default_factory=list)
    required_node_types: list[NodeType] = Field(default_factory=list)
    reliability_features: list[NodeType] = Field(default_factory=list)
    target_throughput: int
    target_latency_p95_ms: int
    budget_monthly_usd: float


class RunRequest(BaseModel):
    challenge_slug: str
    graph: Graph
    seed: int = 42


class Metrics(BaseModel):
    throughput_rps: int
    latency_p95_ms: int
    availability_pct: float
    monthly_cost_usd: float


class ScoreBreakdown(BaseModel):
    total: float
    requirements: float
    reliability: float
    performance: float
    cost: float
    explanations: list[str] = Field(default_factory=list)


class RunResult(BaseModel):
    run_id: int
    challenge_slug: str
    seed: int
    metrics: Metrics
    score: ScoreBreakdown
    created_at: str


class RunRecord(RunResult):
    graph: Graph


class BestScore(BaseModel):
    challenge_slug: str
    total: float
    run_id: int
    updated_at: str

