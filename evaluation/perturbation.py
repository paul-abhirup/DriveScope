import io
import math
import random
from typing import Optional
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np

from drivescope_schema.models import Observation, PerturbationConfig


class PerturbationEngine:
    """
    Applies controlled image, sensor-calibrated, and temporal perturbations to evaluate VLA robustness.
    Supported types:
    - 'gaussian_noise': Generic Gaussian sensor noise
    - 'cmos_sensor_noise': Calibrated CMOS physical noise (photon shot noise + dark current)
    - 'rolling_shutter': Horizontal scanline skew from moving sensor
    - 'motion_blur': Motion smear / camera shake
    - 'exposure_change': Glare or low-light underexposure
    - 'compression_artifact': High JPEG compression artifacts
    - 'frame_drop': Emulate sensor frame dropout
    - 'latency_jitter': Clock drift / delayed frame delivery
    """

    @staticmethod
    def apply_to_observation(observation: Observation, config: Optional[PerturbationConfig]) -> Observation:
        if not config or config.type == "none" or config.intensity <= 0.0:
            return observation

        obs_copy = observation.model_copy(deep=True)
        rng = random.Random((config.seed or 42) + observation.frame_idx)
        intensity = config.intensity

        if config.type == "frame_drop":
            drop_freq = max(2, int(10 / max(intensity, 1.0)))
            if observation.frame_idx % drop_freq == 0:
                if not obs_copy.metadata:
                    obs_copy.metadata = {}
                obs_copy.metadata["dropped_frame"] = True

        elif config.type == "latency_jitter":
            added_delay = int(intensity * rng.uniform(20.0, 80.0))
            obs_copy.timestamp_ms += added_delay
            if not obs_copy.metadata:
                obs_copy.metadata = {}
            obs_copy.metadata["injected_delay_ms"] = added_delay

        return obs_copy

    @staticmethod
    def perturb_image(image: Image.Image, config: PerturbationConfig) -> Image.Image:
        """Perturb PIL Image directly with calibrated noise/optical models."""
        intensity = config.intensity
        p_type = config.type

        if p_type == "gaussian_noise":
            np_img = np.array(image, dtype=np.float32)
            noise_sigma = intensity * 15.0
            noise = np.random.normal(0, noise_sigma, np_img.shape)
            noisy_img = np.clip(np_img + noise, 0, 255).astype(np.uint8)
            return Image.fromarray(noisy_img)

        elif p_type == "cmos_sensor_noise":
            # Calibrated CMOS model: Photon shot noise (Poisson) + Read noise (Gaussian)
            np_img = np.array(image, dtype=np.float32) / 255.0
            gain = max(0.01, intensity * 0.08)
            # Shot noise
            noisy = np.random.poisson(np.maximum(0, np_img / gain)) * gain
            # Read/thermal noise
            read_noise = np.random.normal(0, 0.015 * intensity, np_img.shape)
            final_img = np.clip((noisy + read_noise) * 255.0, 0, 255).astype(np.uint8)
            return Image.fromarray(final_img)

        elif p_type == "rolling_shutter":
            # Scanline horizontal shear
            np_img = np.array(image)
            h, w, c = np_img.shape
            shifted = np.zeros_like(np_img)
            max_shift = int(intensity * 12)
            for y in range(h):
                shift = int((y / h) * max_shift)
                if shift > 0:
                    shifted[y, shift:] = np_img[y, :-shift]
                    shifted[y, :shift] = np_img[y, 0]
                else:
                    shifted[y] = np_img[y]
            return Image.fromarray(shifted)

        elif p_type == "motion_blur":
            radius = int(intensity * 3)
            return image.filter(ImageFilter.BoxBlur(radius=max(1, radius)))

        elif p_type == "exposure_change":
            factor = 1.0 + (intensity * 0.3) if config.params.get("mode") == "over" else max(0.1, 1.0 - (intensity * 0.2))
            enhancer = ImageEnhance.Brightness(image)
            return enhancer.enhance(factor)

        elif p_type == "compression_artifact":
            quality = max(5, int(90 - intensity * 20))
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG", quality=quality)
            buffer.seek(0)
            return Image.open(buffer)

        return image
