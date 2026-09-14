import React from "react";

interface MetricCardProps {
  label: string;
  value: string | number;
  unit?: string;
  subtext?: string;
  trend?: "up" | "down" | "neutral";
  color?: "emerald" | "blue" | "rose" | "amber" | "purple";
}

export function MetricCard({ label, value, unit, subtext, color = "emerald" }: MetricCardProps) {
  const colorMap = {
    emerald: "text-emerald-400 border-emerald-900/40 bg-emerald-950/20",
    blue: "text-blue-400 border-blue-900/40 bg-blue-950/20",
    rose: "text-rose-400 border-rose-900/40 bg-rose-950/20",
    amber: "text-amber-400 border-amber-900/40 bg-amber-950/20",
    purple: "text-purple-400 border-purple-900/40 bg-purple-950/20",
  };

  return (
    <div className={`p-4 rounded-xl border ${colorMap[color]} backdrop-blur`}>
      <div className="text-xs uppercase tracking-wider text-zinc-400 font-medium mb-1">
        {label}
      </div>
      <div className="flex items-baseline gap-1.5">
        <span className="text-2xl font-bold font-mono tracking-tight text-zinc-100">{value}</span>
        {unit && <span className="text-xs text-zinc-400 font-mono">{unit}</span>}
      </div>
      {subtext && <div className="text-xs text-zinc-500 mt-1">{subtext}</div>}
    </div>
  );
}
