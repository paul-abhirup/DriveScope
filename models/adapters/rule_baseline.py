import time
from typing import Optional
from drivescope_schema.models import Observation, VLAOutput, PredictedAction, AdapterHealth
from .base import BaseVLAAdapter


class RuleBaselineAdapter(BaseVLAAdapter):
    """
    Interpretable rule-based driving baseline adapter.
    Uses classical control and rule heuristics based on ego state and scene cues.
    """

    def __init__(self, model_id: str = "rule-baseline-v1", target_speed_mps: float = 12.0):
        super().__init__(model_id)
        self.target_speed_mps = target_speed_mps
        self._is_loaded = True

    def load(self) -> None:
        self._is_loaded = True

    def infer(self, observation: Observation) -> VLAOutput:
        start_time = time.perf_counter()
        
        current_speed = observation.ego.speed_mps
        metadata = observation.metadata or {}
        hazards = metadata.get("hazards", [])
        
        # Rule 1: Hazard safety brake
        if hazards:
            hazard_name = hazards[0]
            brake = min(1.0, max(0.5, current_speed / 10.0))
            throttle = 0.0
            steering = 0.0
            reasoning = f"RULE_TRIGGER: Active hazard '{hazard_name}' detected. Applying emergency braking ({brake:.2f})."
            extracted_hazards = [hazard_name]
        # Rule 2: Speed regulation
        elif current_speed < self.target_speed_mps:
            throttle = min(1.0, (self.target_speed_mps - current_speed) / 5.0)
            brake = 0.0
            steering = 0.0
            reasoning = f"RULE_TRIGGER: Speed ({current_speed:.1f} m/s) below target ({self.target_speed_mps} m/s). Accelerating."
            extracted_hazards = []
        elif current_speed > self.target_speed_mps + 2.0:
            throttle = 0.0
            brake = 0.2
            steering = 0.0
            reasoning = f"RULE_TRIGGER: Speed ({current_speed:.1f} m/s) exceeds target ({self.target_speed_mps} m/s). Coasting/soft brake."
            extracted_hazards = []
        else:
            throttle = 0.2
            brake = 0.0
            steering = 0.0
            reasoning = "RULE_TRIGGER: Speed nominal. Maintaining lane position."
            extracted_hazards = []

        latency_ms = round((time.perf_counter() - start_time) * 1000.0 + 5.0, 2)

        return VLAOutput(
            model_id=self.model_id,
            timestamp_ms=observation.timestamp_ms,
            reasoning=reasoning,
            action=PredictedAction(
                steering=steering,
                brake=round(brake, 2),
                throttle=round(throttle, 2)
            ),
            confidence=0.99,
            latency_ms=latency_ms,
            extracted_hazards=extracted_hazards
        )

    def health(self) -> AdapterHealth:
        return AdapterHealth(
            adapter_id=self.model_id,
            status="healthy",
            model_name="Heuristic Rule Baseline",
            device="cpu",
            latency_p50_ms=5.0,
            details={"target_speed_mps": self.target_speed_mps}
        )
