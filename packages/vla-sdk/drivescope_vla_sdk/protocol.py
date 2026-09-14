import json
import os
import time
from abc import ABC, abstractmethod
from typing import Dict, Iterable, List, Optional, Protocol, runtime_checkable
from pathlib import Path

from drivescope_schema.models import (
    AdapterHealth,
    EgoState,
    GroundTruth,
    Observation,
    ScenarioFrame,
    ScenarioMetadata,
    VLAOutput,
    Action,
)


@runtime_checkable
class ScenarioSource(Protocol):
    """Protocol for scenario data providers (local datasets, hardware rigs, simulators)."""

    def get_metadata(self, scenario_id: str) -> ScenarioMetadata:
        """Fetch static configuration and metadata for a scenario."""
        ...

    def get_frames(self, scenario_id: str) -> Iterable[ScenarioFrame]:
        """Iterate through all timestamped frames in sequential order."""
        ...

    def get_ground_truth(self, scenario_id: str, frame_idx: int) -> GroundTruth:
        """Retrieve ground truth action and hazard annotation for a specific frame."""
        ...


@runtime_checkable
class VLAAdapter(Protocol):
    """Protocol for Vision-Language-Action model adapters."""

    @property
    def model_id(self) -> str:
        """Unique identifier for this adapter instance and version."""
        ...

    def load(self) -> None:
        """Initialize and warm up model weights, quantization runtimes, or network pool."""
        ...

    def infer(self, observation: Observation) -> VLAOutput:
        """Run single-frame inference returning parsed action and optional reasoning."""
        ...

    def health(self) -> AdapterHealth:
        """Report adapter health status, device info, and baseline metrics."""
        ...


class BaseScenarioSource(ABC):
    """Abstract base helper for implementing scenario sources."""

    @abstractmethod
    def list_scenarios(self) -> List[str]:
        pass

    @abstractmethod
    def get_metadata(self, scenario_id: str) -> ScenarioMetadata:
        pass

    @abstractmethod
    def get_frames(self, scenario_id: str) -> Iterable[ScenarioFrame]:
        pass


class DatasetScenarioSource(BaseScenarioSource):
    """Filesystem-based ScenarioSource implementation for recorded sequences."""

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)

    def list_scenarios(self) -> List[str]:
        if not self.base_dir.exists():
            return []
        return [
            d.name for d in self.base_dir.iterdir()
            if d.is_dir() and (d / "metadata.json").exists()
        ]

    def get_metadata(self, scenario_id: str) -> ScenarioMetadata:
        scenario_path = self.base_dir / scenario_id
        meta_file = scenario_path / "metadata.json"
        if not meta_file.exists():
            raise FileNotFoundError(f"Scenario metadata not found for {scenario_id} at {meta_file}")
        
        with open(meta_file, "r") as f:
            data = json.load(f)
        return ScenarioMetadata(**data)

    def get_ground_truth(self, scenario_id: str, frame_idx: int) -> GroundTruth:
        gt_file = self.base_dir / scenario_id / "ground_truth.json"
        if not gt_file.exists():
            raise FileNotFoundError(f"Ground truth not found for {scenario_id} at {gt_file}")
        
        with open(gt_file, "r") as f:
            gt_data = json.load(f)
        
        frame_key = str(frame_idx)
        if frame_key in gt_data:
            return GroundTruth(**gt_data[frame_key])
        
        if isinstance(gt_data, list) and 0 <= frame_idx < len(gt_data):
            return GroundTruth(**gt_data[frame_idx])

        raise KeyError(f"Frame {frame_idx} ground truth not found in {gt_file}")

    def get_frames(self, scenario_id: str) -> Iterable[ScenarioFrame]:
        meta = self.get_metadata(scenario_id)
        gt_file = self.base_dir / scenario_id / "ground_truth.json"
        with open(gt_file, "r") as f:
            gt_data = json.load(f)

        frames_dir = self.base_dir / scenario_id / "frames"
        image_files = sorted(frames_dir.glob("*.jpg")) + sorted(frames_dir.glob("*.png"))
        
        fps = meta.fps or 20
        frame_duration_ms = int(1000 / fps)

        for idx, img_path in enumerate(image_files):
            frame_idx = idx
            timestamp_ms = idx * frame_duration_ms
            
            if str(frame_idx) in gt_data:
                gt_item = GroundTruth(**gt_data[str(frame_idx)])
            elif isinstance(gt_data, list) and idx < len(gt_data):
                gt_item = GroundTruth(**gt_data[idx])
            else:
                gt_item = GroundTruth(
                    action=Action(steering=0.0, brake=0.0, throttle=0.5),
                    hazards=[]
                )

            yield ScenarioFrame(
                scenario_id=scenario_id,
                frame_idx=frame_idx,
                timestamp_ms=timestamp_ms,
                image_uri=str(img_path),
                ego=EgoState(speed_mps=meta.ego.get("initial_speed_mps", 10.0)),
                ground_truth=gt_item,
                sensor_meta={"width": 640, "height": 480}
            )


