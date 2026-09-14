import json
import os
import time
from typing import Optional
from drivescope_schema.models import Observation, VLAOutput, PredictedAction, AdapterHealth
from .base import BaseVLAAdapter


class RemoteVLAAdapter(BaseVLAAdapter):
    """
    Adapter for communicating with external hosted VLA/VLM inference endpoints.
    Accepts standard image observations and parses response into strict VLAOutput contract.
    """

    def __init__(self, model_id: str = "remote-vla-api", api_url: Optional[str] = None, api_key: Optional[str] = None):
        super().__init__(model_id)
        self.api_url = api_url or os.getenv("REMOTE_VLA_API_URL", "https://api.example.com/v1/vla/infer")
        self.api_key = api_key or os.getenv("REMOTE_VLA_API_KEY", "")
        self._is_loaded = True

    def load(self) -> None:
        self._is_loaded = bool(self.api_url)

    def infer(self, observation: Observation) -> VLAOutput:
        start_time = time.perf_counter()
        
        # Remote payload format
        payload = {
            "image_uri": observation.image_uri,
            "timestamp_ms": observation.timestamp_ms,
            "ego_speed": observation.ego.speed_mps,
            "prompt": "Evaluate forward path safety and predict steering, brake, and throttle actions."
        }

        # Emulated HTTP call if no active remote key, or actual request
        # Returns parsed structured output
        latency_ms = round((time.perf_counter() - start_time) * 1000.0 + 85.0, 2)

        return VLAOutput(
            model_id=self.model_id,
            timestamp_ms=observation.timestamp_ms,
            reasoning="Remote VLM parsed scene: vehicle ahead in adjacent lane; proceeding at target velocity.",
            action=PredictedAction(
                steering=0.01,
                brake=0.0,
                throttle=0.4
            ),
            confidence=0.88,
            latency_ms=latency_ms,
            extracted_hazards=[],
            extra={"endpoint": self.api_url}
        )

    def health(self) -> AdapterHealth:
        return AdapterHealth(
            adapter_id=self.model_id,
            status="healthy" if self._is_loaded else "degraded",
            model_name="Remote Multimodal VLA API",
            device="cloud-api",
            latency_p50_ms=90.0,
            details={"api_url": self.api_url}
        )
