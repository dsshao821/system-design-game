# Technical Architecture

## High-level services

1. **Web App (React/TS)**
   - Renders challenge UI and design canvas
   - Maintains local graph state
   - Calls backend for challenge data, run execution, and persistence

2. **API Service (FastAPI)**
   - Auth/session
   - Challenge metadata and run orchestration
   - Score persistence and leaderboard endpoints

3. **Simulation Service (Python worker)**
   - Accepts a normalized graph model + challenge config
   - Runs deterministic capacity/failure calculations
   - Produces metrics and bottleneck explanations

4. **Data Layer**
   - PostgreSQL for users/challenges/runs/scores
   - Redis for queues + short-lived run state

## Core domain model

- `User(id, email, handle, created_at)`
- `Challenge(id, slug, title, difficulty, version)`
- `ChallengeRequirement(id, challenge_id, type, text, weight)`
- `Run(id, user_id, challenge_id, graph_json, seed, created_at)`
- `RunMetric(run_id, latency_p95, throughput, availability, monthly_cost)`
- `RunScore(run_id, total, req_score, reliability_score, cost_score, notes_json)`

## Graph model

```json
{
  "nodes": [
    {"id": "api-1", "type": "api", "config": {"replicas": 3}},
    {"id": "db-1", "type": "database", "config": {"shards": 2}}
  ],
  "edges": [
    {"source": "api-1", "target": "db-1", "mode": "sync"}
  ]
}
```

## Scoring strategy (MVP)

Weighted sum:
- Requirements coverage: 35%
- Reliability and fault tolerance: 25%
- Performance under load: 25%
- Cost efficiency: 15%

Each challenge defines expected architecture capabilities (not exact diagrams). Score compares capability fit against submitted graph.

## Non-functional requirements
- Deterministic simulation for same `seed`
- Median run response < 2s for MVP challenges
- Auditable scoring rules in config files (JSON/YAML)
- Basic anti-cheat validation on graph inputs
