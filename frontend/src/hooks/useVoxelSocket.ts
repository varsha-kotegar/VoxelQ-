import { useEffect, useRef, useState } from "react";
import { wsUrl, getMetricsHistory } from "../services/api";
import type { Metric } from "../types/metrics";

interface VoxelSocketState {
  latest: Metric | null;
  history: Metric[];
  connected: boolean;
  done: boolean;
  error: string | null;
}

/** Subscribes to a job's live metric stream. Backend sends a cached
 * snapshot immediately on connect (event: "snapshot"), then live frames,
 * then {event: "done"} when the job finishes. */
export function useVoxelSocket(jobId: string | null, maxHistory = 200): VoxelSocketState {
  const [latest, setLatest] = useState<Metric | null>(null);
  const [history, setHistory] = useState<Metric[]>([]);
  const [connected, setConnected] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!jobId) return;

    setHistory([]);
    setDone(false);
    setError(null);

    // Fetch existing database history on connect to populate the chart immediately
    getMetricsHistory(jobId)
      .then((existingHistory) => {
        if (existingHistory && existingHistory.length > 0) {
          setHistory(existingHistory);
          // Set the last element as the latest state
          setLatest(existingHistory[existingHistory.length - 1]);
        }
      })
      .catch((err) => {
        console.warn("Could not fetch metrics history:", err);
      });

    const ws = new WebSocket(wsUrl(jobId));
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.event === "error") {
        setError(data.message ?? "unknown error");
        return;
      }
      if (data.event === "done") {
        setDone(true);
        return;
      }

      // "snapshot" events and live frames both carry metric fields directly
      const metric: Metric = {
        timestamp: data.timestamp,
        occupancy: data.occupancy,
        avg_occupancy: data.avg_occupancy,
        arrival_rate_per_min: data.arrival_rate_per_min,
        wait_time_seconds: data.wait_time_seconds,
        density_band: data.density_band,
      };

      setLatest(metric);
      
      // Prevent duplicates if we already fetched history
      setHistory((prev) => {
        if (prev.some((h) => h.timestamp === metric.timestamp)) {
          return prev;
        }
        return [...prev.slice(-(maxHistory - 1)), metric];
      });
    };

    return () => ws.close();
  }, [jobId, maxHistory]);

  return { latest, history, connected, done, error };
}
