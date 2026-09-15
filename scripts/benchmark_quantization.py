#!/usr/bin/env python3
"""Benchmark CPU inference throughput and memory for quantized small VLMs.

Usage:
  python scripts/benchmark_quantization.py \
      --model weights/SmolVLM2-2.2B-Instruct-Q4_K_M.gguf \
      --mmproj weights/mmproj-SmolVLM2-2.2B-Instruct-Q8_0.gguf \
      --quant q4_k_m --iterations 5 --frame path/to/frame.jpg \
      --threads 8 --output-dir data/benchmarks

The script runs `iterations` inference passes over a driving frame and reports
mean / p50 / p95 latency, generated-token rate, and peak RSS (process memory).
"""

import argparse
import glob
import json
import os
import statistics
import sys
import time
from pathlib import Path
from typing import List, Optional

from drivescope_schema.models import Observation, EgoState

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from models.adapters.local_small_vlm import LocalQuantizedVLM  # noqa: E402


def default_frame() -> Optional[str]:
    candidates = sorted(
        glob.glob(str(PROJECT_ROOT / "data" / "sample" / "scenarios" / "*" / "frames" / "*.jpg"))
    )
    return candidates[len(candidates) // 2] if candidates else None


def peak_rss_kb() -> float:
    """Peak resident set size of the current process (best-effort, Linux)."""
    try:
        with open("/proc/self/status", "r") as fh:
            for line in fh:
                if line.startswith("VmHWM:"):
                    return float(line.split()[1])
    except OSError:
        for p in glob.glob("/proc/self/smaps_rollup"):
            with open(p, "r") as fh:
                for line in fh:
                    if line.startswith("Rss:"):
                        return float(line.split()[1])
    return 0.0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, help="path to GGUF weights")
    parser.add_argument("--mmproj", required=True, help="path to mmproj vision projector")
    parser.add_argument("--quant", default="q4_k_m")
    parser.add_argument("--label", default=None, help="short label for reports (default: basename)")
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument("--n-ctx", type=int, default=4096)
    parser.add_argument("--threads", type=int, default=None, help="defaults to all cores")
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--frame", default=None, help="driving frame image path")
    parser.add_argument("--output-dir", default="data/benchmarks")
    args = parser.parse_args()

    frame_path = args.frame or default_frame()
    if not frame_path:
        parser.error("no frame image found; pass --frame")
    if not os.path.isfile(args.model):
        parser.error(f"weights not found: {args.model}")
    if not os.path.isfile(args.mmproj):
        parser.error(f"mmproj not found: {args.mmproj}")

    label = args.label or Path(args.model).stem
    adapter = LocalQuantizedVLM(
        model_id=f"benchmark-{label}",
        quantization=args.quant,
        model_path=args.model,
        mmproj_path=args.mmproj,
        n_ctx=args.n_ctx,
        n_threads=args.threads,
        temperature=args.temperature,
        max_tokens=256,
    )

    print(f"[bench] loading {label} ({args.quant}) ...")
    t0 = time.perf_counter()
    adapter.load()
    load_s = time.perf_counter() - t0
    if adapter._model is None:
        print(f"[bench] load failed: {adapter._load_error}")
        return 1
    rss_after_load_mb = peak_rss_kb() / 1024.0
    print(f"[bench] loaded in {load_s:.1f}s, peak RSS {rss_after_load_mb:.0f} MB")

    obs = Observation(
        scenario_id="benchmark_run",
        frame_idx=0,
        timestamp_ms=0,
        image_uri=frame_path,
        ego=EgoState(speed_mps=10.0),
        metadata={"hazards": []},
    )

    latencies_ms: List[float] = []
    tokens = 0
    real_inferences = 0
    for i in range(args.iterations):
        t0 = time.perf_counter()
        out = adapter.infer(obs)
        dt_ms = (time.perf_counter() - t0) * 1000.0
        if out.extra.get("inference") == "llama.cpp":
            real_inferences += 1
            latencies_ms.append(dt_ms)
        print(f"[bench] iter {i + 1}/{args.iterations}: {dt_ms:.0f} ms "
              f"(real={out.extra.get('inference')})")
        for line in (out.reasoning or "").splitlines():
            tokens += max(1, len(line.split()))

    if not latencies_ms:
        print("[bench] no real inferences succeeded; nothing to report.")
        return 1

    latencies_ms.sort()
    p50 = statistics.median(latencies_ms)
    p95 = latencies_ms[min(len(latencies_ms) * 95 // 100, len(latencies_ms) - 1)]
    mean = statistics.fmean(latencies_ms)
    tokens_per_sec = (tokens / max(sum(latencies_ms) / 1000.0, 1e-6)) if tokens else 0.0
    rss_peak_mb = peak_rss_kb() / 1024.0

    report = {
        "label": label,
        "quantization": args.quant,
        "model_path": args.model,
        "mmproj_path": args.mmproj,
        "threads": adapter.n_threads,
        "context": args.n_ctx,
        "load_time_s": round(load_s, 2),
        "rss_after_load_mb": round(rss_after_load_mb, 1),
        "rss_peak_mb": round(rss_peak_mb, 1),
        "iterations": len(latencies_ms),
        "latency_ms": {
            "mean": round(mean, 1),
            "p50": round(p50, 1),
            "p95": round(p95, 1),
        },
        "generated_tokens": tokens,
        "tokens_per_sec": round(tokens_per_sec, 2),
    }

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"benchmark_{label}_{args.quant}.json"
    out_file.write_text(json.dumps(report, indent=2) + "\n")
    print(f"\n[bench] wrote {out_file}")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())