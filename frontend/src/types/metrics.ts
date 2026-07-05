export type DensityBand = "Low" | "Medium" | "High";

export interface Metric {
  timestamp: string;
  occupancy: number;
  avg_occupancy: number;
  arrival_rate_per_min: number;
  wait_time_seconds: number | null;
  density_band: DensityBand;
}

export interface JobStatus {
  state: "pending" | "running" | "completed" | "error";
  error: string | null;
  last_metrics: Metric | null;
}

export interface StartJobRequest {
  source: string;
  polygon: [number, number][];
  imgsz?: number;
  conf?: number;
  iou?: number;
  debounce_seconds?: number;
  window_seconds?: number;
  low_capacity?: number;
  high_capacity?: number;
}
