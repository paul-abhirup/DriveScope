"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { 
  Play, 
  FlaskConical, 
  Film, 
  AlertTriangle, 
  CheckCircle2, 
  ArrowRight, 
  Activity,
  Layers
} from "lucide-react";
import { MetricCard } from "@/components/MetricCard";
import { StatusBadge } from "@/components/StatusBadge";
import { api } from "@/lib/api";

export default function DashboardPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getDashboard()
      .then((res) => setData(res))
      .catch((err) => console.error("Error loading dashboard:", err))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-8">
      {/* Header Banner */}
      <div className="p-8 rounded-2xl bg-gradient-to-r from-zinc-900 via-zinc-900/80 to-zinc-950 border border-zinc-800 relative overflow-hidden">
        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-mono mb-4">
            <span>Vision-Language-Action Experiment Platform</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white mb-3">
            Reproducible VLA Evaluation Infrastructure
          </h1>
          <p className="text-zinc-400 text-sm sm:text-base leading-relaxed mb-6">
            Orchestrate multimodal sequences, evaluate reasoning/action consistency, quantify sensor perturbation robustness, and analyze failures across driving scenarios.
          </p>
          <div className="flex flex-wrap items-center gap-3">
            <Link
              href="/experiments/new"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-zinc-950 font-semibold text-sm transition-colors shadow-lg shadow-emerald-950/40"
            >
              <FlaskConical className="w-4 h-4" />
              Build Experiment
            </Link>
            <Link
              href="/scenarios"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-200 font-medium text-sm border border-zinc-700 transition-colors"
            >
              <Film className="w-4 h-4" />
              Browse Scenarios
            </Link>
          </div>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Total Scenarios"
          value={data?.total_scenarios ?? 0}
          unit="sequences"
          subtext="Curated benchmark tests"
          color="blue"
        />
        <MetricCard
          label="Total Runs"
          value={data?.total_runs ?? 0}
          unit="executions"
          subtext={`${data?.completed_runs ?? 0} completed`}
          color="emerald"
        />
        <MetricCard
          label="Success Rate"
          value={data?.success_rate ?? 100}
          unit="%"
          subtext="Pipeline completion rate"
          color="purple"
        />
        <MetricCard
          label="Failures Detected"
          value={data?.total_failures_detected ?? 0}
          unit="events"
          subtext="Flagged for analysis"
          color={data?.total_failures_detected > 0 ? "rose" : "amber"}
        />
      </div>

      {/* Grid: Failure Breakdown & Recent Runs */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Failure Breakdown */}
        <div className="p-6 rounded-xl border border-zinc-800 bg-zinc-900/40 backdrop-blur">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-zinc-100 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              Failure Taxonomy
            </h2>
            <Link href="/failures" className="text-xs text-zinc-400 hover:text-emerald-400 flex items-center gap-1">
              Explorer <ArrowRight className="w-3 h-3" />
            </Link>
          </div>

          {data?.failure_distribution && Object.keys(data.failure_distribution).length > 0 ? (
            <div className="space-y-3">
              {Object.entries(data.failure_distribution).map(([className, count]: [string, any]) => (
                <div key={className} className="flex items-center justify-between p-2.5 rounded-lg bg-zinc-950/60 border border-zinc-800/80 text-xs">
                  <span className="font-mono text-zinc-300">{className}</span>
                  <span className="font-bold text-amber-400 px-2 py-0.5 rounded bg-amber-950/40 border border-amber-800/40">
                    {count}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-8 text-center text-xs text-zinc-500">
              No failures detected in current runs.
            </div>
          )}
        </div>

        {/* Recent Runs */}
        <div className="lg:col-span-2 p-6 rounded-xl border border-zinc-800 bg-zinc-900/40 backdrop-blur">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-zinc-100 flex items-center gap-2">
              <Activity className="w-4 h-4 text-emerald-400" />
              Recent Experiment Runs
            </h2>
            <Link href="/runs" className="text-xs text-zinc-400 hover:text-emerald-400 flex items-center gap-1">
              View all <ArrowRight className="w-3 h-3" />
            </Link>
          </div>

          {data?.recent_runs && data.recent_runs.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-zinc-400">
                <thead className="border-b border-zinc-800 text-zinc-300 uppercase tracking-wider font-mono">
                  <tr>
                    <th className="pb-3">Run ID</th>
                    <th className="pb-3">Scenario</th>
                    <th className="pb-3">Model</th>
                    <th className="pb-3">Status</th>
                    <th className="pb-3 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-800/60">
                  {data.recent_runs.map((r: any) => (
                    <tr key={r.id} className="hover:bg-zinc-800/30">
                      <td className="py-3 font-mono text-zinc-200">{r.id}</td>
                      <td className="py-3 text-zinc-300">{r.scenario_id}</td>
                      <td className="py-3 font-mono text-xs text-emerald-400">{r.model_id}</td>
                      <td className="py-3">
                        <StatusBadge status={r.status} />
                      </td>
                      <td className="py-3 text-right">
                        <Link
                          href={`/runs/${r.id}`}
                          className="text-xs text-emerald-400 hover:underline font-mono"
                        >
                          Replay &rarr;
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="py-8 text-center text-xs text-zinc-500">
              No runs recorded yet. Start by creating an experiment!
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
