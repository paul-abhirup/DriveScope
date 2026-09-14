"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Film, ArrowLeft, Play, ShieldAlert, Activity } from "lucide-react";
import { api } from "@/lib/api";

export default function ScenarioDetailPage() {
  const params = useParams();
  const scenarioId = params?.id as string;

  const [scenario, setScenario] = useState<any>(null);
  const [frames, setFrames] = useState<any[]>([]);
  const [currentFrameIdx, setCurrentFrameIdx] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!scenarioId) return;

    Promise.all([
      api.getScenario(scenarioId),
      api.getScenarioFrames(scenarioId),
    ])
      .then(([sc, frs]) => {
        setScenario(sc);
        setFrames(frs);
      })
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, [scenarioId]);

  if (loading) {
    return <div className="py-12 text-center text-zinc-500 text-sm">Loading scenario details...</div>;
  }

  if (!scenario) {
    return <div className="py-12 text-center text-zinc-500 text-sm">Scenario not found.</div>;
  }

  const currentFrame = frames[currentFrameIdx] || frames[0];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <Link
          href="/scenarios"
          className="inline-flex items-center gap-1.5 text-xs text-zinc-400 hover:text-zinc-200 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Scenarios
        </Link>
        <Link
          href={`/experiments/new?scenario=${scenario.id}`}
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-zinc-950 font-semibold text-xs transition-colors"
        >
          <Play className="w-3.5 h-3.5" /> Launch Experiment
        </Link>
      </div>

      <div className="flex flex-col md:flex-row gap-6">
        {/* Frame Viewer */}
        <div className="flex-1 space-y-4">
          <div className="aspect-video bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden relative flex items-center justify-center">
            {currentFrame ? (
              <div className="text-center p-6 space-y-2">
                <div className="text-emerald-400 font-mono text-xs">Simulated Camera Frame</div>
                <div className="text-zinc-300 font-mono text-sm">
                  Frame: {currentFrame.frame_idx} | Time: {currentFrame.timestamp_ms}ms
                </div>
                <div className="text-xs text-zinc-500">
                  Speed: {currentFrame.ego?.speed_mps || 0} m/s
                </div>
                {currentFrame.ground_truth?.hazards?.length > 0 && (
                  <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-rose-950/60 border border-rose-800/60 text-rose-400 text-xs font-mono">
                    <ShieldAlert className="w-3.5 h-3.5" />
                    Hazard: {currentFrame.ground_truth.hazards.join(", ")}
                  </div>
                )}
              </div>
            ) : (
              <div className="text-zinc-500 text-xs font-mono">No frames available</div>
            )}
          </div>

          {/* Timeline Scrubber */}
          {frames.length > 0 && (
            <div className="space-y-2">
              <input
                type="range"
                min="0"
                max={frames.length - 1}
                value={currentFrameIdx}
                onChange={(e) => setCurrentFrameIdx(Number(e.target.value))}
                className="w-full accent-emerald-500 bg-zinc-800 h-2 rounded cursor-pointer"
              />
              <div className="flex justify-between text-xs font-mono text-zinc-500">
                <span>00:00 (Frame 0)</span>
                <span>Frame {currentFrameIdx} / {frames.length - 1}</span>
                <span>{((frames.length - 1) / (scenario.fps || 20)).toFixed(1)}s</span>
              </div>
            </div>
          )}
        </div>

        {/* Metadata & Annotations */}
        <div className="w-full md:w-80 space-y-4">
          <div className="p-4 rounded-xl border border-zinc-800 bg-zinc-900/40">
            <h2 className="text-sm font-semibold text-zinc-200 mb-3">Scenario Metadata</h2>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between py-1 border-b border-zinc-800/60">
                <span className="text-zinc-500">ID</span>
                <span className="font-mono text-zinc-300">{scenario.id}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-zinc-800/60">
                <span className="text-zinc-500">FPS</span>
                <span className="font-mono text-zinc-300">{scenario.fps}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-zinc-800/60">
                <span className="text-zinc-500">Total Frames</span>
                <span className="font-mono text-zinc-300">{scenario.total_frames}</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-zinc-500">Expected</span>
                <span className="font-mono text-emerald-400">
                  {scenario.metadata?.expected_response || "nominal"}
                </span>
              </div>
            </div>
          </div>

          {currentFrame && (
            <div className="p-4 rounded-xl border border-zinc-800 bg-zinc-900/40">
              <h2 className="text-sm font-semibold text-zinc-200 mb-3">Ground Truth Target</h2>
              <div className="space-y-2 text-xs font-mono">
                <div className="flex justify-between">
                  <span className="text-zinc-500">Steering</span>
                  <span className="text-zinc-300">{currentFrame.ground_truth?.action?.steering ?? 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-500">Brake</span>
                  <span className="text-zinc-300">{currentFrame.ground_truth?.action?.brake ?? 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-500">Throttle</span>
                  <span className="text-zinc-300">{currentFrame.ground_truth?.action?.throttle ?? 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-500">TTC</span>
                  <span className="text-zinc-300">
                    {currentFrame.ground_truth?.ttc_seconds ? `${currentFrame.ground_truth.ttc_seconds}s` : "None"}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
