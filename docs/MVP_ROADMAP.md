# MVP Roadmap (12 weeks)

## Phase 1 (Weeks 1-2): Foundation
- Define canonical component taxonomy (LB/API/DB/cache/queue/CDN/object-store)
- Finalize challenge schema + scoring schema
- Set up monorepo and CI
- Build auth + user profile basics

## Phase 2 (Weeks 3-5): Playable core
- Requirements tab with structured prompts
- Drag/drop canvas with connectable components
- Save/load design graphs
- Challenge runner API contract

## Phase 3 (Weeks 6-8): Simulation + feedback
- Implement deterministic simulation worker
- Metrics panel (throughput, p95 latency, availability, monthly cost)
- Rule-based explanations: "why score dropped"
- Reset/re-run/compare iterations

## Phase 4 (Weeks 9-10): Content and progression
- Launch 3 production-ready challenges
- Difficulty progression and unlock logic
- Basic leaderboard + personal bests

## Phase 5 (Weeks 11-12): Polish and launch
- UX polish, accessibility, onboarding hints
- Telemetry and funnel events
- Beta launch page + waitlist integration
- Internal playtests + balancing pass

## Risks and mitigations
- **Risk:** Simulation complexity explodes
  - **Mitigation:** Keep deterministic abstractions; avoid packet-level simulation
- **Risk:** Scoring feels arbitrary
  - **Mitigation:** Explain all scoring deductions with explicit requirement linkage
- **Risk:** Content bottleneck
  - **Mitigation:** Build reusable challenge templates + authoring checklist
