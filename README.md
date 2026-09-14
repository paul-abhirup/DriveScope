# DriveScope

**Experiment infrastructure for evaluating Vision-Language-Action (VLA) agents — reproducibly, on a laptop and portable computers like raspberry pi.**

DriveScope is not a simulator and not a new driving model. It's the orchestration and evaluation layer that sits around scenarios, sensor sequences, model inference, experiment runs, metrics, robustness testing, and failure analysis — so that VLA behavior can be measured, compared, and reproduced instead of eyeballed from a demo video.

> Built around recorded driving scenarios as the first scenario source. The architecture is deliberately source-agnostic: CARLA, a live hardware rig, or another simulator can be plugged in later without touching the evaluation layer.

---

## Why this exists

VLA research gets hard to compare once multiple moving pieces are involved — a scenario produces images, a model produces actions and reasoning, timing matters, perturbations change the observation stream, and evaluating "was that a good decision" needs the exact context the model saw. VLAScope treats every experiment as an immutable, replayable record: same config + same seed → same result, every time.

**Central question:** can a lightweight, reproducible software layer make VLA behavior measurable across scenarios, temporal conditions, and sensor perturbations — and make failures easy to inspect and reproduce?

---

## What it does

- **Runs scenario sequences** through one or more pluggable VLA model adapters (mock, rule-based, remote API, local small VLM)
- **Captures a full trace** of every step — observation, prediction, reasoning, timing, ground truth — in a consistent schema
- **Scores reasoning/action consistency** — does the model's stated reasoning ("pedestrian entering ego path") actually match what its action head does?
- **Applies controlled perturbations** — noise, blur, exposure, compression, frame-drop, delay — and quantifies robustness degradation
- **Clusters and ranks failures** so it's a failure-analysis tool, not just a metrics dashboard
- **Runs entirely on CPU** — no dedicated GPU required for the baseline path

## What it deliberately doesn't do

- Build or modify a photorealistic 3D simulator
- Require a 7B+ VLA running locally
- Claim closed-loop autonomous-driving safety validation
- Reach for Kubernetes/Kafka/multi-region infra before there's a reason to

---

## Architecture

```
                         Next.js / TypeScript UI
                                   │
                          REST + WebSocket
                                   │
                              FastAPI API
                                   │
        ┌──────────────────┬──────┴───────────┬──────────────────┐
        │                  │                  │                  │
  Scenario Service     Run Service      Analysis Service          │
        │                  │                  │                  │
        └────────────── PostgreSQL ───────────┴──────────────────┘
                                   │
                            Redis / Celery
                                   │
                    ┌──────────────┴──────────────┐
              Inference Worker              Evaluation Worker
                    │                              │
               VLA Adapters                  Metric Engine
          (Mock / Rule / Remote /           (action, temporal,
           Local VLM / future D1.5)      safety proxy, reasoning,
                                              robustness)

        Scenario Source Abstraction
        ├── Local dataset sequences (MVP)
        ├── CARLA (future)
        └── Live hardware sensor rig (future)
```

Every model, scenario source, and evaluation profile sits behind a versioned adapter interface — the database schema and UI never depend on which one is plugged in.

---

## Tech stack

| Layer | Choice |
|---|---|
| Frontend | Next.js, TypeScript, Tailwind |
| API | FastAPI |
| Database | PostgreSQL |
| Queue / async jobs | Redis + Celery |
| Object storage | MinIO (optional; local filesystem by default) |
| Deployment | Docker Compose (local-first, cloud-ready) |

**Resource target:** 8 GB RAM minimum, 4+ CPU cores, no GPU required. A `minimal` mode (SQLite + in-process task queue, no Docker Compose) is available for weaker machines — see [Quickstart](#quickstart).

---

## Quickstart

### Full stack (Docker Compose)

```bash
git clone https://github.com/<your-username>/vlascope.git
cd vlascope
docker compose up
```

This starts the web UI, API, worker, Postgres, Redis, and (optionally) MinIO. Visit `http://localhost:3000`.

### Minimal mode (no Docker, low-spec machines)

```bash
pip install -e services/api
MODE=minimal uvicorn api.main:app --reload
```

Runs on SQLite and an in-process task queue instead of Postgres/Redis/Celery — enough to load the demo scenario set and run a full experiment loop on modest hardware.

### First run

1. Load the bundled demo scenario set (`datasets/scenarios/`)
2. Create an experiment with the `MockVLA` adapter
3. Start the run and watch live progress over WebSocket
4. Open the completed run in the replay workbench

---

## Project structure

```
vlascope/
├── apps/
│   └── web/                 # Next.js app
├── services/
│   ├── api/                 # FastAPI control plane
│   └── worker/               # Celery inference/eval jobs
├── packages/
│   ├── scenario-schema/      # shared JSON/types
│   └── vla-sdk/               # adapter contracts
├── models/adapters/          # mock, rule-baseline, remote, local, future d1.5
├── evaluation/                # action, temporal, safety, reasoning, robustness
├── data/
│   ├── manifests/
│   └── sample/                # tiny demo dataset
├── infra/
│   ├── docker-compose.yml
│   └── migrations/
├── docs/
│   ├── architecture.md
│   └── adr/
├── tests/
└── README.md
```

---

## Roadmap

| Phase | Theme | Exit criterion |
|---|---|---|
| 0 | Foundation | Runnable stack + health checks |
| 1 | Scenario system | Browse and inspect scenarios |
| 2 | Run engine | Execute deterministic MockVLA runs |
| 3 | Inference + trace | Per-frame observation → inference record |
| 4 | Evaluation | Reproducible metrics per run |
| 5 | Replay + comparison | Diagnose a failure end-to-end |
| 6 | Robustness | Quantified robustness curves |
| 7 | Failure intelligence | Failure explorer works end-to-end |
| 8 | Polish | Portfolio-grade release, docs, demo |
| 9 | Hardware source *(planned)* | Live sensor rig plugs into the same scenario contract |

Full detail lives in [`docs/architecture.md`](docs/architecture.md) and the project plan.

---

## Testing

```bash
# unit + service tests
pytest tests/

# UI critical-path tests
cd apps/web && npm test
```

Reproducibility is treated as a test case: the same config + seed must produce matching `MockVLA` output.

---

## Positioning

VLAScope is experiment infrastructure for evaluating vision-language-action agents on recorded driving scenarios — with asynchronous inference orchestration, reproducible run manifests, reasoning/action consistency checks, sensor perturbation testing, and failure analysis.

It is **not** a self-driving system, a replication of any commercial simulation product, or a safety-certified evaluation tool. Metrics are labeled as proxies where they are not physics-grounded or safety-certified.

---

## Acknowledgments

Architectural terminology is aligned with publicly described concepts from SimForge's public workflow and related published research, used only as design inspiration — no affiliation, access to private infrastructure, or proprietary data is implied. See `docs/references.md` for the full source list.
