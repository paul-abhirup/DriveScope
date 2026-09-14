from models.adapters.mock import MockVLA
from models.adapters.rule_baseline import RuleBaselineAdapter
from models.adapters.registry import get_adapter, list_available_adapters
from drivescope_schema.models import Observation, EgoState


def test_mock_vla_determinism():
    obs = Observation(
        scenario_id="test_01",
        frame_idx=15,
        timestamp_ms=750,
        image_uri="mock://frame.jpg",
        ego=EgoState(speed_mps=10.0),
        metadata={"hazards": ["pedestrian"]}
    )

    adapter1 = MockVLA(seed=123)
    adapter2 = MockVLA(seed=123)

    out1 = adapter1.infer(obs)
    out2 = adapter2.infer(obs)

    assert out1.action.steering == out2.action.steering
    assert out1.action.brake == out2.action.brake
    assert out1.reasoning == out2.reasoning


def test_rule_baseline_hazard_response():
    obs = Observation(
        scenario_id="test_01",
        frame_idx=15,
        timestamp_ms=750,
        image_uri="mock://frame.jpg",
        ego=EgoState(speed_mps=10.0),
        metadata={"hazards": ["pedestrian"]}
    )

    adapter = RuleBaselineAdapter()
    out = adapter.infer(obs)

    assert out.action.brake >= 0.5
    assert "RULE_TRIGGER" in (out.reasoning or "")


def test_adapter_registry():
    adapters = list_available_adapters()
    assert len(adapters) >= 2
    mock = get_adapter("mock-vla-v1")
    assert mock.model_id == "mock-vla-v1"
