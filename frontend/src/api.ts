import type { BestScore, Challenge, RunRecord, RunRequest, RunResult } from "./types";

const API_BASE = "http://127.0.0.1:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    let message = `${response.status} ${response.statusText}`;
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) {
        message = payload.detail;
      }
    } catch {
      // Keep default message if JSON parsing fails.
    }
    throw new Error(message);
  }

  return (await response.json()) as T;
}

export function getChallenges(): Promise<Challenge[]> {
  return request<Challenge[]>("/challenges");
}

export function getChallenge(slug: string): Promise<Challenge> {
  return request<Challenge>(`/challenges/${slug}`);
}

export function evaluateRun(payload: RunRequest): Promise<RunResult> {
  return request<RunResult>("/runs/evaluate", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getRuns(challengeSlug?: string): Promise<RunRecord[]> {
  if (!challengeSlug) {
    return request<RunRecord[]>("/runs");
  }
  return request<RunRecord[]>(`/runs?challenge_slug=${encodeURIComponent(challengeSlug)}`);
}

export function getBestScores(): Promise<BestScore[]> {
  return request<BestScore[]>("/best-scores");
}

