"""Quantized small VLM adapter for CPU inference.

Runs a small vision-language driving agent locally via llama-cpp-python using
the mtmd (multimodal) chat handler, which supports SmolVLM2 (and other mtmd
architectures) with an external mmproj vision projector.

When model weights or the llama-cpp backend are unavailable, the adapter
gracefully falls back to a deterministic, seed-free heuristic so that the rest
of the platform (evaluation engine, API, tests) keeps working offline.
"""

import base64
import json
import logging
import os
import re
import time
from collections import deque
from typing import Optional

from drivescope_schema.models import Observation, VLAOutput, PredictedAction, AdapterHealth
from .base import BaseVLAAdapter

logger = logging.getLogger("drivescope.adapters.local_vlm")

DEFAULT_MODEL_PATH = "./weights/SmolVLM2-2.2B-Instruct-Q4_K_M.gguf"
DEFAULT_MMPROJ_PATH = "./weights/mmproj-SmolVLM2-2.2B-Instruct-Q8_0.gguf"
MAX_INFERENCE_ATTEMPTS = 2

SYSTEM_PROMPT = (
    "Analyze the front camera driving scene. Output JSON: "
    "steering (float -1..1, right positive), brake (float 0..1), "
    "throttle (float 0..1), confidence (float 0..1), "
    "detected_hazards (array, max 2, empty if no hazards), "
    "reasoning (one short sentence)."
)

_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, float(value)))


def _extract_json(text: str) -> Optional[dict]:
    """Best-effort JSON extraction from model output (strips code fences)."""
    if not text:
        return None
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except (json.JSONDecodeError, TypeError):
        pass
    match = _JSON_OBJECT_RE.search(text)
    if match:
        try:
            return json.loads(match.group(0))
        except (json.JSONDecodeError, TypeError):
            pass
    return None


_ACTION_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "steering": {"type": "number"},
        "brake": {"type": "number"},
        "throttle": {"type": "number"},
        "confidence": {"type": "number"},
        "detected_hazards": {"type": "array", "maxItems": 2, "items": {"type": "string"}},
        "reasoning": {"type": "string"},
    },
    "required": ["steering", "brake", "throttle", "confidence", "detected_hazards", "reasoning"],
    "additionalProperties": False,
}


def _deep_get(data: dict, key: str, default=None):
    """Search a possibly-nested dict for a key at any depth."""
    if key in data:
        return data[key]
    for value in data.values():
        if isinstance(value, dict):
            found = _deep_get(value, key, _MISSING)
            if found is not _MISSING:
                return found
    return default


_MISSING = object()


def _resolve_image_path(observation: Observation) -> Optional[str]:
    uri = observation.image_data or observation.image_uri
    if observation.image_data:
        return None  # bytes already carried on the observation
    if not uri:
        return None
    path = str(uri)
    if not os.path.isabs(path):
        path = os.path.abspath(path)
    return path if os.path.exists(path) else None


