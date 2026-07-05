import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Metric } from "../types/metrics";

interface Props {
  history: Metric[];
}

export function QueueChart({ history }: Props) {
  const data = history.map((m, i) => ({
    idx: i,
    occupancy: m.occupancy,
    time: new Date(m.timestamp).toLocaleTimeString(),
  }));

  return (
    <div className="rounded-lg bg-panel border border-panelBorder px-6 py-5">
      <span className="text-xs uppercase tracking-widest text-textDim font-sans">
        Queue Trend
      </span>
      <div className="mt-4 h-64">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <defs>
              <linearGradient id="occupancyFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#F2A93B" stopOpacity={0.35} />
                <stop offset="100%" stopColor="#F2A93B" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="#22304A" strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="idx" tick={false} stroke="#22304A" />
            <YAxis
              tick={{ fill: "#8A93A6", fontFamily: "IBM Plex Mono", fontSize: 12 }}
              stroke="#22304A"
              allowDecimals={false}
            />
            <Tooltip
              contentStyle={{
                background: "#121B2E",
                border: "1px solid #22304A",
                fontFamily: "IBM Plex Mono",
                fontSize: 12,
              }}
              labelFormatter={(idx) => data[idx as number]?.time ?? ""}
            />
            <Area
              type="monotone"
              dataKey="occupancy"
              stroke="#F2A93B"
              strokeWidth={2}
              fill="url(#occupancyFill)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
