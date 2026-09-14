from models.adapters.mock import MockVLA
from drivescope_schema.models import Observation, EgoState


def test_reproducibility_identical_seeds():
    """Verify that same configuration + seed produces byte-exact predictions."""
    seed = 9999
    model_a = MockVLA(seed=seed)
    model_b = MockVLA(seed=seed)

    for idx in range(20):
        obs = Observation(
            scenario_id="pedestrian_crossing_001",
            frame_idx=idx,
            timestamp_ms=idx * 50,
            image_uri=f"mock://frame_{idx}.jpg",
            ego=EgoState(speed_mps=12.0),
            metadata={"hazards": ["pedestrian"]}
        )

        out_a = model_a.infer(obs)
        out_b = model_b.infer(obs)

        assert out_a.action.steering == out_b.action.steering
        assert out_a.action.brake == out_b.action.brake
        assert out_a.action.throttle == out_b.action.throttle
        assert out_a.reasoning == out_b.reasoning
