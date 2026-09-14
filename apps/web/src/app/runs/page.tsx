"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { PlayCircle, ArrowRight, RefreshCw, Layers } from "lucide-react";
import { StatusBadge } from "@/components/StatusBadge";
import { api } from "@/lib/api";

export default function RunsPage() {
  const [runs, setRuns] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchRuns = () => {
    setLoading(true);
    api.getRuns()
      .then(setRuns)
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchRuns();
    // Auto-refresh periodically for active runs
    const interval = setInterval(fetchRuns, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <PlayCircle className="w-6 h-6 text-emerald-400" />
            Experiment Runs &amp; Monitor
          </h1>
          <p className="text-zinc-400 text-sm mt-1">
            Track execution lifecycle, deterministic seed states, and trace manifests.
          </p>
        </div>
        <button
          onClick={fetchRuns}
          className="p-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 transition-colors"
          title="Refresh"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-emerald-400" : ""}`} />
        </button>
      </div>

      <div className="p-5 rounded-xl border border-zinc-800 bg-zinc-900/40">
        {runs.length === 0 ? (
          <div className="py-12 text-center text-zinc-500 text-sm">
            No experiment runs found. Launch one from the Experiment Builder!
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-zinc-400">
              <thead className="border-b border-zinc-800 text-zinc-300 uppercase tracking-wider font-mono">
                <tr>
                  <th className="pb-3">Run ID</th>
                  <th className="pb-3">Scenario</th>
                  <th className="pb-3">Model</th>
                  <th className="pb-3">Perturbation</th>
                  <th className="pb-3">Progress</th>
                  <th className="pb-3">Status</th>
                  <th className="pb-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800/60 font-mono">
                {runs.map((r) => (
                  <tr key={r.id} className="hover:bg-zinc-800/30">
                    <td className="py-3 text-zinc-200 font-bold">{r.id}</td>
                    <td className="py-3 text-zinc-300 font-sans">{r.scenario_id}</td>
                    <td className="py-3 text-emerald-400">{r.model_id}</td>
                    <td className="py-3 text-zinc-400 font-sans">
                      {r.perturbation_config ? (
                        <span className="px-2 py-0.5 rounded bg-amber-950/40 border border-amber-800/40 text-amber-400 text-[10px]">
                          {r.perturbation_config.type} ({r.perturbation_config.intensity}x)
                        </span>
                      ) : (
                        <span className="text-zinc-600">None (Baseline)</span>
                      )}
                    </td>
                    <td className="py-3">
                      <div className="w-24 bg-zinc-800 rounded-full h-1.5 overflow-hidden">
                        <div
                          className="bg-emerald-400 h-full rounded-full transition-all duration-300"
                          style={{ width: `${(r.progress || 0) * 100}%` }}
                        />
                      </div>
                    </td>
                    <td className="py-3">
                      <StatusBadge status={r.status} />
                    </td>
                    <td className="py-3 text-right">
                      <Link
                        href={`/runs/${r.id}`}
                        className="inline-flex items-center gap-1 text-emerald-400 hover:underline"
                      >
                        Replay <ArrowRight className="w-3 h-3" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
