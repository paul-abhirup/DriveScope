"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AlertTriangle, ShieldAlert, ArrowRight, Filter } from "lucide-react";
import { api } from "@/lib/api";

export default function FailuresPage() {
  const [failures, setFailures] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedClass, setSelectedClass] = useState<string>("");
  const [selectedSeverity, setSelectedSeverity] = useState<string>("");

  useEffect(() => {
    const params: Record<string, string> = {};
    if (selectedClass) params.failure_class = selectedClass;
    if (selectedSeverity) params.severity = selectedSeverity;

    api.getFailures(params)
      .then(setFailures)
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, [selectedClass, selectedSeverity]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          <AlertTriangle className="w-6 h-6 text-rose-400" />
          Failure Intelligence Explorer
        </h1>
        <p className="text-zinc-400 text-sm mt-1">
          Cluster, filter, and drill into detected reasoning-action contradictions, missed hazards, and TTC breaches.
        </p>
      </div>

      {/* Filters */}
      <div className="p-4 rounded-xl border border-zinc-800 bg-zinc-900/40 flex flex-wrap items-center gap-4">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-zinc-400" />
          <span className="text-xs font-mono text-zinc-300">Filter:</span>
        </div>

        <select
          value={selectedClass}
          onChange={(e) => setSelectedClass(e.target.value)}
          className="px-3 py-1.5 rounded-lg bg-zinc-950 border border-zinc-800 text-zinc-100 text-xs font-mono"
        >
          <option value="">All Failure Classes</option>
          <option value="REASONING_ACTION_CONTRADICTION">Reasoning-Action Contradiction</option>
          <option value="MISSED_HAZARD">Missed Hazard</option>
          <option value="TTC_BREACH">TTC Threshold Breach</option>
          <option value="UNNECESSARY_INTERVENTION">Unnecessary Intervention</option>
        </select>

        <select
          value={selectedSeverity}
          onChange={(e) => setSelectedSeverity(e.target.value)}
          className="px-3 py-1.5 rounded-lg bg-zinc-950 border border-zinc-800 text-zinc-100 text-xs font-mono"
        >
          <option value="">All Severities</option>
          <option value="CRITICAL">Critical</option>
          <option value="HIGH">High</option>
          <option value="MEDIUM">Medium</option>
          <option value="LOW">Low</option>
        </select>
      </div>

      {/* Failures List */}
      <div className="p-5 rounded-xl border border-zinc-800 bg-zinc-900/40">
        {loading ? (
          <div className="py-12 text-center text-zinc-500 text-sm">Loading failure records...</div>
        ) : failures.length === 0 ? (
          <div className="py-12 text-center text-zinc-500 text-sm">
            No failures match current filters.
          </div>
        ) : (
          <div className="space-y-3">
            {failures.map((f) => (
              <div
                key={f.id}
                className="p-4 rounded-lg bg-zinc-950/80 border border-zinc-800/80 flex flex-col md:flex-row md:items-center justify-between gap-4"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-zinc-200">
                      {f.failure_class}
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                        f.severity === "CRITICAL"
                          ? "bg-rose-950 text-rose-400 border border-rose-800"
                          : f.severity === "HIGH"
                          ? "bg-amber-950 text-amber-400 border border-amber-800"
                          : "bg-zinc-800 text-zinc-400"
                      }`}
                    >
                      {f.severity}
                    </span>
                    <span className="text-zinc-500 text-xs font-mono">
                      Run: {f.run_id} &bull; Frame: {f.frame_idx}
                    </span>
                  </div>
                  <div className="text-xs text-zinc-400 font-mono">
                    Evidence: {JSON.stringify(f.evidence)}
                  </div>
                </div>

                <Link
                  href={`/runs/${f.run_id}`}
                  className="inline-flex items-center gap-1 text-xs font-mono text-emerald-400 hover:underline shrink-0"
                >
                  Inspect in Replay <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
