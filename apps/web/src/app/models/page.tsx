"use client";

import { useEffect, useState } from "react";
import { Cpu, CheckCircle2, AlertCircle, Clock, Zap } from "lucide-react";
import { api } from "@/lib/api";

export default function ModelsPage() {
  const [models, setModels] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getModels()
      .then(setModels)
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          <Cpu className="w-6 h-6 text-emerald-400" />
          VLA Model Adapters
        </h1>
        <p className="text-zinc-400 text-sm mt-1">
          Registered Vision-Language-Action adapters, runtime execution environments, and latency probes.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {models.map((m) => (
          <div
            key={m.adapter_id}
            className="p-5 rounded-xl border border-zinc-800 bg-zinc-900/40 space-y-4"
          >
            <div className="flex items-start justify-between">
              <div>
                <h3 className="font-bold text-zinc-100 text-base">{m.model_name}</h3>
                <div className="text-xs font-mono text-zinc-500">ID: {m.adapter_id}</div>
              </div>
              <span
                className={`inline-flex items-center gap-1 px-2.5 py-1 rounded text-xs font-mono font-medium ${
                  m.status === "healthy"
                    ? "bg-emerald-950/60 text-emerald-400 border border-emerald-800/60"
                    : "bg-amber-950/60 text-amber-400 border border-amber-800/60"
                }`}
              >
                {m.status === "healthy" ? (
                  <CheckCircle2 className="w-3.5 h-3.5" />
                ) : (
                  <AlertCircle className="w-3.5 h-3.5" />
                )}
                {m.status}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs font-mono">
              <div className="p-2.5 rounded-lg bg-zinc-950 border border-zinc-800/80">
                <div className="text-zinc-500 text-[10px]">DEVICE / RUNTIME</div>
                <div className="text-zinc-200 mt-0.5">{m.device}</div>
              </div>
              <div className="p-2.5 rounded-lg bg-zinc-950 border border-zinc-800/80">
                <div className="text-zinc-500 text-[10px]">P50 LATENCY</div>
                <div className="text-emerald-400 mt-0.5">
                  {m.latency_p50_ms ? `${m.latency_p50_ms} ms` : "N/A"}
                </div>
              </div>
            </div>

            {m.details && (
              <div className="pt-2 border-t border-zinc-800/60 text-xs font-mono text-zinc-400">
                <span className="text-zinc-500">Details: </span>
                {JSON.stringify(m.details)}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
