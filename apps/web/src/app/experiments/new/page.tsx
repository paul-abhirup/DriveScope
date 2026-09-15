"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { FlaskConical, Play, Cpu, Sliders, ShieldCheck, Loader2 } from "lucide-react";
import { api } from "@/lib/api";

function NewExperimentContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const preselectedScenario = searchParams?.get("scenario");

  const [name, setName] = useState("VLA Baseline & Robustness Run");
  const [scenarios, setScenarios] = useState<any[]>([]);
  const [selectedScenarios, setSelectedScenarios] = useState<string[]>(
    preselectedScenario ? [preselectedScenario] : []
  );
  const [modelId, setModelId] = useState("mock-vla-v1");
  const [models, setModels] = useState<any[]>([]);
  const [evalProfile, setEvalProfile] = useState("standard");
  const [enablePerturbation, setEnablePerturbation] = useState(false);
  const [perturbationType, setPerturbationType] = useState("gaussian_noise");
  const [intensity, setIntensity] = useState(1.0);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    Promise.all([api.getScenarios(), api.getModels()])
      .then(([scs, mds]) => {
        setScenarios(scs);
        setModels(mds);
        if (!selectedScenarios.length && scs.length > 0) {
          setSelectedScenarios([scs[0].id]);
        }
      })
      .catch((err) => console.error(err));
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedScenarios.length) return alert("Select at least one scenario");

    setLoading(true);
    try {
      const expPayload: any = {
        name,
        scenario_ids: selectedScenarios,
        model_id: modelId,
        eval_profile: evalProfile,
        perturbation_profile: enablePerturbation
          ? { type: perturbationType, intensity: Number(intensity) }
          : null,
      };

      const exp = await api.createExperiment(expPayload);

      // Launch run for first scenario
      const run = await api.queueRun({
        experiment_id: exp.id,
        scenario_id: selectedScenarios[0],
        model_id: modelId,
        seed: 42,
        perturbation_config: expPayload.perturbation_profile,
      });

      router.push(`/runs/${run.id}`);
    } catch (err: any) {
      alert(`Failed to launch experiment: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          <FlaskConical className="w-6 h-6 text-emerald-400" />
          Experiment Builder
        </h1>
        <p className="text-zinc-400 text-sm mt-1">
          Configure model adapter, scenario evaluation suite, and sensor perturbation profiles.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Info */}
        <div className="p-5 rounded-xl border border-zinc-800 bg-zinc-900/40 space-y-4">
          <h2 className="text-sm font-semibold text-zinc-200">1. Experiment Configuration</h2>
          <div>
            <label className="block text-xs font-mono text-zinc-400 mb-1">Experiment Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-zinc-950 border border-zinc-800 text-zinc-100 text-sm focus:outline-none focus:border-emerald-500 font-mono"
              required
            />
          </div>
        </div>

        {/* Model Adapter */}
        <div className="p-5 rounded-xl border border-zinc-800 bg-zinc-900/40 space-y-4">
          <h2 className="text-sm font-semibold text-zinc-200 flex items-center gap-2">
            <Cpu className="w-4 h-4 text-emerald-400" />
            2. Select VLA Model Adapter
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {models.map((m) => (
              <label
                key={m.adapter_id}
                className={`p-3 rounded-lg border cursor-pointer transition-all flex flex-col justify-between ${
                  modelId === m.adapter_id
                    ? "border-emerald-500 bg-emerald-950/20"
                    : "border-zinc-800 bg-zinc-950/60 hover:border-zinc-700"
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-mono text-xs font-bold text-zinc-200">{m.model_name}</span>
                  <input
                    type="radio"
                    name="model"
                    value={m.adapter_id}
                    checked={modelId === m.adapter_id}
                    onChange={(e) => setModelId(e.target.value)}
                    className="accent-emerald-500"
                  />
                </div>
                <div className="flex items-center justify-between text-[11px] text-zinc-500 font-mono">
                  <span>Device: {m.device}</span>
                  <span className="text-emerald-400">{m.status}</span>
                </div>
              </label>
            ))}
          </div>
        </div>

        {/* Scenario Selection */}
        <div className="p-5 rounded-xl border border-zinc-800 bg-zinc-900/40 space-y-4">
          <h2 className="text-sm font-semibold text-zinc-200">3. Target Scenarios</h2>
          <div className="space-y-2">
            {scenarios.map((sc) => (
              <label
                key={sc.id}
                className={`flex items-center justify-between p-3 rounded-lg border cursor-pointer transition-all ${
                  selectedScenarios.includes(sc.id)
                    ? "border-emerald-500 bg-emerald-950/20"
                    : "border-zinc-800 bg-zinc-950/40 hover:border-zinc-700"
                }`}
              >
                <div>
                  <div className="text-xs font-medium text-zinc-200">{sc.name}</div>
                  <div className="text-[11px] text-zinc-500 font-mono">
                    {sc.total_frames} frames &bull; {sc.id}
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={selectedScenarios.includes(sc.id)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setSelectedScenarios([...selectedScenarios, sc.id]);
                    } else {
                      setSelectedScenarios(selectedScenarios.filter((id) => id !== sc.id));
                    }
                  }}
                  className="accent-emerald-500"
                />
              </label>
            ))}
          </div>
        </div>

        {/* Perturbations (Robustness) */}
        <div className="p-5 rounded-xl border border-zinc-800 bg-zinc-900/40 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-zinc-200 flex items-center gap-2">
              <Sliders className="w-4 h-4 text-emerald-400" />
              4. Sensor &amp; Temporal Perturbation
            </h2>
            <input
              type="checkbox"
              checked={enablePerturbation}
              onChange={(e) => setEnablePerturbation(e.target.checked)}
              className="accent-emerald-500"
            />
          </div>

          {enablePerturbation && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 border-t border-zinc-800">
              <div>
                <label className="block text-xs font-mono text-zinc-400 mb-1">Perturbation Type</label>
                <select
                  value={perturbationType}
                  onChange={(e) => setPerturbationType(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-zinc-950 border border-zinc-800 text-zinc-100 text-xs font-mono"
                >
                  <option value="gaussian_noise">Gaussian Sensor Noise</option>
                  <option value="motion_blur">Motion Blur</option>
                  <option value="exposure_change">Exposure Under/Over</option>
                  <option value="compression_artifact">JPEG Compression</option>
                  <option value="frame_drop">Sensor Frame Drop</option>
                  <option value="latency_jitter">Latency Jitter</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-mono text-zinc-400 mb-1">
                  Intensity: {intensity}
                </label>
                <input
                  type="range"
                  min="0.5"
                  max="3.0"
                  step="0.5"
                  value={intensity}
                  onChange={(e) => setIntensity(Number(e.target.value))}
                  className="w-full accent-emerald-500 bg-zinc-800 h-2 rounded cursor-pointer mt-2"
                />
              </div>
            </div>
          )}
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full py-3 rounded-xl bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 text-zinc-950 font-bold text-sm transition-all flex items-center justify-center gap-2 shadow-lg shadow-emerald-950/40"
        >
          <Play className="w-4 h-4" />
          {loading ? "Queueing & Executing..." : "Launch Experiment"}
        </button>
      </form>
    </div>
  );
}

export default function NewExperimentPage() {
  return (
    <Suspense
      fallback={
        <div className="flex items-center justify-center min-h-[400px] text-zinc-500">
          <Loader2 className="w-6 h-6 animate-spin mr-2" />
          <span className="text-sm font-mono">Loading Experiment Builder...</span>
        </div>
      }
    >
      <NewExperimentContent />
    </Suspense>
  );
}