class LocalQuantizedVLM(BaseVLAAdapter):
    """
    CPU-viable quantized small VLM adapter (SmolVLM2 / SmolVLM / Moondream / Phi-3.5-Vision)
    running via quantized int4/int8 GGUF (llama.cpp) multimodal execution.
    """

    def __init__(
        self,
        model_id: str = "local-small-vlm-q4",
        quantization: str = "q4_k_m",
        runtime: str = "gguf_cpu",
        model_path: Optional[str] = None,
        mmproj_path: Optional[str] = None,
        n_ctx: int = 4096,
        n_threads: Optional[int] = None,
        temperature: float = 0.0,
        max_tokens: int = 256,
    ):
        super().__init__(model_id)
        self.quantization = quantization
        self.runtime = runtime
        self.model_path = model_path or os.getenv("VLM_MODEL_PATH", "").strip() or DEFAULT_MODEL_PATH
        self.mmproj_path = mmproj_path or os.getenv("VLM_MMPROJ_PATH", "").strip() or DEFAULT_MMPROJ_PATH
        self.n_ctx = n_ctx
        self.n_threads = n_threads or os.cpu_count() or 4
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._model = None
        self._latencies_ms = deque(maxlen=64)
        self._fallback_active = False
        self._load_error: Optional[str] = None

    # --- lifecycle ---------------------------------------------------------

    def load(self) -> None:
        """Load weights via llama-cpp-python; fall back to heuristic on failure."""
        for required in (self.model_path, self.mmproj_path):
            if not os.path.isfile(required):
                self._load_error = f"missing weights file: {required}"
                break
        else:
            try:
                from llama_cpp import Llama
                from llama_cpp.llama_chat_format import MTMDChatHandler

                handler = MTMDChatHandler(clip_model_path=self.mmproj_path, verbose=False, use_gpu=False)
                self._model = Llama(
                    model_path=self.model_path,
                    chat_handler=handler,
                    n_ctx=self.n_ctx,
                    n_gpu_layers=0,
                    n_threads=self.n_threads,
                    n_batch=256,
                    verbose=False,
                )
            except Exception as exc:  # noqa: BLE001 - backend is optional
                self._model = None
                self._load_error = f"llama.cpp init failed: {exc}"

        self._is_loaded = self._model is not None
        if self._model is not None:
            self._fallback_active = False
            self._load_error = None
            model_size_gb = os.path.getsize(self.model_path) / (1024 ** 3)
            logger.info(
                "LocalQuantizedVLM loaded: %s (%.2f GB, %d threads)",
                self.model_path, model_size_gb, self.n_threads,
            )
        else:
            self._fallback_active = True
            logger.warning(
                "LocalQuantizedVLM unavailable (%s); using heuristic fallback.",
                self._load_error or "unknown",
            )

    def _run_model_inference(self, observation: Observation) -> VLAOutput:
        start = time.perf_counter()
        if observation.image_data:
            image_bytes = observation.image_data
        else:
            image_path = _resolve_image_path(observation)
            if not image_path:
                raise FileNotFoundError(f"frame image not found: {observation.image_uri}")
            with open(image_path, "rb") as fh:
                image_bytes = fh.read()

        b64 = base64.b64encode(image_bytes).decode("ascii")
        mime = "image/png" if str(observation.image_uri).lower().endswith(".png") else "image/jpeg"
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                    {"type": "text", "text": SYSTEM_PROMPT},
                ],
            }
        ]
        response = self._model.create_chat_completion(
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stream=False,
            response_format={
                "type": "json_schema",
                "json_schema": {"name": "driving_output", "schema": _ACTION_JSON_SCHEMA},
            },
        )
        raw = response.get("choices", [{}])[0].get("message", {}).get("content", "") or ""

        latency_ms = (time.perf_counter() - start) * 1000.0
        self._latencies_ms.append(latency_ms)

        data = _extract_json(raw)
        if not data:
            raise ValueError(f"VLM returned unparseable output: {raw[:200]!r}")

        def num(key: str, default: float = 0.0) -> float:
            try:
                return float(_deep_get(data, key, default))
            except (TypeError, ValueError):
                return default

        hazards = _deep_get(data, "detected_hazards") or []
        if not isinstance(hazards, list):
            hazards = [str(hazards)]
        hazards = [str(h) for h in hazards]

        reasoning = str(_deep_get(data, "reasoning", "")).strip()
        if not reasoning or reasoning.lower() in {"short list", "empty if none", "none"}:
            reasoning = "No meaningful reasoning produced."

        return VLAOutput(
            model_id=self.model_id,
            timestamp_ms=observation.timestamp_ms,
            reasoning=reasoning,
            action=PredictedAction(
                steering=_clamp(num("steering"), -1.0, 1.0),
                brake=_clamp(num("brake"), 0.0, 1.0),
                throttle=_clamp(num("throttle"), 0.0, 1.0),
            ),
            confidence=_clamp(num("confidence", 0.5), 0.0, 1.0),
            latency_ms=round(latency_ms, 2),
            extracted_hazards=hazards,
            extra={
                "quantization": self.quantization,
                "runtime": self.runtime,
                "threads": self.n_threads,
                "inference": "llama.cpp",
            },
        )

    def _fallback_inference(self, observation: Observation) -> VLAOutput:
        start = time.perf_counter()
        metadata = observation.metadata or {}
        hazards = metadata.get("hazards", [])

        if hazards:
            hazard = hazards[0]
            reasoning = (
                f"[{self.model_id} fallback]: Ego corridor hazard '{hazard}' detected "
                "from scenario metadata. Recommending decelerating maneuver."
            )
            brake, throttle, steer = 0.60, 0.0, 0.0
            detected = list(hazards)
        else:
            reasoning = f"[{self.model_id} fallback]: Ego lane clear. Path free of obstacles."
            brake, throttle, steer = 0.0, 0.40, 0.0
            detected = []

        latency_ms = (time.perf_counter() - start) * 1000.0
        self._latencies_ms.append(latency_ms)

        return VLAOutput(
            model_id=self.model_id,
            timestamp_ms=observation.timestamp_ms,
            reasoning=reasoning,
            action=PredictedAction(steering=steer, brake=brake, throttle=throttle),
            confidence=0.6,
            latency_ms=round(latency_ms, 2),
            extracted_hazards=detected,
            extra={
                "quantization": self.quantization,
                "runtime": self.runtime,
                "threads": self.n_threads,
                "inference": "heuristic-fallback",
            },
        )

    # --- adapter interface -------------------------------------------------

    def infer(self, observation: Observation) -> VLAOutput:
        if self._model is not None:
            for attempt in range(MAX_INFERENCE_ATTEMPTS):
                try:
                    return self._run_model_inference(observation)
                except Exception as exc:  # noqa: BLE001 - fall back on any runtime error
                    logger.warning(
                        "Real inference attempt %d/%d failed (%s); %s",
                        attempt + 1, MAX_INFERENCE_ATTEMPTS, exc,
                        "retrying" if attempt + 1 < MAX_INFERENCE_ATTEMPTS else "using heuristic fallback",
                    )
            self._fallback_active = True
        return self._fallback_inference(observation)

    @property
    def latency_p50_ms(self) -> float:
        if not self._latencies_ms:
            return 0.0
        ordered = sorted(self._latencies_ms)
        mid = len(ordered) // 2
        if len(ordered) % 2 == 0:
            return round((ordered[mid - 1] + ordered[mid]) / 2.0, 2)
        return round(ordered[mid], 2)

    def health(self) -> AdapterHealth:
        status = "healthy" if self._model is not None else ("fallback" if self._fallback_active else "unloaded")
        details: dict = {
            "quantization": self.quantization,
            "runtime": self.runtime,
            "cpu_cores": self.n_threads,
            "model_path": self.model_path,
            "mmproj_path": self.mmproj_path,
            "inference_backend": "llama.cpp" if self._model is not None else "heuristic",
        }
        if self._model is not None and os.path.isfile(self.model_path):
            details["model_size_gb"] = round(os.path.getsize(self.model_path) / (1024 ** 3), 3)
        if self._load_error:
            details["load_error"] = self._load_error

        return AdapterHealth(
            adapter_id=self.model_id,
            status=status,
            model_name=f"Local Small VLM ({self.quantization.upper()})",
            device="cpu-x86_64",
            runtime_engine="llama.cpp / mtmd",
            latency_p50_ms=self.latency_p50_ms,
            details=details,
        )