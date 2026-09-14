# DriveScope

**Experiment & Evaluation Infrastructure for Vision-Language-Action (VLA) Foundation Models.**

DriveScope is an open-source orchestration and evaluation platform for Vision-Language-Action (VLA) models and physical-AI agents. It provides a reproducible experimentation layer sitting around scenario sequences, camera observations, model inference heads, reasoning traces, metric evaluations, sensor perturbations, and failure analysis — so model behavior can be measured, compared, and reproduced across hardware setups.

[![CI/CD Pipeline](https://github.com/paul-abhirup/DriveScope/actions/workflows/ci.yml/badge.svg)](https://github.com/paul-abhirup/DriveScope/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-emerald.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](pyproject.toml)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-black.svg)](apps/web)
[![CPU First](https://img.shields.io/badge/Compute-Laptop%20%2F%20CPU%20Friendly-green.svg)](docs/architecture.md)

---

## Key Capabilities

- 🎯 **Pluggable VLA Adapters**: Evaluate models via strict contracts (`MockVLA`, `RuleBaseline`, `LocalQuantizedVLM` via int4 GGUF/ONNX on CPU, or remote multimodal APIs).
- 🧠 **Reasoning-Action Consistency**: Quantify whether verbal chain-of-thought explanations ("pedestrian entering road") actually align with continuous actuator head actions (steering, brake, throttle).
- 🔬 **Sensor Perturbation & Robustness Curves**: Test degradation against physical CMOS noise, rolling shutter skew, exposure variations, motion blur, and frame drops.
- 📡 **Physical Sensor Rig Integration (ECE Core)**: Stream live frames with microsecond hardware timestamps and 6-DOF IMU telemetry from an ESP32-CAM or Raspberry Pi rig via `HardwareScenarioSource`.
- 🔍 **Failure Intelligence Explorer**: Tag, filter, and cluster failures (contradictions, missed hazards, TTC breaches, unnecessary interventions) to diagnose failure modes.
- ⏱️ **Synchronized Replay Workbench**: Frame-by-frame visual inspection of video observations, model reasoning, action gauges, ground truth targets, and latency.
- ⚡ **Dual Execution Engines**: Run locally in seconds via `MODE=minimal` (SQLite + in-process async queue) or deploy full distributed clusters via Docker Compose (FastAPI + PostgreSQL + Redis + Celery + Next.js).

---

## Architecture

```
                         Next.js 14 / TypeScript UI
                                   │
                          REST + WebSockets
                                   │
                         FastAPI Control Plane
                                   │
        ┌──────────────────┬──────┴───────────┬──────────────────┐
        │                  │                  │                  │
  Scenario Service     Run Service      Analysis Service          │
        │                  │                  │                  │
        └────────────── Database Engine ──────┴──────────────────┘
                 (SQLite in minimal / PostgreSQL in docker)
                                   │
                          Execution Dispatcher
                 (In-process async / Celery + Redis)
                                   │
                    ┌──────────────┴──────────────┐
              Inference Worker              Evaluation Worker
                    │                              │
               VLA Adapters                  Metric Engine
           (Mock / Rule / Quantized          (Action, Temporal,
             VLM / Remote API)              Safety, Consistency,
                                                 Robustness)

        Scenario Source Abstraction
        ├── DatasetScenarioSource (Prerecorded frame sequences)
        ├── HardwareScenarioSource (ESP32-CAM / Pi Camera live streams)
        └── SimulatorScenarioSource (Pluggable CARLA / Simulation bridge)
```

---

## Quickstart

### Option 1: Minimal Mode (Zero Docker, Low-Spec Laptops, Instant Start)

Runs on standard CPUs using SQLite and an in-process async execution loop (~250 MB RAM):

```bash
# 1. Clone repository
git clone https://github.com/paul-abhirup/DriveScope.git
cd DriveScope

# 2. Install dependencies & packages in editable mode
pip install -r requirements.txt
pip install -e packages/scenario-schema
pip install -e packages/vla-sdk

# 3. Generate benchmark demo dataset
python data/generate_demo_data.py

# 4. Start FastAPI Control Plane
MODE=minimal uvicorn services.api.main:app --reload --port 8000
```

Start the Next.js frontend in a separate terminal:

```bash
cd apps/web
npm install
npm run dev
```

Visit [`http://localhost:3000`](http://localhost:3000) to open the DriveScope Workbench.

---

### Option 2: Full Distributed Stack (Docker Compose)

Starts the Web UI, API, Celery Worker, PostgreSQL, Redis, and MinIO:

```bash
docker compose -f infra/docker-compose.yml up --build
```

---

## Repository Structure

```
DriveScope/
├── apps/
│   └── web/                         # Next.js 14 + TypeScript + Tailwind UI
│       ├── src/app/                 # Dashboard, Scenarios, Builder, Replay, Compare, Failures, Models
│       ├── src/components/          # Navbar, MetricCard, StatusBadge, Timeline
│       └── src/lib/api.ts           # Typed API Client
├── packages/
│   ├── scenario-schema/             # Shared Pydantic data models & contracts
│   │   └── drivescope_schema/       # Scenario, Observation, VLAOutput, Trace, Metric, Failure, Manifest
│   └── vla-sdk/                     # ScenarioSource & VLAAdapter protocol interfaces
│       └── drivescope_vla_sdk/      # DatasetScenarioSource, HardwareScenarioSource
├── models/
│   └── adapters/                    # Model Adapter implementations
│       ├── base.py                  # BaseVLAAdapter class
│       ├── mock.py                  # Deterministic MockVLA (seedable synthetic generator)
│       ├── rule_baseline.py         # Heuristic rule-based driving baseline
│       ├── local_small_vlm.py       # Quantized Small VLM (GGUF / ONNX on CPU)
│       ├── remote.py                # Hosted API / Remote multimodal adapter
│       └── registry.py              # Adapter registry & health probes
├── evaluation/                      # Multi-dimensional Evaluation Suite
│   ├── action.py                    # Steering/brake/throttle MAE, RMSE, cumulative drift
│   ├── temporal.py                  # Mean/p95 latency, hazard reaction delay
│   ├── safety.py                    # Time-to-Collision (TTC) breaches, missed hazards
│   ├── reasoning.py                 # Multi-factor Reasoning-Action Consistency scoring
│   ├── perturbation.py              # Calibrated CMOS noise, rolling shutter, blur, exposure, frame drop
│   ├── robustness.py                # Metric degradation slopes & delta analysis
│   └── engine.py                    # Central EvaluationEngine orchestrator
├── services/
│   ├── api/                         # FastAPI Control Plane
│   │   ├── main.py                  # FastAPI app with REST, CORS, and WebSocket routing
│   │   ├── database.py              # SQLAlchemy engine (SQLite minimal / PostgreSQL docker)
│   │   ├── models/db_models.py      # Relational schemas (Scenarios, Runs, Traces, Metrics, Failures)
│   │   ├── routers/                 # /scenarios, /models, /experiments, /runs, /failures, /export, /ws
│   │   └── services/                # ScenarioService, RunService, AnalysisService
│   └── worker/                      # Celery & in-process execution workers
│       ├── celery_app.py            # Celery configuration
│       ├── runner.py                # Deterministic frame loop & evaluation pipeline
│       └── tasks.py                 # Asynchronous task wrappers
├── hardware/
│   └── esp32_cam/                   # Physical sensor rig Arduino firmware (MJPEG + Hardware Timestamps + Servos)
├── data/
│   ├── manifests/                   # demo_scenarios_manifest.json
│   ├── sample/scenarios/            # Curated benchmark test sequences with frame data & ground truth
│   └── generate_demo_data.py        # Scenario suite generator
├── infra/
│   ├── docker-compose.yml           # Multi-service stack (Web, API, Worker, Postgres, Redis, MinIO)
│   ├── Dockerfile.api               # API container
│   ├── Dockerfile.worker            # Worker container
│   └── Dockerfile.web               # Next.js web container
├── docs/
│   ├── architecture.md              # System design & execution flows
│   ├── references.md                # Research citations & physical AI foundations
│   ├── adr/                         # Architecture Decision Records (ADR 0001 - 0005)
│   └── research-notes/              # Reasoning-action consistency mathematical formulation
├── tests/
│   ├── unit/                        # Tests for schemas, adapters, evaluations, perturbations
│   ├── api/                         # API endpoint tests & full lifecycle integration tests
│   └── reproducibility/             # Deterministic seed reproducibility validation
├── .github/workflows/ci.yml         # Automated GitHub Actions CI/CD Pipeline
├── pyproject.toml / requirements.txt
└── .env.example / .gitignore
```

---

## Multi-Factor Reasoning-Action Consistency

DriveScope mathematically assesses whether the model's stated verbal reasoning corresponds to its actual actuator commands:

$$\text{Consistency} = 0.35 \cdot S_{\text{hazard}} + 0.25 \cdot S_{\text{temp}} + 0.25 \cdot S_{\text{dir}} + 0.15 \cdot S_{\text{conf}}$$

- **$S_{\text{hazard}}$ (Hazard-Action Agreement)**: Verifies if verbal hazard identification induces braking ($\text{brake} \ge 0.30$).
- **$S_{\text{dir}}$ (Directional Agreement)**: Verifies if lateral intent ("turn left", "steer right") matches steering angle.
- **$S_{\text{temp}}$ (Temporal Alignment)**: Measures latency between hazard realization and action onset.
- **$S_{\text{conf}}$ (Confidence Calibration)**: Flags overconfident predictions that exhibit severe error or miss hazards.

---

## Hardware Sensor Rig (ESP32-CAM / Raspberry Pi)

DriveScope includes full firmware and adapter support for testing physical sensor hardware:
1. Flash `hardware/esp32_cam/drivescope_rig.ino` to an ESP32-CAM module.
2. The firmware serves MJPEG frames embedded with microsecond hardware timer headers (`X-Hardware-Timestamp-Us`) and controls a 2-axis Pan-Tilt servo over `/control`.
3. Point `HardwareScenarioSource(device_url="http://<ESP32_IP>/stream")` to evaluate live sensor feeds with end-to-end hardware latency tracking.

---

## Testing & Quality

Run the complete test suite including unit tests, API integration flows, sensor perturbations, and reproducibility checks:

```bash
pytest tests/
```

---

## License

MIT License. See [LICENSE](LICENSE) for details.
