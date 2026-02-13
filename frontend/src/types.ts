export type NodeType = "lb" | "api" | "db" | "cache" | "queue" | "cdn" | "object_store";
export type EdgeMode = "sync" | "async";

export interface NodeConfig {
  replicas?: number;
  shards?: number;
  [key: string]: string | number | boolean | undefined;
}

export interface Node {
  id: string;
  type: NodeType;
  config: NodeConfig;
}

export interface Edge {
  source: string;
  target: string;
  mode: EdgeMode;
}

export interface Graph {
  nodes: Node[];
  edges: Edge[];
}

export interface Challenge {
  slug: string;
  title: string;
  difficulty: string;
  requirements: string[];
  hints: string[];
  required_node_types: NodeType[];
  reliability_features: NodeType[];
  target_throughput: number;
  target_latency_p95_ms: number;
  budget_monthly_usd: number;
}

export interface RunRequest {
  challenge_slug: string;
  graph: Graph;
  seed: number;
}

export interface Metrics {
  throughput_rps: number;
  latency_p95_ms: number;
  availability_pct: number;
  monthly_cost_usd: number;
}

export interface ScoreBreakdown {
  total: number;
  requirements: number;
  reliability: number;
  performance: number;
  cost: number;
  explanations: string[];
}

export interface RunResult {
  run_id: number;
  challenge_slug: string;
  seed: number;
  metrics: Metrics;
  score: ScoreBreakdown;
  created_at: string;
}

export interface RunRecord extends RunResult {
  graph: Graph;
}

export interface BestScore {
  challenge_slug: string;
  total: number;
  run_id: number;
  updated_at: string;
}

