from models.adapters.local_small_vlm import (
    LocalQuantizedVLM,
    _extract_json,
    _deep_get,
    _MISSING,
    _ACTION_JSON_SCHEMA,
    MAX_INFERENCE_ATTEMPTS,
)
from models.adapters.registry import get_adapter, list_available_adapters
from drivescope_schema.models import Observation, EgoState, VLAOutput


def _make_obs(hazards=None):
    return Observation(
        scenario_id="test_01",
        frame_idx=15,
        timestamp_ms=750,
        image_uri="mock://frame.jpg",
        ego=EgoState(speed_mps=10.0),
        metadata={"hazards": hazards or []},
    )


def test_fallback_when_weights_missing():
    adapter = LocalQuantizedVLM(
        model_path="weights/does_not_exist.gguf",
        mmproj_path="weights/does_not_exist.gguf",
    )
    adapter.load()
    assert adapter._model is None
    assert adapter._fallback_active is True
    assert adapter._load_error is not None

    out = adapter.infer(_make_obs(["pedestrian"]))
    assert isinstance(out, VLAOutput)
    assert out.action.brake >= 0.5
    assert out.action.throttle == 0.0
    assert out.extra["inference"] == "heuristic-fallback"
    assert out.latency_ms >= 0.0


def test_fallback_clear_path():
    adapter = LocalQuantizedVLM(
        model_path="weights/does_not_exist.gguf",
        mmproj_path="weights/does_not_exist.gguf",
    )
    adapter.load()
    out = adapter.infer(_make_obs())
    assert out.action.brake == 0.0
    assert out.action.throttle == 0.40
    assert out.extracted_hazards == []


def test_fallback_deterministic():
    adapter = LocalQuantizedVLM(
        model_path="weights/does_not_exist.gguf",
        mmproj_path="weights/does_not_exist.gguf",
    )
    adapter.load()
    a = adapter.infer(_make_obs(["pedestrian"]))
    b = adapter.infer(_make_obs(["pedestrian"]))
    assert a.reasoning == b.reasoning
    assert a.action == b.action


def test_health_reports_fallback():
    adapter = LocalQuantizedVLM(
        model_path="weights/does_not_exist.gguf",
        mmproj_path="weights/does_not_exist.gguf",
    )
    adapter.load()
    health = adapter.health()
    assert health.status in {"fallback", "unloaded"}
    assert health.details["inference_backend"] == "heuristic"
    assert "load_error" in health.details


def test_extract_json_variants():
    assert _extract_json('{"steering": 0.1}') == {"steering": 0.1}
    assert _extract_json('```json\n{"brake": 0.5}\n```') == {"brake": 0.5}
    assert _extract_json('prefix {"throttle": 0.3} suffix') == {"throttle": 0.3}
    assert _extract_json("not json at all") is None
    assert _extract_json("") is None


def test_deep_get_nested():
    data = {"front_camera": {"steering": -0.5, "detected_hazards": ["pedestrian"]}}
    assert _deep_get(data, "steering") == -0.5
    assert _deep_get(data, "detected_hazards") == ["pedestrian"]
    assert _deep_get(data, "missing", "fallback") == "fallback"
    assert _deep_get({"a": 1}, "a") == 1
    assert _deep_get({"a": {"b": {"c": 3}}}, "c") == 3
    assert _deep_get({"a": {"b": 1}}, "zzz", _MISSING) is _MISSING


def test_action_schema_shape():
    assert set(_ACTION_JSON_SCHEMA["required"]) >= {
        "steering", "brake", "throttle", "detected_hazards", "reasoning",
    }


def test_inference_attempts_constant():
    assert MAX_INFERENCE_ATTEMPTS >= 1


def test_registry_includes_local_vlm():
    adapter = get_adapter("local-small-vlm-q4")
    assert isinstance(adapter, LocalQuantizedVLM)
    ids = {a.adapter_id for a in list_available_adapters()}
    assert "local-small-vlm-q4" in ids