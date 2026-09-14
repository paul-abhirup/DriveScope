# DriveScope Architecture Specification

## 1. System Overview

DriveScope is an experiment and evaluation platform for physical-AI and Vision-Language-Action (VLA) agents. It provides a modular, reproducible evaluation environment for multimodal driving sequences without requiring heavy 3D simulation engines or local 7B+ GPU weights.

```
                         Next.js / TypeScript UI
                                   │
                          REST + WebSocket
                                   │
                         FastAPI Control Plane
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

## 2. Core Architectural Abstractions

### 2.1 Scenario Source Interface
```python
class ScenarioSource(Protocol):
    def get_metadata(self, scenario_id: str) -> ScenarioMetadata: ...
    def get_frames(self, scenario_id: str) -> Iterable[ScenarioFrame]: ...
    def get_ground_truth(self, scenario_id: str, frame_idx: int) -> GroundTruth: ...
```

### 2.2 VLA Adapter Interface
```python
class VLAAdapter(Protocol):
    @property
    def model_id(self) -> str: ...
    def load(self) -> None: ...
    def infer(self, observation: Observation) -> VLAOutput: ...
    def health(self) -> AdapterHealth: ...
```

## 3. Run State Machine

```
CREATED -> QUEUED -> RUNNING -> EVALUATING -> COMPLETED
                           |                 |
                           +-> FAILED <-----+
```

- Allowed terminal states: `COMPLETED`, `FAILED`, `CANCELLED`
- Every completed run generates an immutable `RunManifest` cryptographically binding the dataset version, code version, model adapter, seed, perturbation config, and metric outputs.

## 4. Evaluation Engine

The evaluation pipeline computes metrics across four core dimensions:
1. **Action Error**: MAE/RMSE for steering angle, brake pressure, and throttle, plus cumulative lateral drift.
2. **Temporal Behavior**: Mean latency, p95 latency, and hazard reaction delay.
3. **Safety Proxies**: Minimum Time-To-Collision (TTC), critical threshold breaches, missed hazard counts, and unnecessary abrupt interventions.
4. **Reasoning-Action Consistency**: Multi-factor scoring assessing whether the model's stated verbal reasoning corresponds to its actual actuator commands:
   $$\text{Consistency} = w_1 \cdot \text{HazardActionAgreement} + w_2 \cdot \text{TemporalAlignment} + w_3 \cdot \text{DirectionalAgreement} + w_4 \cdot \text{ConfidenceCalibration}$$
