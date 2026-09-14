import math
import random
import time
from typing import Optional
from drivescope_schema.models import Observation, VLAOutput, PredictedAction, AdapterHealth
from .base import BaseVLAAdapter


class MockVLA(BaseVLAAdapter):
    """
    Deterministic synthetic VLA adapter for testing pipeline execution,
    reproducibility, and evaluation metrics without requiring heavy weights or GPUs.
    """

    def __init__(self, model_id: str = "mock-vla-v1", seed: int = 42, inject_anomaly: bool = False):
        super().__init__(model_id)
        self.seed = seed
        self.inject_anomaly = inject_anomaly
        self.rng = random.Random(seed)
        self._is_loaded = True

    def load(self) -> None:
        self.rng = random.Random(self.seed)
        self._is_loaded = True

    def infer(self, observation: Observation) -> VLAOutput:
        start_time = time.perf_counter()
        
        frame_idx = observation.frame_idx
        metadata = observation.metadata or {}
        scenario_hazards = metadata.get("hazards", [])
        
        # Deterministic pseudo-random variation based on frame_idx and seed
        frame_rng = random.Random(self.seed * 1000 + frame_idx)
        jitter = frame_rng.uniform(-0.02, 0.02)
        
        # Simulate smooth steering trajectory with sinusoidal drift
        steering = round(math.sin(frame_idx * 0.1) * 0.15 + jitter, 3)
        steering = max(-1.0, min(1.0, steering))

        # Check if scenario has hazards around this frame range
        is_hazard_active = len(scenario_hazards) > 0 and 10 <= frame_idx <= 40
        
        if is_hazard_active:
            detected_hazard = scenario_hazards[0]
            reasoning = f"Detected {detected_hazard} in path; initiating braking."
            
            if self.inject_anomaly and frame_idx == 25:
                # Anomaly: model reasons about hazard but gives weak brake / maintains throttle
                brake = 0.05
                throttle = 0.3
                reasoning = f"Pedestrian crossing road in front of ego vehicle, but road seems passable."
            else:
                brake = round(0.65 + frame_rng.uniform(0.0, 0.2), 2)
                throttle = 0.0
        else:
            detected_hazard = None
            reasoning = "Lane is clear. Maintaining speed within lane boundaries."
            brake = 0.0
            throttle = round(0.45 + jitter, 2)

        latency_ms = round((time.perf_counter() - start_time) * 1000.0 + frame_rng.uniform(15.0, 35.0), 2)

        return VLAOutput(
            model_id=self.model_id,
            timestamp_ms=observation.timestamp_ms,
            reasoning=reasoning,
            action=PredictedAction(
                steering=steering,
                brake=brake,
                throttle=throttle
            ),
            confidence=round(frame_rng.uniform(0.82, 0.98), 2),
            latency_ms=latency_ms,
            extracted_hazards=[detected_hazard] if detected_hazard else [],
            extra={"seed": self.seed, "frame_idx": frame_idx}
        )

    def health(self) -> AdapterHealth:
        return AdapterHealth(
            adapter_id=self.model_id,
            status="healthy",
            model_name="Mock VLA Generator",
            device="cpu",
            latency_p50_ms=22.5,
            details={"seed": self.seed, "deterministic": True}
        )
