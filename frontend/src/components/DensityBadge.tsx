import { useEffect, useState } from "react";
import type { DensityBand } from "../types/metrics";

const BAND_COLOR: Record<DensityBand, string> = {
  Low: "bg-low text-bg",
  Medium: "bg-medium text-bg",
  High: "bg-high text-bg",
};

interface Props {
  band: DensityBand | null;
}

export function DensityBadge({ band }: Props) {
  const [flapKey, setFlapKey] = useState(0);
  const [displayBand, setDisplayBand] = useState(band);

  useEffect(() => {
    if (band && band !== displayBand) {
      setDisplayBand(band);
      setFlapKey((k) => k + 1);
    }
  }, [band, displayBand]);

  return (
    <div className="flex flex-col gap-2">
      <span className="text-xs uppercase tracking-widest text-textDim font-sans">
        Density
      </span>
      <div
        key={flapKey}
        className={`flap-tile inline-flex items-center justify-center rounded-md px-4 py-3 font-mono font-semibold text-lg tracking-widest ${
          displayBand ? BAND_COLOR[displayBand] : "bg-panelBorder text-textDim"
        }`}
      >
        {displayBand ? displayBand.toUpperCase() : "—"}
      </div>
    </div>
  );
}
