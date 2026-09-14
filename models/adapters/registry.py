from typing import Dict, List, Type
from drivescope_schema.models import AdapterHealth
from .base import BaseVLAAdapter
from .mock import MockVLA
from .rule_baseline import RuleBaselineAdapter
from .remote import RemoteVLAAdapter
from .local_small_vlm import LocalQuantizedVLM


ADAPTER_REGISTRY: Dict[str, Type[BaseVLAAdapter]] = {
    "mock-vla-v1": MockVLA,
    "rule-baseline-v1": RuleBaselineAdapter,
    "local-small-vlm-q4": LocalQuantizedVLM,
    "remote-vla-api": RemoteVLAAdapter,
}


def get_adapter(model_id: str, **kwargs) -> BaseVLAAdapter:
    """Factory function to instantiate adapter by ID."""
    if model_id not in ADAPTER_REGISTRY:
        raise ValueError(f"Unknown model adapter '{model_id}'. Available: {list(ADAPTER_REGISTRY.keys())}")
    return ADAPTER_REGISTRY[model_id](model_id=model_id, **kwargs)


def list_available_adapters() -> List[AdapterHealth]:
    """List all registered adapters and their health statuses."""
    result = []
    for model_id, cls in ADAPTER_REGISTRY.items():
        try:
            instance = cls(model_id=model_id)
            result.append(instance.health())
        except Exception as e:
            result.append(AdapterHealth(
                adapter_id=model_id,
                status="unhealthy",
                model_name=model_id,
                device="unknown",
                details={"error": str(e)}
            ))
    return result
