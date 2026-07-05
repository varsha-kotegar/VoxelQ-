interface Props {
  occupancy: number | null;
  avgOccupancy: number | null;
}

export function OccupancyCard({ occupancy, avgOccupancy }: Props) {
  return (
    <div className="rounded-lg bg-panel border border-panelBorder px-6 py-5">
      <span className="text-xs uppercase tracking-widest text-textDim font-sans">
        Current Occupancy
      </span>
      <div className="mt-2 font-mono text-4xl font-semibold text-text">
        {occupancy ?? "—"} <span className="text-lg text-textDim">people</span>
      </div>
      {avgOccupancy !== null && (
        <div className="mt-1 text-sm text-textDim font-mono">
          avg {avgOccupancy.toFixed(1)} (rolling window)
        </div>
      )}
    </div>
  );
}
