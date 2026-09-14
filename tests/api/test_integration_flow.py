from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from services.api.services.scenario_service import ScenarioService


def test_full_experiment_lifecycle(client: TestClient, db_session: Session):
    # Ensure sample scenarios are ingested in test DB
    sample_dir = Path("./data/sample/scenarios")
    if sample_dir.exists():
        for p in sample_dir.iterdir():
            if p.is_dir() and (p / "metadata.json").exists():
                ScenarioService.ingest_from_directory(db_session, str(p), p.name)

    # 1. Health check
    res = client.get("/health")
    assert res.status_code == 200

    # 2. List scenarios
    sc_res = client.get("/api/v1/scenarios")
    assert sc_res.status_code == 200
    scenarios = sc_res.json()
    assert len(scenarios) >= 1
    scenario_id = scenarios[0]["id"]

    # 3. Create experiment
    exp_res = client.post("/api/v1/experiments", json={
        "name": "Integration Test Experiment",
        "scenario_ids": [scenario_id],
        "model_id": "mock-vla-v1",
        "eval_profile": "standard"
    })
    assert exp_res.status_code == 200
    exp_id = exp_res.json()["id"]

    # 4. Queue run
    run_res = client.post("/api/v1/runs", json={
        "experiment_id": exp_id,
        "scenario_id": scenario_id,
        "model_id": "mock-vla-v1",
        "seed": 42
    })
    assert run_res.status_code == 200
    run_id = run_res.json()["id"]

    # 5. Check run status & traces
    r_detail = client.get(f"/api/v1/runs/{run_id}")
    assert r_detail.status_code == 200
    assert r_detail.json()["status"] == "COMPLETED"

    # 6. Retrieve trace
    trace_res = client.get(f"/api/v1/runs/{run_id}/trace")
    assert trace_res.status_code == 200
    traces = trace_res.json()
    assert len(traces) > 0

    # 7. Retrieve metrics
    metrics_res = client.get(f"/api/v1/runs/{run_id}/metrics")
    assert metrics_res.status_code == 200
    metrics = metrics_res.json()
    assert len(metrics) > 0

    # 8. Export manifest
    manifest_res = client.get(f"/api/v1/export/{run_id}")
    assert manifest_res.status_code == 200
    manifest = manifest_res.json()
    assert manifest["config_hash"] is not None
