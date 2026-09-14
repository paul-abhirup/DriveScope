import pytest
from drivescope_schema.models import (
    Action,
    Observation,
    VLAOutput,
    PredictedAction,
    EgoState,
    GroundTruth,
    ScenarioMetadata,
    RunStatus,
    FailureClass,
)


def test_action_validation():
    act = Action(steering=0.5, brake=0.2, throttle=0.8)
    assert act.steering == 0.5
    assert act.brake == 0.2
    assert act.throttle == 0.8

    with pytest.raises(Exception):
        # Steering out of range [-1, 1]
        Action(steering=2.5, brake=0.0, throttle=0.0)


def test_vla_output():
    out = VLAOutput(
        model_id="mock-vla-v1",
        timestamp_ms=1000,
        reasoning="Slowing down due to traffic",
        action=PredictedAction(steering=0.0, brake=0.5, throttle=0.0),
        confidence=0.95,
        latency_ms=25.0
    )
    assert out.model_id == "mock-vla-v1"
    assert out.action.brake == 0.5
    assert out.confidence == 0.95
