# **DriveScope | Project Engineering Specification**

### **Experiment Infrastructure for Vision-Language-Action (VLA) Model Evaluation**

Detailed project plan • CPU/laptop-first • Portable Edge & Hardware Rig integration • Extensible to Simulators and Foundation Robotics Models

---

##### **Project Thesis**
Build the open-source software and physical experiment layer that orchestrates multimodal driving sequences, VLA inference, experiment lifecycle, multi-factor reasoning/action consistency evaluation, calibrated sensor perturbations, and failure analysis — without requiring heavy 3D simulation dependencies or local GPU clusters.

| **Specification** | **Details** |
|---|---|
| **Document** | DriveScope Engineering Specification & Roadmap |
| **Target Developer Profile** | ECE + Systems + Full-Stack Software + AI Research |
| **Compute Floor** | Laptop / CPU first (8 GB RAM minimum, 0 GPU required) |
| **Hardware Rig Target** | ESP32-CAM / Raspberry Pi Camera module + IMU sensor rig |
| **Status** | Active Baseline Specification (September 2026) |

---

## **0. Document Map**

| **Section** | **Core Questions Answered** |
|---|---|
| **1. Project Definition** | What DriveScope is, why it exists, and primary outcomes |
| **2. Architectural Scope & Non-Goals** | What is built in MVP vs deliberately deferred |
| **3. Functional & Non-Functional Requirements** | Scenario registry, trace persistence, determinism, reproducibility |
| **4. System Architecture & Boundaries** | Services, protocols, execution modes (`minimal` vs `docker`) |
| **5. Data Model & Contracts** | Observations, VLAOutput, Traces, Metrics, Perturbations, Manifests |
| **6. VLA Adapters & Quantized CPU Path** | MockVLA, RuleBaseline, Quantized Small VLM (GGUF/ONNX), Remote API |
| **7. Multi-Dimensional Evaluation Engine** | Action error, latency distribution, safety proxies, reasoning consistency |
| **8. Sensor Perturbation & Robustness** | CMOS sensor noise, rolling shutter, blur, exposure, frame-drop, jitter |
| **9. Hardware & Sensor Rig Integration (ECE Core)** | `HardwareScenarioSource`, ESP32-CAM, hardware timestamps, IMU synchronization |
| **10. Frontend Workbench & UX Design** | Dashboard, Replay Workbench, Compare Diff, Failure Explorer |
| **11. Full-Stack & Engineering Discipline** | CI/CD pipelines, typed client generation, signed shareable links, auth |
| **12. Implementation Roadmap & Milestones** | Phases 0 through 9 with vertical execution gates |
| **13. Testing, Quality & Reproducibility Gates** | Test pyramid, determinism verification, data integrity |

---

## **1. Project Definition**

DriveScope is a reproducible experiment and evaluation platform for Vision-Language-Action (VLA) agents. It provides the experimentation and evaluation layer sitting around scenario sequences, camera observations, model inference heads, experiment runs, metrics, sensor perturbations, and failure analysis.

### **1.1 Core Engineering Question**
> **Can a lightweight, reproducible software and hardware layer make VLA behavior measurable across scenarios, temporal conditions, physical sensor noise, and sensor perturbations — and make semantic and behavioral failures easy to inspect and reproduce?**

### **1.2 Primary Outcomes**
- **Orchestrate Scenario Sequences**: Step through prerecorded datasets or live hardware streams through versioned VLA adapters.
- **Trace Full Decisions**: Capture observation images, predicted actions, reasoning explanations, timestamps, and ground-truth targets in a strict schema.
- **Score Reasoning-Action Consistency**: Detect semantic dissociation where model explanations contradict low-level actuator commands.
- **Quantify Robustness Curves**: Measure degradation across calibrated CMOS noise, rolling shutter, exposure flicker, and frame-drops.
- **Physical Sensor Rig**: Stream live camera and IMU telemetry from an ESP32-CAM / Raspberry Pi rig with hardware microsecond timestamps.
- **Zero-GPU Baseline**: Run the full stack on standard laptop CPUs via `MODE=minimal` and quantized small VLMs.

---

## **2. Architectural Scope & Non-Goals**

### **2.1 In Scope**
- Local dataset sequence source (`DatasetScenarioSource`) and physical sensor rig (`HardwareScenarioSource`).
- Pluggable VLA adapters: `MockVLA`, `RuleBaselineAdapter`, `LocalQuantizedVLM` (int4 GGUF / ONNX), `RemoteVLAAdapter`.
- Multi-factor evaluation: Action MAE/RMSE, temporal latency, proxy safety metrics (TTC, missed hazards), composite reasoning-action consistency.
- Two runtime modes: `MODE=minimal` (SQLite + in-process async queue) and `MODE=docker` (PostgreSQL + Redis + Celery).
- Next.js 14 Replay Workbench with synchronized frame playback, action gauges, and metric comparisons.
- Failure intelligence: taxonomy tagging, filtering, and representative case clustering.
- Hardware sensor synchronization: hardware capture timestamp vs model inference vs actuation delay tracking.

### **2.2 Explicit Non-Goals**
- Rebuilding a custom 3D graphics simulator from scratch.
- Requiring a local 7B+ parameter unquantized model as an MVP dependency.
- Claiming certified real-world road safety validation.

---

## **3. System Architecture & Execution Modes**

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
        └── SimulatorScenarioSource (Future CARLA / Unreal bridge)
