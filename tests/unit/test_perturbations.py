from PIL import Image
from evaluation.perturbation import PerturbationEngine
from drivescope_schema.models import PerturbationConfig, Observation, EgoState


def test_image_perturbation():
    img = Image.new("RGB", (100, 100), color=(128, 128, 128))
    config = PerturbationConfig(type="gaussian_noise", intensity=2.0)
    
    noisy_img = PerturbationEngine.perturb_image(img, config)
    assert noisy_img.size == (100, 100)


def test_observation_temporal_perturbation():
    obs = Observation(
        scenario_id="sc_01",
        frame_idx=10,
        timestamp_ms=500,
        image_uri="mock://test.jpg",
        ego=EgoState(speed_mps=10.0)
    )
    config = PerturbationConfig(type="latency_jitter", intensity=1.5)

    perturbed_obs = PerturbationEngine.apply_to_observation(obs, config)
    assert perturbed_obs.timestamp_ms >= 500
    assert "injected_delay_ms" in (perturbed_obs.metadata or {})
