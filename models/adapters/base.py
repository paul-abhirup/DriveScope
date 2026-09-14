from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from drivescope_schema.models import Observation, VLAOutput, AdapterHealth


class BaseVLAAdapter(ABC):
    """Base class providing common utilities for VLA adapters."""

    def __init__(self, model_id: str):
        self._model_id = model_id
        self._is_loaded = False

    @property
    def model_id(self) -> str:
        return self._model_id

    @abstractmethod
    def load(self) -> None:
        """Load model weights or establish remote connections."""
        pass

    @abstractmethod
    def infer(self, observation: Observation) -> VLAOutput:
        """Perform inference on observation and return structured VLAOutput."""
        pass

    def health(self) -> AdapterHealth:
        """Default health probe."""
        return AdapterHealth(
            adapter_id=self.model_id,
            status="healthy" if self._is_loaded else "unloaded",
            model_name=self.model_id,
            device="cpu",
            latency_p50_ms=25.0,
            details={"loaded": self._is_loaded}
        )
