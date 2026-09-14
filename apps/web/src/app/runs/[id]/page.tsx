"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { 
  ArrowLeft, 
  Play, 
  Pause, 
  Download, 
  Sliders, 
  ShieldAlert, 
  Activity, 
  Cpu, 
  CheckCircle2,
  FileSpreadsheet
} from "lucide-react";
import { StatusBadge } from "@/components/StatusBadge";
import { MetricCard } from "@/components/MetricCard";
import { api } from "@/lib/api";

export default function RunReplayPage() {
  const params = useParams();
  const router = useRouter();
  const runId = params?.id as string;

  const [run, setRun] = useState<any>(null);
  const [traces, setTraces] = useState<any[]>([]);
  const [metrics, setMetrics] = useState<any[]>([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!runId) return;

    Promise.all([
      api.getRun(runId),
      api.getRunTrace(runId),
      api.getRunMetrics(runId),
    ])
      .then(([r, tr, mt]) => {
        setRun(r);
        setTraces(tr);
        setMetrics(mt);
      })
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, [runId]);

  // Autoplay loop
  useEffect(() => {
    let interval: any;
    if (isPlaying && traces.length > 0) {
      interval = setInterval(() => {
        setCurrentIdx((prev) => (prev < traces.length - 1 ? prev + 1 : 0));
      }, 150);
    }
    return () => clearInterval(interval);
  }, [isPlaying, traces.length]);

  if (loading) {
    return <div className="py-12 text-center text-zinc-500 text-sm">Loading run trace &amp; metrics...</div>;
  }

  if (!run) {
    return <div className="py-12 text-center text-zinc-500 text-sm">Run not found.</div>;
  }

  const currentTrace = traces[currentIdx] || traces[0];

  return (
    <div className="space-y-6">
      {/* Top Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link
            href="/runs"
            className="p-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold font-mono text-zinc-100">{run.id}</h1>
              <StatusBadge status={run.status} />
            </div>
            <div className="text-xs text-zinc-500 font-mono">
              Scenario: {run.scenario_id} &bull; Model: {run.model_id} &bull; Seed: {run.seed}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <a
            href={`http://localhost:8000/api/v1/export/${run.id}`}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-mono border border-zinc-700 transition-colors"
          >
            <Download className="w-3.5 h-3.5" /> Manifest JSON
          </a>
          <a
            href={`http://localhost:8000/api/v1/export/${run.id}/csv`}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-mono border border-zinc-700 transition-colors"
          >
            <FileSpreadsheet className="w-3.5 h-3.5" /> Trace CSV
          </a>
        </div>
      </div>

      {/* Main Replay Workbench Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Visual Frame & Timeline */}
        <div className="lg:col-span-2 space-y-4">
          <div className="aspect-video bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden relative flex flex-col justify-between p-6">
            <div className="flex items-center justify-between text-xs font-mono text-zinc-400">
              <span className="px-2 py-0.5 rounded bg-zinc-950/80 border border-zinc-800">
                Frame {currentTrace?.frame_idx ?? 0}
              </span>
              <span className="px-2 py-0.5 rounded bg-zinc-950/80 border border-zinc-800">
                Latency: {currentTrace?.latency_ms ?? 0}ms
              </span>
            </div>

            <div className="text-center space-y-2">
              <div className="text-emerald-400 font-mono text-xs">Synchronized Replay Canvas</div>
              <div className="text-2xl font-bold font-mono text-zinc-100">
                {currentTrace?.ego_speed_mps?.toFixed(1) ?? 0} m/s
              </div>
              {currentTrace?.hazards_present?.length > 0 && (
                <div className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-rose-950/80 border border-rose-800/80 text-rose-400 text-xs font-mono">
                  <ShieldAlert className="w-3.5 h-3.5" />
                  Active Hazard: {currentTrace.hazards_present.join(", ")}
                </div>
              )}
            </div>

            <div className="flex items-center justify-between text-xs font-mono text-zinc-500">
              <span>Time: {currentTrace?.timestamp_ms ?? 0} ms</span>
              <span>Confidence: {((currentTrace?.confidence ?? 1) * 100).toFixed(0)}%</span>
            </div>
          </div>

          {/* Player Controls & Scrubber */}
          {traces.length > 0 && (
            <div className="p-4 rounded-xl border border-zinc-800 bg-zinc-900/40 space-y-3">
              <div className="flex items-center gap-4">
                <button
                  onClick={() => setIsPlaying(!isPlaying)}
                  className="p-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-zinc-950 transition-colors"
                >
                  {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                </button>
                <input
                  type="range"
                  min="0"
                  max={traces.length - 1}
                  value={currentIdx}
                  onChange={(e) => setCurrentIdx(Number(e.target.value))}
                  className="flex-1 accent-emerald-500 bg-zinc-800 h-2 rounded cursor-pointer"
                />
                <span className="text-xs font-mono text-zinc-400 w-16 text-right">
                  {currentIdx} / {traces.length - 1}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Reasoning & Actions Comparison Panel */}
        <div className="space-y-4">
          {/* Model Reasoning */}
          <div className="p-4 rounded-xl border border-zinc-800 bg-zinc-900/40 space-y-2">
            <h2 className="text-xs font-mono uppercase tracking-wider text-zinc-400 flex items-center gap-1.5">
              <Cpu className="w-3.5 h-3.5 text-emerald-400" />
              Model Reasoning
            </h2>
            <div className="p-3 rounded-lg bg-zinc-950/80 border border-zinc-800/80 text-xs text-zinc-200 leading-relaxed font-mono min-h-[70px]">
              {currentTrace?.model_reasoning || "No natural language rationale generated for this frame."}
            </div>
          </div>

          {/* Action Heads Comparison */}
          <div className="p-4 rounded-xl border border-zinc-800 bg-zinc-900/40 space-y-3">
            <h2 className="text-xs font-mono uppercase tracking-wider text-zinc-400">
              Predicted vs Ground Truth Action
            </h2>

            <div className="space-y-3 text-xs font-mono">
              {/* Steering */}
              <div>
                <div className="flex justify-between text-zinc-400 mb-1">
                  <span>Steering</span>
                  <span className="text-emerald-400">
                    Pred: {currentTrace?.predicted_action?.steering ?? 0} | GT: {currentTrace?.ground_truth_action?.steering ?? 0}
                  </span>
                </div>
                <div className="w-full bg-zinc-800 h-2 rounded-full overflow-hidden flex">
                  <div
                    className="bg-emerald-400 h-full transition-all"
                    style={{
                      width: `${Math.min(100, Math.max(0, ((currentTrace?.predicted_action?.steering ?? 0) + 1) * 50))}%`,
                    }}
                  />
                </div>
              </div>

              {/* Brake */}
              <div>
                <div className="flex justify-between text-zinc-400 mb-1">
                  <span>Brake Pressure</span>
                  <span className="text-rose-400">
                    Pred: {currentTrace?.predicted_action?.brake ?? 0} | GT: {currentTrace?.ground_truth_action?.brake ?? 0}
                  </span>
                </div>
                <div className="w-full bg-zinc-800 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-rose-400 h-full transition-all"
                    style={{ width: `${(currentTrace?.predicted_action?.brake ?? 0) * 100}%` }}
                  />
                </div>
              </div>

              {/* Throttle */}
              <div>
                <div className="flex justify-between text-zinc-400 mb-1">
                  <span>Throttle</span>
                  <span className="text-blue-400">
                    Pred: {currentTrace?.predicted_action?.throttle ?? 0} | GT: {currentTrace?.ground_truth_action?.throttle ?? 0}
                  </span>
                </div>
                <div className="w-full bg-zinc-800 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-blue-400 h-full transition-all"
                    style={{ width: `${(currentTrace?.predicted_action?.throttle ?? 0) * 100}%` }}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Metrics Summary Section */}
      <div className="p-6 rounded-xl border border-zinc-800 bg-zinc-900/40 space-y-4">
        <h2 className="text-base font-semibold text-zinc-100 flex items-center gap-2">
          <Activity className="w-4 h-4 text-emerald-400" />
          Evaluation Metrics &amp; Consistency Scores
        </h2>

        {metrics.length === 0 ? (
          <div className="py-6 text-center text-xs text-zinc-500">No metrics computed yet.</div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {metrics.map((m) => (
              <div key={m.metric_name} className="p-3.5 rounded-lg bg-zinc-950 border border-zinc-800 font-mono text-xs">
                <div className="text-zinc-500 uppercase text-[10px] mb-1">{m.metric_group}</div>
                <div className="text-zinc-300 font-medium truncate mb-2">{m.metric_name}</div>
                <div className="text-lg font-bold text-emerald-400">{m.value}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
