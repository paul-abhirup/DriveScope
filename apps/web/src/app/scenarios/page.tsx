"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Film, Tag, Clock, ArrowRight, Layers } from "lucide-react";
import { api } from "@/lib/api";

export default function ScenariosPage() {
  const [scenarios, setScenarios] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTag, setSelectedTag] = useState<string | null>(null);

  useEffect(() => {
    api.getScenarios(selectedTag || undefined)
      .then(setScenarios)
      .catch((err) => console.error("Error fetching scenarios:", err))
      .finally(() => setLoading(false));
  }, [selectedTag]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <Film className="w-6 h-6 text-emerald-400" />
            Scenario Registry
          </h1>
          <p className="text-zinc-400 text-sm mt-1">
            Multimodal driving sequences with annotated ground-truth actions, hazards, and conditions.
          </p>
        </div>
      </div>

      {/* Filter Tags */}
      <div className="flex items-center gap-2 flex-wrap">
        <button
          onClick={() => setSelectedTag(null)}
          className={`px-3 py-1 rounded-full text-xs font-mono transition-colors ${
            selectedTag === null
              ? "bg-emerald-500 text-zinc-950 font-bold"
              : "bg-zinc-800 text-zinc-400 hover:text-zinc-200"
          }`}
        >
          All
        </button>
        {["crossing", "intersection", "occlusion", "urban", "benchmark"].map((tag) => (
          <button
            key={tag}
            onClick={() => setSelectedTag(tag)}
            className={`px-3 py-1 rounded-full text-xs font-mono transition-colors ${
              selectedTag === tag
                ? "bg-emerald-500 text-zinc-950 font-bold"
                : "bg-zinc-800 text-zinc-400 hover:text-zinc-200"
            }`}
          >
            #{tag}
          </button>
        ))}
      </div>

      {/* Scenario Grid */}
      {loading ? (
        <div className="py-12 text-center text-zinc-500 text-sm">Loading scenarios...</div>
      ) : scenarios.length === 0 ? (
        <div className="py-12 text-center text-zinc-500 text-sm">No scenarios found.</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {scenarios.map((sc) => (
            <div
              key={sc.id}
              className="p-5 rounded-xl border border-zinc-800 bg-zinc-900/40 hover:border-zinc-700 transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between gap-2 mb-2">
                  <h3 className="font-semibold text-zinc-100 text-base">{sc.name}</h3>
                  <span className="text-xs font-mono text-emerald-400 bg-emerald-950/60 border border-emerald-800/40 px-2 py-0.5 rounded">
                    {sc.fps} FPS
                  </span>
                </div>
                <p className="text-xs text-zinc-400 leading-relaxed mb-4 line-clamp-2">
                  {sc.description || "No description provided."}
                </p>

                <div className="flex items-center gap-4 text-xs font-mono text-zinc-400 mb-4">
                  <div className="flex items-center gap-1">
                    <Layers className="w-3.5 h-3.5 text-zinc-500" />
                    <span>{sc.total_frames} frames</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5 text-zinc-500" />
                    <span>{((sc.total_frames || 0) / (sc.fps || 20)).toFixed(1)}s duration</span>
                  </div>
                </div>

                <div className="flex items-center gap-1.5 flex-wrap mb-4">
                  {sc.tags?.map((t: string) => (
                    <span
                      key={t}
                      className="px-2 py-0.5 rounded bg-zinc-800 text-zinc-400 text-[10px] font-mono"
                    >
                      #{t}
                    </span>
                  ))}
                </div>
              </div>

              <div className="pt-4 border-t border-zinc-800/80 flex items-center justify-between">
                <span className="text-[10px] font-mono text-zinc-500">ID: {sc.id}</span>
                <Link
                  href={`/scenarios/${sc.id}`}
                  className="inline-flex items-center gap-1 text-xs font-medium text-emerald-400 hover:text-emerald-300"
                >
                  Inspect <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
