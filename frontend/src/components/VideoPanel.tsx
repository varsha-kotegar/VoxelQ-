import type { JobStatus } from "../types/metrics";

interface Props {
  jobId: string | null;
  source: string | null;
  status: JobStatus["state"] | null;
  connected: boolean;
}

const STATUS_COLOR: Record<string, string> = {
  pending: "text-textDim",
  running: "text-low",
  completed: "text-accent",
  error: "text-high",
};

export function VideoPanel({ jobId, source, status, connected }: Props) {
  return (
    <div className="rounded-lg bg-panel border border-panelBorder px-6 py-4 flex flex-wrap items-center gap-6 font-mono text-sm">
      <div>
        <span className="text-textDim">source </span>
        <span className="text-text">{source ?? "—"}</span>
      </div>
      <div>
        <span className="text-textDim">job_id </span>
        <span className="text-text">{jobId ?? "—"}</span>
      </div>
      <div>
        <span className="text-textDim">status </span>
        <span className={status ? STATUS_COLOR[status] : "text-textDim"}>
          {status ?? "idle"}
        </span>
      </div>
      <div className="flex items-center gap-2">
        <span
          className={`inline-block h-2 w-2 rounded-full ${
            connected ? "bg-low" : "bg-panelBorder"
          }`}
        />
        <span className="text-textDim">{connected ? "live" : "disconnected"}</span>
      </div>
    </div>
  );
}
