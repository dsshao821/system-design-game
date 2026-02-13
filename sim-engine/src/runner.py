"""Deterministic simulation runner stub for MVP."""

from dataclasses import dataclass


@dataclass
class SimulationResult:
    throughput_rps: int
    latency_p95_ms: int
    availability_pct: float


def run_simulation(seed: int = 42) -> SimulationResult:
    # Placeholder deterministic values for early wiring and API contracts
    return SimulationResult(throughput_rps=1200 + seed % 100, latency_p95_ms=48, availability_pct=99.2)
