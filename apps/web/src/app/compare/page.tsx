"use client";

import { useEffect, useState } from "react";
import { SlidersHorizontal, ArrowRight, TrendingUp, TrendingDown, Minus } from "lucide-react";
import { api } from "@/lib/api";

export default function ComparePage() {
  const [runs, setRuns] = useState<any[]>([]);
  const [baselineId, setBaselineId] = useState<string>("");
  const [comparisonId, setComparisonId] = useState<string>("");
  const [comparisonResult, setComparisonResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.getRuns()
      .then((r) => {
        setRuns(r);
        if (r.length >= 2) {
          setBaselineId(r[1].id);
          setComparisonId(r[0].id);
        } else if (r.length === 1) {
          setBaselineId(r[0].id);
          setComparisonId(r[0].id);
        }
      })
      .catch((err) => console.error(err));
  }, []);

  const handleCompare = async () => {
    if (!baselineId || !comparisonId) return;
    setLoading(true);
    try {
      const res = await api.compareRuns(baselineId, comparisonId);
      setComparisonResult(res);
    } catch (err: any) {
      alert(`Comparison error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          <SlidersHorizontal className="w-6 h-6 text-emerald-400" />
          Run Comparison &amp; Robustness Analysis
        </h1>
        <p className="text-zinc-400 text-sm mt-1">
          Evaluate metric degradation across sensor perturbations, frame drops, and model adapter variations.
        </p>
      </div>

      {/* Selectors */}
      <div className="p-5 rounded-xl border border-zinc-800 bg-zinc-900/40 grid grid-cols-1 sm:grid-cols-3 gap-4 items-end">
        <div>
          <label className="block text-xs font-mono text-zinc-400 mb-1">Baseline Run</label>
          <select
            value={baselineId}
            onChange={(e) => setBaselineId(e.target.value)}
            className="w-full px-3 py-2 rounded-lg bg-zinc-950 border border-zinc-800 text-zinc-100 text-xs font-mono"
          >
            {runs.map((r) => (
              <option key={r.id} value={r.id}>
                {r.id} ({r.model_id} - {r.scenario_id})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-mono text-zinc-400 mb-1">Comparison / Variant Run</label>
          <select
            value={comparisonId}
            onChange={(e) => setComparisonId(e.target.value)}
            className="w-full px-3 py-2 rounded-lg bg-zinc-950 border border-zinc-800 text-zinc-100 text-xs font-mono"
          >
            {runs.map((r) => (
              <option key={r.id} value={r.id}>
                {r.id} ({r.perturbation_config ? `${r.perturbation_config.type} ` : "Baseline "} - {r.model_id})
              </option>
            ))}
          </select>
        </div>

        <button
          onClick={handleCompare}
          disabled={loading || !baselineId || !comparisonId}
          className="w-full py-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 text-zinc-950 font-bold text-xs transition-colors"
        >
          {loading ? "Comparing..." : "Compute Metric Deltas"}
        </button>
      </div>

      {/* Comparison Results */}
      {comparisonResult && (
        <div className="space-y-6">
          <div className="p-5 rounded-xl border border-zinc-800 bg-zinc-900/40">
            <h2 className="text-sm font-semibold text-zinc-100 mb-4 font-mono">
              Metric Delta Analysis
            </h2>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-zinc-400">
                <thead className="border-b border-zinc-800 text-zinc-300 uppercase tracking-wider font-mono">
                  <tr>
                    <th className="pb-3">Metric</th>
                    <th className="pb-3">Baseline</th>
                    <th className="pb-3">Comparison</th>
                    <th className="pb-3">Absolute Delta</th>
                    <th className="pb-3 text-right">Relative Shift (%)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-800/60 font-mono">
                  {Object.entries(comparisonResult.metric_deltas).map(([k, v]: [string, any]) => {
                    const isPositive = v.delta > 0;
                    const isZero = v.delta === 0;
                    return (
                      <tr key={k} className="hover:bg-zinc-800/30">
                        <td className="py-3 text-zinc-200">{k}</td>
                        <td className="py-3 text-zinc-400">{v.baseline}</td>
                        <td className="py-3 text-emerald-400">{v.comparison}</td>
                        <td className="py-3 text-zinc-300">
                          {isPositive ? `+${v.delta}` : v.delta}
                        </td>
                        <td className="py-3 text-right">
                          <span
                            className={`inline-flex items-center gap-1 font-bold ${
                              isZero
                                ? "text-zinc-500"
                                : isPositive
                                ? "text-rose-400"
                                : "text-emerald-400"
                            }`}
                          >
                            {isZero ? (
                              <Minus className="w-3 h-3" />
                            ) : isPositive ? (
                              <TrendingUp className="w-3 h-3" />
                            ) : (
                              <TrendingDown className="w-3 h-3" />
                            )}
                            {v.pct_change}%
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
