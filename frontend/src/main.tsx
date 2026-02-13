import React, { FormEvent, useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";

import { evaluateRun, getBestScores, getChallenges, getRuns } from "./api";
import "./main.css";
import { loadDraftGraph, loadLastSeed, saveDraftGraph, saveLastSeed } from "./storage";
import type { BestScore, Challenge, EdgeMode, Graph, NodeType, RunRecord, RunResult } from "./types";

const NODE_TYPES: NodeType[] = ["lb", "api", "db", "cache", "queue", "cdn", "object_store"];
const EDGE_MODES: EdgeMode[] = ["sync", "async"];
const DEFAULT_GRAPH: Graph = { nodes: [], edges: [] };

interface CompareDelta {
  comparedRunId: number;
  throughput: number;
  latency: number;
  availability: number;
  cost: number;
  total: number;
}

function formatError(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  return "Unexpected error";
}

function formatSigned(value: number): string {
  const rounded = Number(value.toFixed(2));
  if (rounded > 0) {
    return `+${rounded}`;
  }
  return String(rounded);
}

function App() {
  const [challenges, setChallenges] = useState<Challenge[]>([]);
  const [selectedSlug, setSelectedSlug] = useState<string>("");
  const [graph, setGraph] = useState<Graph>(DEFAULT_GRAPH);
  const [seed, setSeed] = useState<number>(42);
  const [result, setResult] = useState<RunResult | null>(null);
  const [history, setHistory] = useState<RunRecord[]>([]);
  const [bestScores, setBestScores] = useState<BestScore[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [error, setError] = useState<string>("");
  const [compareDelta, setCompareDelta] = useState<CompareDelta | null>(null);
  const [loadedRunId, setLoadedRunId] = useState<number | null>(null);
  const [historyScope, setHistoryScope] = useState<"selected" | "all">("selected");

  const [nodeDraft, setNodeDraft] = useState({
    id: "",
    type: "api" as NodeType,
    replicas: 1,
    shards: 1,
  });

  const [edgeDraft, setEdgeDraft] = useState({
    source: "",
    target: "",
    mode: "sync" as EdgeMode,
  });

  const selectedChallenge = useMemo(
    () => challenges.find((challenge) => challenge.slug === selectedSlug) ?? null,
    [challenges, selectedSlug]
  );

  const selectedBestScore = useMemo(
    () => bestScores.find((score) => score.challenge_slug === selectedSlug) ?? null,
    [bestScores, selectedSlug]
  );

  useEffect(() => {
    async function bootstrap() {
      setIsLoading(true);
      setError("");
      try {
        const [challengeData, scoreData] = await Promise.all([getChallenges(), getBestScores()]);
        setChallenges(challengeData);
        setBestScores(scoreData);
        if (challengeData.length > 0) {
          setSelectedSlug(challengeData[0].slug);
        }
      } catch (err) {
        setError(`Failed to load startup data: ${formatError(err)}`);
      } finally {
        setIsLoading(false);
      }
    }

    void bootstrap();
  }, []);

  useEffect(() => {
    if (!selectedSlug) {
      return;
    }

    const savedGraph = loadDraftGraph(selectedSlug);
    setGraph(savedGraph ?? { nodes: [], edges: [] });

    const savedSeed = loadLastSeed(selectedSlug);
    setSeed(savedSeed ?? 42);

    setResult(null);
    setCompareDelta(null);
    setLoadedRunId(null);

    async function refreshHistory() {
      try {
        const runs = historyScope === "all" ? await getRuns() : await getRuns(selectedSlug);
        setHistory(runs);
      } catch (err) {
        setError(`Failed to load run history: ${formatError(err)}`);
      }
    }

    void refreshHistory();
  }, [selectedSlug, historyScope]);

  useEffect(() => {
    if (!selectedSlug) {
      return;
    }
    saveDraftGraph(selectedSlug, graph);
  }, [selectedSlug, graph]);

  useEffect(() => {
    if (!selectedSlug) {
      return;
    }
    saveLastSeed(selectedSlug, seed);
  }, [selectedSlug, seed]);

  function resetDraftsWithNode(nodeId: string): void {
    setNodeDraft((prev) => ({ ...prev, id: "" }));
    setEdgeDraft((prev) => ({
      ...prev,
      source: prev.source || nodeId,
      target: prev.target || nodeId,
    }));
  }

  function handleAddNode(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    const nodeId = nodeDraft.id.trim();
    if (!nodeId) {
      setError("Node ID is required.");
      return;
    }

    if (graph.nodes.some((node) => node.id === nodeId)) {
      setError(`Node '${nodeId}' already exists.`);
      return;
    }

    const config: Record<string, number> = {};
    if (nodeDraft.replicas > 1) {
      config.replicas = nodeDraft.replicas;
    }
    if (nodeDraft.type === "db" && nodeDraft.shards > 1) {
      config.shards = nodeDraft.shards;
    }

    setGraph((prev) => ({
      ...prev,
      nodes: [...prev.nodes, { id: nodeId, type: nodeDraft.type, config }],
    }));
    setError("");
    resetDraftsWithNode(nodeId);
  }

  function handleRemoveNode(nodeId: string): void {
    setGraph((prev) => ({
      nodes: prev.nodes.filter((node) => node.id !== nodeId),
      edges: prev.edges.filter((edge) => edge.source !== nodeId && edge.target !== nodeId),
    }));
  }

  function handleAddEdge(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();

    const source = edgeDraft.source.trim();
    const target = edgeDraft.target.trim();
    if (!source || !target) {
      setError("Edge source and target are required.");
      return;
    }

    const nodeIds = new Set(graph.nodes.map((node) => node.id));
    if (!nodeIds.has(source) || !nodeIds.has(target)) {
      setError("Edge must reference existing nodes.");
      return;
    }

    if (
      graph.edges.some(
        (edge) =>
          edge.source === source && edge.target === target && edge.mode === edgeDraft.mode
      )
    ) {
      setError("Duplicate edge detected.");
      return;
    }

    setGraph((prev) => ({
      ...prev,
      edges: [...prev.edges, { source, target, mode: edgeDraft.mode }],
    }));
    setError("");
  }

  function handleRemoveEdge(index: number): void {
    setGraph((prev) => ({
      ...prev,
      edges: prev.edges.filter((_, edgeIndex) => edgeIndex !== index),
    }));
  }

  async function runEvaluation(seedToUse: number): Promise<void> {
    if (!selectedSlug) {
      setError("Select a challenge before running the simulation.");
      return;
    }
    if (graph.nodes.length === 0) {
      setError("Add at least one node before running a simulation.");
      return;
    }

    setIsRunning(true);
    setError("");

    try {
      const run = await evaluateRun({
        challenge_slug: selectedSlug,
        graph,
        seed: seedToUse,
      });

      const [runs, scores] = await Promise.all([
        historyScope === "all" ? getRuns() : getRuns(selectedSlug),
        getBestScores(),
      ]);

      setResult(run);
      setHistory(runs);
      setBestScores(scores);
      setLoadedRunId(run.run_id);

      if (runs.length >= 2 && runs[0].run_id === run.run_id) {
        const previous = runs[1];
        setCompareDelta({
          comparedRunId: previous.run_id,
          throughput: runs[0].metrics.throughput_rps - previous.metrics.throughput_rps,
          latency: runs[0].metrics.latency_p95_ms - previous.metrics.latency_p95_ms,
          availability: Number(
            (runs[0].metrics.availability_pct - previous.metrics.availability_pct).toFixed(2)
          ),
          cost: Number((runs[0].metrics.monthly_cost_usd - previous.metrics.monthly_cost_usd).toFixed(2)),
          total: Number((runs[0].score.total - previous.score.total).toFixed(2)),
        });
      } else {
        setCompareDelta(null);
      }
    } catch (err) {
      setError(`Run failed: ${formatError(err)}`);
    } finally {
      setIsRunning(false);
    }
  }

  function handleLoadRun(run: RunRecord): void {
    setGraph(run.graph);
    setSeed(run.seed);
    setResult(run);
    setCompareDelta(null);
    setLoadedRunId(run.run_id);
    setError("");
  }

  if (isLoading) {
    return (
      <main className="app">
        <p>Loading local MVP data...</p>
      </main>
    );
  }

  if (challenges.length === 0) {
    return (
      <main className="app">
        <h1>System Design Game - Frontend</h1>
        <p>No challenges available. Verify backend startup and seed data.</p>
      </main>
    );
  }

  return (
    <main className="app">
      <header className="app-header">
        <h1>System Design Game - Local MVP</h1>
        <p className="subtitle">Design a system, run deterministic simulation, and review score breakdowns.</p>
      </header>

      {error && <div className="error">{error}</div>}

      <div className="layout">
        <section className="panel">
          <h2>Challenge Setup</h2>
          <div className="field">
            <label htmlFor="challenge-select">Challenge</label>
            <select
              id="challenge-select"
              value={selectedSlug}
              onChange={(event) => setSelectedSlug(event.target.value)}
            >
              {challenges.map((challenge) => (
                <option key={challenge.slug} value={challenge.slug}>
                  {challenge.title} ({challenge.difficulty})
                </option>
              ))}
            </select>
          </div>

          <p className="muted">
            {selectedBestScore
              ? `Best score: ${selectedBestScore.total.toFixed(2)} (run #${selectedBestScore.run_id})`
              : "Best score: no runs yet"}
          </p>

          {selectedChallenge && (
            <>
              <h3>Requirements</h3>
              <ol className="list">
                {selectedChallenge.requirements.map((requirement) => (
                  <li key={requirement}>{requirement}</li>
                ))}
              </ol>
              <h3>Hints</h3>
              <ul className="list">
                {selectedChallenge.hints.map((hint) => (
                  <li key={hint}>{hint}</li>
                ))}
              </ul>
              <p className="muted">
                Targets: {selectedChallenge.target_throughput} rps, {selectedChallenge.target_latency_p95_ms}ms p95,
                budget ${selectedChallenge.budget_monthly_usd.toFixed(0)}/month
              </p>
            </>
          )}

          <h2>Graph Editor</h2>
          <p className="muted">
            {loadedRunId ? `Loaded graph: Run #${loadedRunId}` : "Loaded graph: current draft"}
          </p>
          <form className="inline" onSubmit={handleAddNode}>
            <div className="field">
              <label htmlFor="node-id">Node ID</label>
              <input
                id="node-id"
                value={nodeDraft.id}
                onChange={(event) => setNodeDraft((prev) => ({ ...prev, id: event.target.value }))}
                placeholder="api-1"
              />
            </div>

            <div className="field">
              <label htmlFor="node-type">Type</label>
              <select
                id="node-type"
                value={nodeDraft.type}
                onChange={(event) =>
                  setNodeDraft((prev) => ({ ...prev, type: event.target.value as NodeType }))
                }
              >
                {NODE_TYPES.map((nodeType) => (
                  <option key={nodeType} value={nodeType}>
                    {nodeType}
                  </option>
                ))}
              </select>
            </div>

            <div className="field">
              <label htmlFor="replicas">Replicas</label>
              <input
                id="replicas"
                type="number"
                min={1}
                value={nodeDraft.replicas}
                onChange={(event) =>
                  setNodeDraft((prev) => ({ ...prev, replicas: Math.max(1, Number(event.target.value)) }))
                }
              />
            </div>

            <div className="field">
              <label htmlFor="shards">Shards (DB)</label>
              <input
                id="shards"
                type="number"
                min={1}
                value={nodeDraft.shards}
                onChange={(event) =>
                  setNodeDraft((prev) => ({ ...prev, shards: Math.max(1, Number(event.target.value)) }))
                }
              />
            </div>

            <button type="submit">Add Node</button>
          </form>

          {graph.nodes.length === 0 ? (
            <p className="muted">No nodes added yet.</p>
          ) : (
            <table className="nodes-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Type</th>
                  <th>Config</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {graph.nodes.map((node) => (
                  <tr key={node.id}>
                    <td>{node.id}</td>
                    <td>{node.type}</td>
                    <td>{JSON.stringify(node.config)}</td>
                    <td>
                      <button className="secondary" onClick={() => handleRemoveNode(node.id)} type="button">
                        Remove
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          <form className="inline" onSubmit={handleAddEdge}>
            <div className="field">
              <label htmlFor="edge-source">Edge source</label>
              <input
                id="edge-source"
                value={edgeDraft.source}
                onChange={(event) => setEdgeDraft((prev) => ({ ...prev, source: event.target.value }))}
                placeholder="api-1"
              />
            </div>
            <div className="field">
              <label htmlFor="edge-target">Edge target</label>
              <input
                id="edge-target"
                value={edgeDraft.target}
                onChange={(event) => setEdgeDraft((prev) => ({ ...prev, target: event.target.value }))}
                placeholder="db-1"
              />
            </div>
            <div className="field">
              <label htmlFor="edge-mode">Mode</label>
              <select
                id="edge-mode"
                value={edgeDraft.mode}
                onChange={(event) =>
                  setEdgeDraft((prev) => ({ ...prev, mode: event.target.value as EdgeMode }))
                }
              >
                {EDGE_MODES.map((mode) => (
                  <option key={mode} value={mode}>
                    {mode}
                  </option>
                ))}
              </select>
            </div>
            <button type="submit">Add Edge</button>
          </form>

          {graph.edges.length > 0 && (
            <ul className="edges">
              {graph.edges.map((edge, index) => (
                <li key={`${edge.source}-${edge.target}-${edge.mode}-${index}`}>
                  {edge.source} -[{edge.mode}]-&gt; {edge.target}{" "}
                  <button className="secondary" type="button" onClick={() => handleRemoveEdge(index)}>
                    Remove
                  </button>
                </li>
              ))}
            </ul>
          )}

          <h2>Run Simulation</h2>
          <div className="inline">
            <div className="field">
              <label htmlFor="seed-input">Seed</label>
              <input
                id="seed-input"
                type="number"
                value={seed}
                onChange={(event) => setSeed(Number(event.target.value))}
              />
            </div>
            <button type="button" onClick={() => void runEvaluation(seed)} disabled={isRunning}>
              {isRunning ? "Running..." : "Run Evaluation"}
            </button>
            <button
              className="secondary"
              type="button"
              onClick={() => void runEvaluation(seed)}
              disabled={isRunning}
            >
              Rerun Same Seed
            </button>
          </div>
        </section>

        <section className="panel">
          <h2>Run Results</h2>
          {!result ? (
            <p className="muted">Run a simulation to see metrics and score.</p>
          ) : (
            <>
              <p>
                <span className="pill">Run #{result.run_id}</span> {result.created_at}
              </p>
              <div className="metrics-grid">
                <div className="metric">
                  <span className="name">Throughput</span>
                  <span className="value">{result.metrics.throughput_rps} rps</span>
                </div>
                <div className="metric">
                  <span className="name">Latency p95</span>
                  <span className="value">{result.metrics.latency_p95_ms} ms</span>
                </div>
                <div className="metric">
                  <span className="name">Availability</span>
                  <span className="value">{result.metrics.availability_pct}%</span>
                </div>
                <div className="metric">
                  <span className="name">Monthly Cost</span>
                  <span className="value">${result.metrics.monthly_cost_usd}</span>
                </div>
              </div>

              <h3>Score Breakdown</h3>
              <div className="score-grid">
                <div className="score-item">
                  <span className="name">Total</span>
                  <strong>{result.score.total}</strong>
                </div>
                <div className="score-item">
                  <span className="name">Requirements (35)</span>
                  <strong>{result.score.requirements}</strong>
                </div>
                <div className="score-item">
                  <span className="name">Reliability (25)</span>
                  <strong>{result.score.reliability}</strong>
                </div>
                <div className="score-item">
                  <span className="name">Performance (25)</span>
                  <strong>{result.score.performance}</strong>
                </div>
                <div className="score-item">
                  <span className="name">Cost (15)</span>
                  <strong>{result.score.cost}</strong>
                </div>
              </div>

              <h3>Explanations</h3>
              <ul className="list">
                {result.score.explanations.map((note) => (
                  <li key={note}>{note}</li>
                ))}
              </ul>
            </>
          )}

          {compareDelta && (
            <>
              <h3>Compare with Previous Run #{compareDelta.comparedRunId}</h3>
              <ul className="list">
                <li>Throughput delta: {formatSigned(compareDelta.throughput)} rps</li>
                <li>Latency delta: {formatSigned(compareDelta.latency)} ms</li>
                <li>Availability delta: {formatSigned(compareDelta.availability)}%</li>
                <li>Cost delta: {formatSigned(compareDelta.cost)} USD</li>
                <li>Total score delta: {formatSigned(compareDelta.total)}</li>
              </ul>
            </>
          )}

          <h2>Run History</h2>
          <div className="inline">
            <label htmlFor="history-scope">Show</label>
            <select
              id="history-scope"
              value={historyScope}
              onChange={(event) => setHistoryScope(event.target.value as "selected" | "all")}
            >
              <option value="selected">Selected challenge only</option>
              <option value="all">All challenges</option>
            </select>
          </div>
          {history.length === 0 ? (
            <p className="muted">
              {historyScope === "all" ? "No runs yet." : "No runs for this challenge yet."}
            </p>
          ) : (
            <table className="history-table">
              <thead>
                <tr>
                  <th>Run</th>
                  <th>Challenge</th>
                  <th>Seed</th>
                  <th>Score</th>
                  <th>Metrics</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {history.map((run) => (
                  <tr key={run.run_id} className={loadedRunId === run.run_id ? "loaded-row" : undefined}>
                    <td>
                      #{run.run_id}
                      <br />
                      <span className="muted">{run.created_at}</span>
                    </td>
                    <td>{run.challenge_slug}</td>
                    <td>{run.seed}</td>
                    <td>{run.score.total}</td>
                    <td>
                      {run.metrics.throughput_rps} rps
                      <br />
                      {run.metrics.latency_p95_ms} ms
                    </td>
                    <td>
                      <button className="secondary" type="button" onClick={() => handleLoadRun(run)}>
                        Load Graph
                      </button>
                      {loadedRunId === run.run_id && <div className="muted active-run">Active</div>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      </div>
    </main>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
