from drivescope_schema.models import (
    InferenceTrace,
    PredictedAction,
    Action,
    FailureClass,
)
from evaluation.action import compute_action_metrics
from evaluation.temporal import compute_temporal_metrics
from evaluation.safety import compute_safety_metrics_and_failures
from evaluation.reasoning import compute_reasoning_action_consistency


def test_action_metrics_calculation():
    traces = [
        InferenceTrace(
            run_id="run_1",
            frame_idx=0,
            timestamp_ms=0,
            image_uri="mock://0.jpg",
            ego_speed_mps=10.0,
            predicted_action=PredictedAction(steering=0.1, brake=0.0, throttle=0.5),
            ground_truth_action=Action(steering=0.0, brake=0.0, throttle=0.5),
        ),
        InferenceTrace(
            run_id="run_1",
            frame_idx=1,
            timestamp_ms=50,
            image_uri="mock://1.jpg",
            ego_speed_mps=10.0,
            predicted_action=PredictedAction(steering=-0.1, brake=0.0, throttle=0.5),
            ground_truth_action=Action(steering=0.0, brake=0.0, throttle=0.5),
        )
    ]

    metrics = compute_action_metrics(traces, "run_1")
    metric_map = {m.metric_name: m.value for m in metrics}

    assert "action_steering_mae" in metric_map
    assert metric_map["action_steering_mae"] == 0.1


def test_reasoning_contradiction_detection():
    # Model states pedestrian crossing but commands zero brake
    traces = [
        InferenceTrace(
            run_id="run_1",
            frame_idx=10,
            timestamp_ms=500,
            image_uri="mock://10.jpg",
            ego_speed_mps=10.0,
            model_reasoning="Pedestrian entering roadway; immediate stop needed.",
            predicted_action=PredictedAction(steering=0.0, brake=0.0, throttle=0.6),
            ground_truth_action=Action(steering=0.0, brake=0.8, throttle=0.0),
            hazards_present=["pedestrian"]
        )
    ]

    metrics, failures = compute_reasoning_action_consistency(traces, "run_1")
    assert len(failures) > 0
    assert failures[0].failure_class == FailureClass.REASONING_ACTION_CONTRADICTION
