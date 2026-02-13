import type { Graph } from "./types";

const GRAPH_PREFIX = "sdg:graph:";
const SEED_PREFIX = "sdg:seed:";

export function saveDraftGraph(challengeSlug: string, graph: Graph): void {
  localStorage.setItem(`${GRAPH_PREFIX}${challengeSlug}`, JSON.stringify(graph));
}

export function loadDraftGraph(challengeSlug: string): Graph | null {
  const raw = localStorage.getItem(`${GRAPH_PREFIX}${challengeSlug}`);
  if (!raw) {
    return null;
  }

  try {
    const parsed = JSON.parse(raw) as Graph;
    if (!Array.isArray(parsed.nodes) || !Array.isArray(parsed.edges)) {
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

export function saveLastSeed(challengeSlug: string, seed: number): void {
  localStorage.setItem(`${SEED_PREFIX}${challengeSlug}`, String(seed));
}

export function loadLastSeed(challengeSlug: string): number | null {
  const raw = localStorage.getItem(`${SEED_PREFIX}${challengeSlug}`);
  if (!raw) {
    return null;
  }

  const parsed = Number(raw);
  if (!Number.isFinite(parsed)) {
    return null;
  }
  return parsed;
}

