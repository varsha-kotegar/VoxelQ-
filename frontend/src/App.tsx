import { useState } from "react";
import { startJob } from "./services/api";
import { useVoxelSocket } from "./hooks/useVoxelSocket";
import { WaitTimeCard } from "./components/WaitTimeCard";
import { OccupancyCard } from "./components/OccupancyCard";
import { DensityBadge } from "./components/DensityBadge";
import { QueueChart } from "./components/QueueChart";
import { VideoPanel } from "./components/VideoPanel";

// Default source and our calibrated/scaled polygon coordinates for clip2.mp4
const DEFAULT_SOURCE = "sample_videos/clip2.mp4";
const DEFAULT_POLYGON: [number, number][] = [
  [360, 900],
  [1440, 900],
  [1440, 1080],
  [360, 1080],
];

export default function App() {
  const [jobId, setJobId] = useState<string | null>(null);
  const [source, setSource] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);

  const { latest, history, connected, done } = useVoxelSocket(jobId);

  async function handleStart() {
    setStarting(true);
    try {
      const { job_id } = await startJob({
        source: DEFAULT_SOURCE,
        polygon: DEFAULT_POLYGON,
        window_seconds: 10,
        low_capacity: 2,
        high_capacity: 5,
        debounce_seconds: 0.5,
        imgsz: 640,
        conf: 0.35,
      });
      setSource(DEFAULT_SOURCE);
      setJobId(job_id);
    } catch (err) {
      console.error("Failed to start job:", err);
    } finally {
      setStarting(false);
    }
  }

  return (
    <div className="min-h-screen bg-bg px-8 py-10">
      <div className="mx-auto max-w-5xl space-y-6">
        <header className="flex items-center justify-between">
          <div>
            <h1 className="font-mono text-2xl font-semibold text-text tracking-tight">
              VoxelQ
            </h1>
            <p className="text-sm text-textDim font-sans">Live crowd density &amp; queue wait-time</p>
          </div>
          <button
            onClick={handleStart}
            disabled={starting}
            className="rounded-md bg-accent px-4 py-2 font-sans font-medium text-bg hover:bg-[#d9922b] transition-colors disabled:opacity-50"
          >
            {starting ? "Starting…" : "Start Job"}
          </button>
        </header>

        <VideoPanel
          jobId={jobId}
          source={source}
          status={done ? "completed" : jobId ? "running" : null}
          connected={connected}
        />

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          <WaitTimeCard waitTimeSeconds={latest?.wait_time_seconds ?? null} />
          <OccupancyCard
            occupancy={latest?.occupancy ?? null}
            avgOccupancy={latest?.avg_occupancy ?? null}
          />
          <DensityBadge band={latest?.density_band ?? null} />
        </div>

        <QueueChart history={history} />
      </div>
    </div>
  );
}
