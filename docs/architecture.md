# DriveScope Architecture & System Design

This document details the software architecture, protocol contracts, dataflow sequences, hardware integration specifications, and state machines powering **DriveScope**.

---

## 1. Architectural Principles

1. **Protocol Decoupling**: Scenario data providers (`ScenarioSource`) and models (`VLAAdapter`) sit behind runtime interfaces. The database schema, metrics engine, and UI never depend on which model or data source is active.
2. **Dual-Engine Execution**: Ultra-lightweight `MODE=minimal` (SQLite + in-process queue) for modest hardware and laptops, alongside `MODE=docker` (PostgreSQL + Redis + Celery + MinIO) for multi-node production runs.
3. **Reproducibility by Design**: Every experiment execution generates a SHA-256 configuration hash and an immutable `RunManifest` tracking code version, scenario hash, seed, and evaluation outputs.
4. **Physical Sensor Calibration**: Sensor perturbations model real CMOS sensor physics (Poisson shot noise + dark current read noise + rolling shutter skew) rather than arbitrary noise.

---

## 2. Layered Architecture Diagram

<p align="center">
  <img src="../CoreArchitechture.png" alt="DriveScope Core Architecture Diagram" width="100%" />
</p>

```mermaid
flowchart TD
    subgraph Presentation["Presentation Layer (Next.js 14 + Tailwind)"]
        UI_Dash["Dashboard & Global Analytics"]
        UI_Scen["Scenario Library & Scrubber"]
        UI_Exp["Experiment Builder"]
        UI_Rep["Replay Workbench & Telemetry Gauges"]
        UI_Comp["Run Comparison & Robustness Curves"]
        UI_Fail["Failure Intelligence Explorer"]
    end

    subgraph ControlPlane["FastAPI Control Plane"]
        API_Scen["Scenario Service"]
        API_Run["Run & Lifecycle Service"]
        API_Eval["Analysis & Metrics Service"]
        API_Auth["HMAC Signed Links & Auth"]
        API_WS["WebSocket Connection Manager"]
    end

    subgraph Persistence["Persistence & State Engine"]
        DB[("Relational Database (SQLite / PostgreSQL)")]
        BlobStore["Artifact Store (Local Disk / MinIO S3)"]
        MsgBroker[("Task Queue Broker (In-process Async / Redis)")]
    end

    subgraph Workers["Execution & Compute Workers"]
        W_Inf["Inference Dispatcher"]
        W_Eval["Evaluation & Robustness Engine"]
    end

    subgraph Adapters["Model Adapter Layer"]
        A_Mock["MockVLA (Deterministic Synthetic)"]
        A_Rule["RuleBaseline (Classical Heuristics)"]
        A_VLM["LocalQuantizedVLM (int4 GGUF / ONNX on CPU)"]
        A_Remote["RemoteVLA (Hosted Multimodal API)"]
    end

    subgraph Sources["Scenario Sources"]
        S_Data["DatasetScenarioSource (Prerecorded Sequences)"]
        S_HW["HardwareScenarioSource (ESP32-CAM / RPi)"]
        S_Sim["SimulatorScenarioSource (CARLA Bridge)"]
    end

    Presentation <--> ControlPlane
    ControlPlane <--> Persistence
    Persistence <--> Workers
    Workers --> Adapters
    Workers <--> Sources
    W_Eval --> API_Eval
```

---

## 3. End-to-End Evaluation Sequence

```mermaid
sequenceDiagram
    autonumber
    participant UI as Next.js Workbench
    participant API as FastAPI Control Plane
    participant Worker as Execution Engine
    participant Source as Scenario Source (Data / HW)
    participant Model as VLA Adapter
    participant Eval as Metric Engine
    participant DB as Relational Database

    UI->>API: POST /api/v1/experiments (Model, Scenarios, Perturbations, Stride)
    API->>DB: Persist Experiment & Queue Run
    API->>Worker: Dispatch execution (In-process or Celery task)
    Worker->>Source: Fetch Scenario Metadata & Frames Iterator

    loop Frame-by-Frame Execution Loop (with Frame Stride)
        Source->>Worker: Emit ScenarioFrame (Image, Hardware TS, Ego State, Ground Truth)
        Worker->>Worker: Apply Perturbation Engine (Calibrated CMOS noise, blur, jitter)
        Worker->>Model: infer(Observation)
        Model-->>Worker: VLAOutput (Reasoning, Predicted Action, Confidence, Latency)
        Worker->>DB: Persist InferenceTrace record
        Worker-->>API: WebSocket frame.processed event
        API-->>UI: Real-time progress bar update & telemetry
    end

    Worker->>Eval: evaluate_run(Traces, Profile)
    Eval->>Eval: Action MAE/RMSE & Lateral Drift
    Eval->>Eval: Temporal Latency & Reaction Delays
    Eval->>Eval: Safety Proxies (Min TTC, Missed Hazards)
    Eval->>Eval: Multi-factor Reasoning-Action Consistency
    Eval-->>Worker: Return Computed Metrics & FailureRecords
    Worker->>DB: Save Metrics & Failure records
    Worker->>DB: Calculate SHA-256 Manifest Hash & Status to COMPLETED
    Worker-->>API: WebSocket run.completed event
    API-->>UI: Replay workbench populated with metrics & telemetry
```

