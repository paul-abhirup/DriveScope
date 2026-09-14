from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.run_service import RunService
from ..models.db_models import RunDB

router = APIRouter(prefix="/runs", tags=["Runs"])


@router.get("")
def list_runs(experiment_id: Optional[str] = None, limit: int = 50, db: Session = Depends(get_db)):
    runs = RunService.list_runs(db, experiment_id=experiment_id, limit=limit)
    return [
        {
            "id": r.id,
            "experiment_id": r.experiment_id,
            "scenario_id": r.scenario_id,
            "model_id": r.model_id,
            "status": r.status,
            "progress": r.progress,
            "seed": r.seed,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "ended_at": r.ended_at.isoformat() if r.ended_at else None,
            "error_message": r.error_message,
            "perturbation_config": r.perturbation_config,
            "created_at": r.created_at.isoformat() if r.created_at else None
        } for r in runs
    ]


@router.post("")
def queue_run(payload: dict, db: Session = Depends(get_db)):
    experiment_id = payload.get("experiment_id")
    scenario_id = payload.get("scenario_id")
    model_id = payload.get("model_id")
    seed = payload.get("seed", 42)
    perturbation_config = payload.get("perturbation_config")

    if not experiment_id or not scenario_id:
        raise HTTPException(status_code=400, detail="experiment_id and scenario_id are required")

    try:
        run = RunService.queue_run(
            db=db,
            experiment_id=experiment_id,
            scenario_id=scenario_id,
            model_id=model_id,
            seed=seed,
            perturbation_config=perturbation_config
        )
        return {
            "id": run.id,
            "status": run.status,
            "experiment_id": run.experiment_id,
            "scenario_id": run.scenario_id,
            "model_id": run.model_id,
            "progress": run.progress
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{run_id}")
def get_run(run_id: str, db: Session = Depends(get_db)):
    run = RunService.get_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    metrics = RunService.get_metrics(db, run_id)
    return {
        "id": run.id,
        "experiment_id": run.experiment_id,
        "scenario_id": run.scenario_id,
        "model_id": run.model_id,
        "status": run.status,
        "progress": run.progress,
        "seed": run.seed,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "ended_at": run.ended_at.isoformat() if run.ended_at else None,
        "manifest_hash": run.manifest_hash,
        "error_message": run.error_message,
        "perturbation_config": run.perturbation_config,
        "created_at": run.created_at.isoformat() if run.created_at else None,
        "metrics_count": len(metrics),
        "failures_count": len(run.failures)
    }


@router.get("/{run_id}/trace")
def get_run_trace(run_id: str, limit: int = 1000, db: Session = Depends(get_db)):
    traces = RunService.get_traces(db, run_id, limit=limit)
    return [
        {
            "frame_idx": t.frame_idx,
            "timestamp_ms": t.timestamp_ms,
            "image_uri": t.image_uri,
            "ego_speed_mps": t.ego_speed_mps,
            "model_reasoning": t.model_reasoning,
            "predicted_action": t.predicted_action,
            "ground_truth_action": t.ground_truth_action,
            "hazards_present": t.hazards_present,
            "hazards_detected": t.hazards_detected,
            "confidence": t.confidence,
            "latency_ms": t.latency_ms,
            "ttc_seconds": t.ttc_seconds
        } for t in traces
    ]


@router.get("/{run_id}/metrics")
def get_run_metrics(run_id: str, db: Session = Depends(get_db)):
    metrics = RunService.get_metrics(db, run_id)
    return [
        {
            "metric_name": m.metric_name,
            "metric_group": m.metric_group,
            "value": m.value,
            "aggregation": m.aggregation,
            "version": m.version,
            "metadata": m.metadata_json
        } for m in metrics
    ]


@router.get("/{run_id}/share")
def get_shareable_link(run_id: str, db: Session = Depends(get_db)):
    """Generate a shareable read-only signed link for an experiment run."""
    run = RunService.get_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    from ..auth import generate_share_signature
    sig = generate_share_signature(run.id, run.share_token or "public")
    return {
        "run_id": run.id,
        "share_token": run.share_token,
        "signature": sig,
        "share_url": f"/runs/shared/{run.id}?token={run.share_token}&sig={sig}"
    }


@router.get("/shared/{run_id}")
def get_shared_run(run_id: str, token: str = Query(...), sig: str = Query(...), db: Session = Depends(get_db)):
    """Read-only access to a shared experiment run via signed signature."""
    from ..auth import verify_share_signature
    run = RunService.get_run(db, run_id)
    if not run or not verify_share_signature(run_id, token, sig):
        raise HTTPException(status_code=403, detail="Invalid or expired share signature")

    metrics = RunService.get_metrics(db, run_id)
    return {
        "id": run.id,
        "experiment_id": run.experiment_id,
        "scenario_id": run.scenario_id,
        "model_id": run.model_id,
        "status": run.status,
        "metrics_summary": {m.metric_name: m.value for m in metrics},
        "failures_count": len(run.failures),
        "manifest_hash": run.manifest_hash
    }


@router.post("/{run_id}/perturb")
def queue_perturbation_run(run_id: str, payload: dict, db: Session = Depends(get_db)):
    base_run = RunService.get_run(db, run_id)
    if not base_run:
        raise HTTPException(status_code=404, detail="Base run not found")

    perturbation_type = payload.get("type", "gaussian_noise")
    intensity = payload.get("intensity", 1.0)
    params = payload.get("params", {})
    seed = payload.get("seed", base_run.seed)

    perturbation_config = {
        "type": perturbation_type,
        "intensity": intensity,
        "params": params,
        "seed": seed,
        "parent_run_id": base_run.id
    }

    try:
        new_run = RunService.queue_run(
            db=db,
            experiment_id=base_run.experiment_id,
            scenario_id=base_run.scenario_id,
            model_id=base_run.model_id,
            seed=seed,
            perturbation_config=perturbation_config
        )
        return {
            "status": "queued",
            "parent_run_id": base_run.id,
            "perturbed_run_id": new_run.id,
            "perturbation_config": perturbation_config
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