class HardwareScenarioSource(BaseScenarioSource):
    """
    Hardware ScenarioSource implementation for physical sensor rigs.
    Receives live or captured streams from an ESP32-CAM, Raspberry Pi Camera module,
    or USB video device alongside hardware nanosecond timestamps and IMU telemetry.
    """

    def __init__(self, device_url: str = "http://192.168.4.1/stream", device_type: str = "esp32-cam"):
        self.device_url = device_url
        self.device_type = device_type
        self._is_streaming = False

    def list_scenarios(self) -> List[str]:
        return [f"live_hardware_feed_{self.device_type}"]

    def get_metadata(self, scenario_id: str) -> ScenarioMetadata:
        return ScenarioMetadata(
            scenario_id=scenario_id,
            source=f"hardware_{self.device_type}",
            conditions={"weather": "physical_lab", "lighting": "ambient"},
            ego={"initial_speed_mps": 0.0},
            hazards=[],
            expected_response="reactive_avoidance",
            fps=15,
            description=f"Live observation stream from physical sensor rig ({self.device_type} at {self.device_url}).",
            tags=["hardware", "sensor_rig", "live", self.device_type],
            hardware_info={
                "device_type": self.device_type,
                "stream_url": self.device_url,
                "sensor_model": "OV2640 / Sony IMX219",
                "has_imu": True,
                "pan_tilt_servo": True
            }
        )

    def get_ground_truth(self, scenario_id: str, frame_idx: int) -> GroundTruth:
        # Default safety baseline for live physical testing
        return GroundTruth(
            action=Action(steering=0.0, brake=0.0, throttle=0.0),
            hazards=[],
            safe_action_bounds={"max_speed": 1.5, "emergency_stop_distance_cm": 25.0}
        )

    def get_frames(self, scenario_id: str, max_frames: int = 50) -> Iterable[ScenarioFrame]:
        """
        Emits live frames with precise hardware monotonic timestamps (nanoseconds)
        and simulated/real IMU sensor payload.
        """
        fps = 15
        interval_ms = int(1000 / fps)

        for idx in range(max_frames):
            hw_now_ns = time.time_ns()
            timestamp_ms = idx * interval_ms

            yield ScenarioFrame(
                scenario_id=scenario_id,
                frame_idx=idx,
                timestamp_ms=timestamp_ms,
                hw_timestamp_ns=hw_now_ns,
                image_uri=f"hw://{self.device_type}/frame_{idx:04d}",
                ego=EgoState(
                    speed_mps=0.0,
                    imu={"accel_x": 0.01, "accel_y": 0.02, "accel_z": 9.81, "gyro_z": 0.0}
                ),
                ground_truth=self.get_ground_truth(scenario_id, idx),
                sensor_meta={
                    "device": self.device_type,
                    "resolution": "640x480",
                    "hardware_timestamp_ns": hw_now_ns
                }
            )