---

## 4. Reasoning-Action Consistency Engine

$$\text{Consistency} = 0.35 \cdot S_{\text{hazard}} + 0.25 \cdot S_{\text{temp}} + 0.25 \cdot S_{\text{dir}} + 0.15 \cdot S_{\text{conf}}$$

```mermaid
flowchart LR
    subgraph InputTokens["Model Output Head"]
        Text["Natural Language Rationale: Pedestrian crossing ahead, applying emergency brake"]
        Action["Action Commands: steering 0.0, brake 0.05, throttle 0.30"]
        Confidence["Reported Confidence: 0.95"]
    end

    subgraph Scorers["Scoring Dimensions"]
        HAA["Hazard-Action Agreement (w1 = 0.35)"]
        TA["Temporal Alignment (w2 = 0.25)"]
        DA["Directional Agreement (w3 = 0.25)"]
        CC["Confidence Calibration (w4 = 0.15)"]
    end

    subgraph Output["Consistency Decision"]
        Score["Composite Consistency Score"]
        Contradiction["Flag REASONING_ACTION_CONTRADICTION"]
    end

    Text --> HAA
    Action --> HAA
    Text --> TA
    Action --> TA
    Text --> DA
    Action --> DA
    Confidence --> CC
    Action --> CC

    HAA --> Score
    TA --> Score
    DA --> Score
    CC --> Score
    HAA -.-> Contradiction
```

---

## 5. Hardware Sensor Rig Architecture (ECE Core)

```mermaid
flowchart TD
    subgraph Microcontroller["ESP32-CAM / Raspberry Pi Hardware Rig"]
        Sensor["Camera Module (OV2640 / IMX219)"]
        IMU_HW["6-DOF IMU Sensor (MPU6050)"]
        Clock["Microsecond Hardware Timer"]
        PanTilt["2-Axis Pan-Tilt Servos"]
        HTTP_Serv["Firmware MJPEG Server (drivescope_rig.ino)"]
        
        Sensor --> HTTP_Serv
        IMU_HW --> HTTP_Serv
        Clock --> HTTP_Serv
        PanTilt <--> HTTP_Serv
    end

    subgraph Network["Wi-Fi / Ethernet Stream"]
        MJPEG["MJPEG Video Stream + X-Hardware-Timestamp-Us"]
        TelemetryStream["IMU Accelerometer/Gyro JSON Stream"]
        REST_Control["REST /control (Pan/Tilt Angles)"]
    end

    subgraph Ingestion["DriveScope Hardware Source"]
        HSS["HardwareScenarioSource (drivescope_vla_sdk)"]
        TimingSync["Hardware Lag Profiler (Capture -> Infer -> Action)"]
        NoiseCalib["Calibrated CMOS Sensor Noise Engine"]
    end

    HTTP_Serv --> MJPEG
    HTTP_Serv --> TelemetryStream
    REST_Control --> HTTP_Serv
    MJPEG --> HSS
    TelemetryStream --> HSS
    HSS --> TimingSync
    HSS --> NoiseCalib
```

---

## 6. Future Ecosystem & Roadmap Extensions

```mermaid
flowchart TD
    subgraph Foundation["DriveScope Core Platform"]
        Core_App["Control Plane & Replay Workbench"]
        Core_Eval["Multi-Factor Evaluation Engine"]
    end

    subgraph SimulationEcosystem["Simulation Track"]
        CARLA_Bridge["CARLA Closed-Loop Simulator Bridge"]
        Scenario_Fuzz["Failure-Driven Scenario Fuzzing & Mutation"]
    end

    subgraph HardwareEcosystem["Hardware & Edge Track"]
        Rig_Tracking["Active Pan-Tilt Subject Tracking via Servos"]
        Sensor_Fusion["Multi-Camera Stereo & Ultrasonic Array"]
    end

    subgraph AIEcosystem["AI Intelligence Track"]
        Quant_Native["Native GGUF/ONNX Quantized VLM Tokenizer"]
        Fail_Embeddings["Vector Embeddings & Semantic Failure Clustering"]
        Video_Renderer["Automated Annotated MP4 Video Exporter"]
    end

    Foundation --- SimulationEcosystem
    Foundation --- HardwareEcosystem
    Foundation --- AIEcosystem
```
