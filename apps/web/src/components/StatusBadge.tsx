import React from "react";

export function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    COMPLETED: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
    RUNNING: "bg-blue-500/10 text-blue-400 border-blue-500/30 animate-pulse",
    EVALUATING: "bg-amber-500/10 text-amber-400 border-amber-500/30",
    QUEUED: "bg-purple-500/10 text-purple-400 border-purple-500/30",
    FAILED: "bg-rose-500/10 text-rose-400 border-rose-500/30",
    CANCELLED: "bg-zinc-500/10 text-zinc-400 border-zinc-500/30",
    CREATED: "bg-zinc-800 text-zinc-400 border-zinc-700",
  };

  const currentStyle = styles[status] || styles.CREATED;

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-mono font-medium border ${currentStyle}`}>
      {status}
    </span>
  );
}
