# DriveScope Implementation & Roadmap TODO

> Track development progress, verified features, and future engineering milestones across the DriveScope platform.

---

## ✅ Completed (MVP & Core Architecture)

### 1. Architecture, Protocols & Schemas
- [x] Shared Pydantic data contracts (`Scenario`, `Observation`, `GroundTruth`, `VLAOutput`, `InferenceTrace`, `Metric`, `FailureRecord`, `PerturbationConfig`, `RunManifest`) in `packages/scenario-schema/`.
- [x] Protocol abstractions (`ScenarioSource`, `VLAAdapter`) in `packages/vla-sdk/`.
- [x] `DatasetScenarioSource` for filesystem-based prerecorded multimodal driving sequences.
- [x] `HardwareScenarioSource` with hardware nanosecond timestamps (`hw_timestamp_ns`) and IMU telemetry.
- [x] Modular monorepo configuration with `pyproject.toml`, package setup scripts, and editable installs.

### 2. Pluggable VLA Model Adapters
- [x] `BaseVLAAdapter` base class.
- [x] `MockVLA` with deterministic seed reproducibility, anomaly injection, and synthetic reasoning generation.
- [x] `RuleBaselineAdapter` heuristic speed regulation and hazard avoidance baseline.
- [x] `LocalQuantizedVLM` adapter architecture for int4/int8 GGUF (llama.cpp) or ONNX small VLMs on CPU.
- [x] `RemoteVLAAdapter` for hosted multimodal API endpoints.
- [x] Central adapter registry (`models/adapters/registry.py`) and health probes.

### 3. Multi-Factor Evaluation Engine
- [x] **Action Error**: MAE/RMSE calculations for steering, brake, throttle, and cumulative lateral drift.
- [x] **Temporal Metrics**: Mean latency, p95 latency, and hazard reaction delay.
- [x] **Safety Proxies**: Min Time-to-Collision (TTC), critical threshold breaches, missed hazards, and unsafe braking.
- [x] **Reasoning-Action Consistency**: Composite multi-factor scoring (Hazard-Action Agreement, Directional Agreement, Temporal Alignment, Confidence Calibration).
- [x] **Sensor Perturbations**: Calibrated CMOS physical noise (Poisson shot + Gaussian dark current), rolling shutter skew, motion blur, exposure shifts, frame drops, and latency jitter.
- [x] **Robustness Degradation**: Delta percentage shifts and sensitivity slope calculations.

### 4. Dual-Engine FastAPI Backend
- [x] `MODE=minimal` support: In-process async task execution with thread-safe SQLite connection pooling.
- [x] `MODE=docker` support: PostgreSQL + Redis + Celery distributed worker dispatch.
- [x] REST API endpoints (`/scenarios`, `/models`, `/experiments`, `/runs`, `/failures`, `/export`).
- [x] WebSocket manager and real-time event broadcasting (`/ws/runs/{id}`, `/ws/events`).
- [x] Frame Stride (`frame_stride`) parameter for resource-constrained execution and frame-rate robustness.
- [x] Cryptographic HMAC signed shareable run links (`/api/v1/runs/{id}/share` & `/api/v1/runs/shared/{id}`).
- [x] Lightweight API Key auth module (`services/api/auth.py`).

### 5. Next.js 14 Replay Workbench
- [x] **Dashboard**: Run statistics, success rates, failure distribution, and recent activity.
- [x] **Scenario Browser**: Tag filters, FPS, frame counts, and detail view with frame scrubber.
- [x] **Experiment Builder**: Model adapter selector, scenario picker, evaluation profile, and perturbation settings.
- [x] **Runs Monitor**: Live progress tracking, deterministic seed visibility, and run status indicators.
- [x] **Replay Workbench**: Synchronized frame canvas, natural language reasoning cards, predicted vs ground-truth action gauges, and metric summary.
- [x] **Run Comparison & Robustness Diff**: Baseline vs variant metric deltas and percentage shifts.
- [x] **Failure Explorer**: Taxonomy classification, severity filters, and evidence inspection.
- [x] **VLA Adapters Health**: Runtime engine diagnostics and p50 latency probes.

### 6. Hardware Rig, Data & Quality
- [x] Arduino firmware for ESP32-CAM with microsecond timer headers and pan-tilt servo control (`hardware/esp32_cam/drivescope_rig.ino`).
- [x] Synthetic demo scenario suite generator (`data/generate_demo_data.py`) with 3 curated benchmark sequences.
- [x] Test suite: 13 unit, API integration, and seed reproducibility tests (`tests/`).
- [x] GitHub Actions CI/CD workflow (`.github/workflows/ci.yml`).
- [x] TypeScript OpenAPI generator script (`scripts/generate_openapi_client.py`).
- [x] Comprehensive Architecture documentation, ADRs 0001–0005, and rewritten `README.md`.

---

## 📋 Upcoming Tasks & Future Milestones

### Phase A: Real Model Weights & Local Quantized VLM Execution
- [ ] Add download script (`scripts/download_models.sh`) for quantized small VLMs (e.g. `SmolVLM-Instruct-256M.gguf` or `Moondream2.onnx`).
- [ ] Connect `LocalQuantizedVLM` to `llama-cpp-python` / `onnxruntime` backend for live image tokenization and prompt inference.
- [ ] Benchmark CPU inference throughput and memory footprint across quantization levels (`Q4_K_M`, `Q8_0`, `FP16`).

### Phase B: Physical Hardware Rig Testing (ECE Track)
- [ ] Deploy `drivescope_rig.ino` to a physical ESP32-CAM module and verify Wi-Fi MJPEG stream.
- [ ] Connect `HardwareScenarioSource` to live ESP32-CAM stream and validate microsecond timestamp extraction.
- [ ] Test Pan-Tilt servo adjustment commands via REST/WebSocket `/control` endpoint.
- [ ] Collect real physical sensor noise profiles (low-light, fluorescent 50Hz flicker, platform vibration) and update perturbation calibration.

### Phase C: Dataset Ingestion & Video Converter Tools
- [ ] Create dataset ingestion script (`scripts/ingest_dataset.py`) to parse nuScenes, Waymo Open Dataset, or BDD100K camera clips.
- [ ] Implement automatic ground-truth action extraction (steering angle and acceleration from ego-vehicle CAN logs).
- [ ] Add automatic thumbnail generator (`thumbnail_uri`) for high-resolution sequences to optimize frontend memory on large datasets.

### Phase D: Advanced Failure Intelligence & Clustering
- [ ] Implement vector embedding extraction for model reasoning strings (using a lightweight sentence transformer).
- [ ] Add UMAP / $k$-means clustering on failure evidence (action error + reasoning embeddings) in `AnalysisService`.
- [ ] Render interactive failure cluster scatter plot in Next.js Failure Explorer.

### Phase E: Video Exporter & Annotated Media
- [ ] Implement backend video compositor using OpenCV / FFmpeg to render replay sequences directly to MP4.
- [ ] Overlay telemetry HUD (speed, steering gauge, brake pressure bar, reasoning subtitle, TTC warnings) onto exported video.
- [ ] Add "Export Annotated Video" button to Next.js Replay Workbench.

### Phase F: Simulator Bridge (Future Extensibility)
- [ ] Implement `CarlaScenarioSource` connecting to CARLA Python API client.
- [ ] Support closed-loop step execution where VLA action commands steer the CARLA ego-vehicle.
