from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RunStatus(str, Enum):
    CREATED = "CREATED"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    EVALUATING = "EVALUATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class FailureSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class FailureClass(str, Enum):
    MISSED_HAZARD = "MISSED_HAZARD"
    UNSAFE_BRAKING = "UNSAFE_BRAKING"
    STEERING_DRIFT = "STEERING_DRIFT"
    TTC_BREACH = "TTC_BREACH"
    REASONING_ACTION_CONTRADICTION = "REASONING_ACTION_CONTRADICTION"
    UNNECESSARY_INTERVENTION = "UNNECESSARY_INTERVENTION"
    EXCESSIVE_LATENCY = "EXCESSIVE_LATENCY"
    SENSOR_DROPOUT_SENSITIVITY = "SENSOR_DROPOUT_SENSITIVITY"
    HARDWARE_TIMING_JITTER = "HARDWARE_TIMING_JITTER"


# --- Ego, Hardware & Ground Truth ---

class EgoState(BaseModel):
    speed_mps: float = Field(0.0, description="Vehicle speed in meters per second")
    yaw_rate: Optional[float] = Field(0.0, description="Yaw rate in rad/s")
    acceleration_mps2: Optional[float] = Field(0.0, description="Longitudinal acceleration in m/s^2")
    imu: Optional[Dict[str, float]] = Field(default_factory=dict, description="Raw 6-DOF IMU accelerometer/gyro readings")


class Action(BaseModel):
    steering: float = Field(..., ge=-1.0, le=1.0, description="Steering command [-1.0, 1.0]")
    brake: float = Field(..., ge=0.0, le=1.0, description="Brake pressure [0.0, 1.0]")
    throttle: float = Field(0.0, ge=0.0, le=1.0, description="Throttle application [0.0, 1.0]")


class PredictedAction(Action):
    pass


class GroundTruth(BaseModel):
    action: Action
    hazards: List[str] = Field(default_factory=list, description="Active hazards at this timestamp")
    ttc_seconds: Optional[float] = Field(None, description="Time to collision proxy in seconds")
    safe_action_bounds: Optional[Dict[str, Any]] = None


# --- Scenarios & Observations ---

class ScenarioMetadata(BaseModel):
    scenario_id: str
    source: str = "local_dataset"  # "local_dataset", "hardware_esp32", "hardware_rpi", "carla"
    conditions: Dict[str, Any] = Field(default_factory=dict, description="e.g. weather, time_of_day, sensor_calibration")
    ego: Dict[str, Any] = Field(default_factory=dict, description="e.g. initial_speed_mps")
    hazards: List[str] = Field(default_factory=list)
    expected_response: str = "nominal"
    fps: int = 20
    description: Optional[str] = ""
    tags: List[str] = Field(default_factory=list)
    license: Optional[str] = "MIT"
    hardware_info: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Sensor rig hardware details (ESP32-CAM, Pi Camera, IMU)")


class ScenarioFrame(BaseModel):
    scenario_id: str
    frame_idx: int
    timestamp_ms: int
    hw_timestamp_ns: Optional[int] = Field(None, description="Hardware clock timestamp in nanoseconds for sync analysis")
    image_uri: str
    thumbnail_uri: Optional[str] = None
    ego: EgoState
    ground_truth: GroundTruth
    sensor_meta: Optional[Dict[str, Any]] = Field(default_factory=dict)


class Observation(BaseModel):
    scenario_id: str
    frame_idx: int
    timestamp_ms: int
    hw_timestamp_ns: Optional[int] = None
    image_uri: str
    image_data: Optional[bytes] = None
    thumbnail_uri: Optional[str] = None
    ego: EgoState
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class Scenario(BaseModel):
    id: str
    name: str
    tags: List[str] = Field(default_factory=list)
    metadata_version: str = "1.0.0"
    source_ref: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    total_frames: int = 0
    fps: int = 20
    metadata_payload: Optional[ScenarioMetadata] = None


# --- VLA Models & Outputs ---

class VLAOutput(BaseModel):
    model_id: str
    timestamp_ms: int
    reasoning: Optional[str] = Field(None, description="Natural language explanation of situation and plan")
    action: PredictedAction
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    latency_ms: float = Field(0.0, ge=0.0)
    extracted_hazards: List[str] = Field(default_factory=list)
    extra: Optional[Dict[str, Any]] = Field(default_factory=dict)


class AdapterHealth(BaseModel):
    adapter_id: str
    status: str  # "healthy", "degraded", "unloaded", "unhealthy"
    model_name: str
    device: str
    runtime_engine: str = "native"  # "native", "onnx", "llama_cpp", "api"
    latency_p50_ms: Optional[float] = None
    details: Optional[Dict[str, Any]] = Field(default_factory=dict)


# --- Experiments, Runs & Traces ---

class PerturbationConfig(BaseModel):
    type: str  # "gaussian_noise", "cmos_sensor_noise", "motion_blur", "exposure_change", "compression_artifact", "frame_drop", "latency_jitter", "rolling_shutter"
    intensity: float = Field(1.0, ge=0.0, le=10.0)
    params: Dict[str, Any] = Field(default_factory=dict)
    seed: Optional[int] = 42


class Experiment(BaseModel):
    id: str
    name: str
    scenario_ids: List[str]
    model_id: str
    eval_profile: str = "standard"
    frame_stride: int = Field(1, ge=1, le=10, description="Step stride: evaluate every Nth frame (useful for low-spec CPU runs and frame-skip robustness)")
    perturbation_profile: Optional[PerturbationConfig] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    description: Optional[str] = None


class Run(BaseModel):
    id: str
    experiment_id: str
    scenario_id: str
    model_id: str
    status: RunStatus = RunStatus.CREATED
    seed: int = 42
    frame_stride: int = 1
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    manifest_hash: Optional[str] = None
    share_token: Optional[str] = None
    progress: float = 0.0
    error_message: Optional[str] = None
    perturbation_config: Optional[PerturbationConfig] = None


class InferenceTrace(BaseModel):
    id: Optional[str] = None
    run_id: str
    frame_idx: int
    timestamp_ms: int
    hw_timestamp_ns: Optional[int] = None
    image_uri: str
    ego_speed_mps: float
    model_reasoning: Optional[str] = None
    predicted_action: PredictedAction
    ground_truth_action: Action
    hazards_present: List[str] = Field(default_factory=list)
    hazards_detected: List[str] = Field(default_factory=list)
    confidence: float = 1.0
    latency_ms: float = 0.0
    ttc_seconds: Optional[float] = None


class Metric(BaseModel):
    id: Optional[str] = None
    run_id: str
    metric_name: str
    metric_group: str  # "action", "temporal", "safety", "reasoning", "robustness", "hardware"
    value: float
    aggregation: str = "mean"
    version: str = "1.0.0"
    metadata_payload: Optional[Dict[str, Any]] = None


class FailureRecord(BaseModel):
    id: Optional[str] = None
    run_id: str
    frame_idx: int
    failure_class: FailureClass
    severity: FailureSeverity
    evidence: Dict[str, Any]
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    resolved: bool = False
    notes: Optional[str] = None


class RunManifest(BaseModel):
    run_id: str
    experiment_id: str
    timestamp: str
    code_version: str = "0.1.0"
    scenario_id: str
    scenario_version: str
    model_id: str
    model_version: str
    eval_profile: str
    frame_stride: int = 1
    perturbation_profile: Optional[Dict[str, Any]] = None
    seed: int
    config_hash: str
    share_token: Optional[str] = None
    metrics_summary: Dict[str, float] = Field(default_factory=dict)
    failures_summary: Dict[str, int] = Field(default_factory=dict)