```

### **3.1 Execution Modes**
1. **`MODE=minimal` (Ultra-portable / Laptop)**:
   - Database: SQLite with thread-safe pooling.
   - Job Dispatch: In-process asynchronous task queue.
   - Model Path: `MockVLA`, `RuleBaseline`, or Quantized CPU VLM (`LocalQuantizedVLM`).
   - Memory footprint: ~250 MB total RAM.
2. **`MODE=docker` (Production / Multi-worker)**:
   - Database: PostgreSQL with relational indexes.
   - Job Dispatch: Celery workers backed by Redis broker.
   - Storage: Local filesystem or MinIO S3-compatible store.

---

## **4. Data Model & Contracts**

### **4.1 Core Protocols**
```python
class ScenarioSource(Protocol):
    def get_metadata(self, scenario_id: str) -> ScenarioMetadata: ...
    def get_frames(self, scenario_id: str) -> Iterable[ScenarioFrame]: ...
    def get_ground_truth(self, scenario_id: str, frame_idx: int) -> GroundTruth: ...

class VLAAdapter(Protocol):
    @property
    def model_id(self) -> str: ...
    def load(self) -> None: ...
    def infer(self, observation: Observation) -> VLAOutput: ...
    def health(self) -> AdapterHealth: ...
```

### **4.2 Observation & Output Schema**
```json
{
  "scenario_id": "pedestrian_crossing_001",
  "frame_idx": 18,
  "timestamp_ms": 900,
  "hw_timestamp_ns": 1726329482103948,
  "image_uri": "seq://crossing_001/frame_0018.jpg",
  "ego": {
    "speed_mps": 9.5,
    "imu": {"accel_x": 0.05, "accel_y": -0.12, "accel_z": 9.80}
  },
  "ground_truth": {
    "action": {"steering": 0.0, "brake": 0.75, "throttle": 0.0},
    "hazards": ["pedestrian"],
    "ttc_seconds": 1.2
  }
}
```

```json
{
  "model_id": "local-small-vlm-q4",
  "timestamp_ms": 900,
  "reasoning": "Pedestrian crossing ahead from right kerb. Applying brake.",
  "action": {"steering": 0.0, "brake": 0.65, "throttle": 0.0},
  "confidence": 0.91,
  "latency_ms": 68.4,
  "extracted_hazards": ["pedestrian"]
}
```

---

## **5. Reasoning-Action Consistency & Evaluation**

DriveScope evaluates semantic alignment between verbal explanations and actuator head commands:

$$\text{Consistency} = 0.35 \cdot S_{\text{hazard}} + 0.25 \cdot S_{\text{temp}} + 0.25 \cdot S_{\text{dir}} + 0.15 \cdot S_{\text{conf}}$$

- **$S_{\text{hazard}}$ (Hazard-Action Agreement)**: Verifies if verbal hazard identification induces braking ($\text{brake} \ge 0.30$).
- **$S_{\text{dir}}$ (Directional Agreement)**: Verifies if lateral intent ("turn left", "steer right") matches steering sign and angle.
- **$S_{\text{temp}}$ (Temporal Alignment)**: Measures latency between hazard realization and action onset.
- **$S_{\text{conf}}$ (Confidence Calibration)**: Flags high confidence predictions that exhibit severe error or miss hazards.

---

## **6. Sensor Perturbations & Calibrated Physical Noise**

DriveScope models both synthetic and calibrated CMOS physical noise:
- **`cmos_sensor_noise`**: Poisson photon shot noise combined with Gaussian dark current read noise derived from physical camera sensors (OV2640 / IMX219).
- **`rolling_shutter`**: Progressive scanline horizontal skew across frames.
- **`motion_blur`**: Directional spatial smear from platform vibration.
- **`exposure_change`**: Glare underexposure / overexposure.
- **`frame_drop`**: Sensor communication dropout simulation.
- **`latency_jitter`**: Microcontroller clock drift and network jitter.

---

## **7. Hardware Sensor Rig Integration (ECE Track)**

### **7.1 Architecture**
An ESP32-CAM or Raspberry Pi camera module mounted on a 2-axis Pan-Tilt servo streaming live observations into `HardwareScenarioSource`:
- **Microsecond Hardware Timestamps**: Embedded in frame headers to calculate true capture $\rightarrow$ inference $\rightarrow$ action lag.
- **IMU Telemetry**: 6-DOF acceleration and angular rates synchronized per frame.
- **Dynamic Observation Adjustments**: Pan-tilt servo positioning via REST/WebSocket control.

---

## **8. Roadmap & Phased Delivery**

| **Phase** | **Theme** | **Key Deliverables** | **Exit Gate** |
|---|---|---|---|
| **Phase 0** | Foundation | Monorepo layout, schemas, database models, Docker Compose | Runnable stack + passing tests |
| **Phase 1** | Scenario System | Scenario registry, ingestion, metadata validation, frame browser | Browse and inspect scenarios |
| **Phase 2** | Run Engine | State machine, minimal runner, Celery tasks, WebSocket feed | Deterministic MockVLA runs |
| **Phase 3** | VLA Adapters | `MockVLA`, `RuleBaseline`, `LocalQuantizedVLM` (GGUF/ONNX) | Per-frame inference trace |
| **Phase 4** | Evaluation Engine | Action error, temporal metrics, safety proxies, consistency | Reproducible metrics per run |
| **Phase 5** | Replay Workbench | Synchronized frame player, reasoning cards, action gauges | Human failure diagnosis |
| **Phase 6** | Robustness Suite | Calibrated CMOS noise, rolling shutter, degradation curves | Quantified robustness plots |
| **Phase 7** | Failure Intelligence | Taxonomy classification, clustering, filter queries | Failure explorer end-to-end |
| **Phase 8** | CI/CD & Client Tooling | GitHub Actions, typed client generator, signed share links | Green CI + automated types |
| **Phase 9** | Hardware Sensor Rig | `HardwareScenarioSource`, ESP32-CAM firmware, hardware sync | Live physical stream eval |
