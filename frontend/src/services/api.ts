import type { JobStatus, Metric, StartJobRequest } from "../types/metrics";

const API_BASE = (import.meta.env.VITE_API_BASE ?? "http://localhost:8000").replace(/\/+$/, "");

export async function startJob(req: StartJobRequest): Promise<{ job_id: string }> {
  const res = await fetch(`${API_BASE}/videos/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new Error(`start_job failed: ${res.status}`);
  return res.json();
}

export async function getStatus(jobId: string): Promise<JobStatus> {
  const res = await fetch(`${API_BASE}/videos/${jobId}/status`);
  if (!res.ok) throw new Error(`get_status failed: ${res.status}`);
  return res.json();
}

export async function getMetricsHistory(jobId: string, limit = 500): Promise<Metric[]> {
  const res = await fetch(`${API_BASE}/videos/${jobId}/metrics?limit=${limit}`);
  if (!res.ok) throw new Error(`get_metrics failed: ${res.status}`);
  return res.json();
}

export function wsUrl(jobId: string): string {
  const base = API_BASE.replace(/^http/, "ws");
  return `${base}/videos/${jobId}/stream`;
}
