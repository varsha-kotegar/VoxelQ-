interface Props {
  waitTimeSeconds: number | null;
}

export function WaitTimeCard({ waitTimeSeconds }: Props) {
  return (
    <div className="rounded-lg bg-panel border border-panelBorder px-6 py-5">
      <span className="text-xs uppercase tracking-widest text-textDim font-sans">
        Estimated Wait Time
      </span>
      <div className="mt-2 font-mono text-4xl font-semibold text-accent">
        {waitTimeSeconds !== null ? `${waitTimeSeconds.toFixed(1)}s` : "—"}
      </div>
    </div>
  );
}
