import asyncio
import hashlib
import json
import logging
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from services.api.database import SessionLocal
from services.api.models.db_models import (
    RunDB,
    ScenarioDB,
    ScenarioFrameDB,
    InferenceTraceDB,
    MetricDB,
    FailureDB,
    ArtifactDB,
)
from drivescope_schema.models import (
    Observation,
    InferenceTrace,
    PerturbationConfig,
    RunStatus,
    PredictedAction,
    Action,
)
from models.adapters.registry import get_adapter
from evaluation.perturbation import PerturbationEngine
from evaluation.engine import EvaluationEngine
from evaluation.robustness import compute_robustness_metrics

logger = logging.getLogger("drivescope.worker")


def execute_run_sync(run_id: str, db: Optional[Session] = None) -> dict:
    """
    Synchronously executes a full inference and evaluation pipeline for a run.
    Used for minimal mode and direct worker invocations.
    """
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        run = db.query(RunDB).filter(RunDB.id == run_id).first()
        if not run:
            raise ValueError(f"Run {run_id} not found in database")

        run.status = RunStatus.RUNNING.value
        run.started_at = datetime.utcnow()
        run.progress = 0.0
        db.commit()

        scenario = db.query(ScenarioDB).filter(ScenarioDB.id == run.scenario_id).first()
        if not scenario:
            raise ValueError(f"Scenario {run.scenario_id} not found")

        frames = db.query(ScenarioFrameDB).filter(
            ScenarioFrameDB.scenario_id == run.scenario_id
        ).order_by(ScenarioFrameDB.frame_idx.asc()).all()

        if not frames:
            raise ValueError(f"Scenario {run.scenario_id} has no frames")

        # Instantiate VLA Adapter
        perturbation_cfg = PerturbationConfig(**run.perturbation_config) if run.perturbation_config else None
        
        # Apply frame stride if specified (e.g. evaluate every 2nd or 3rd frame)
        stride = run.frame_stride or 1
        eval_frames = frames[::stride]

        adapter = get_adapter(run.model_id, seed=run.seed)
        adapter.load()

        total_frames = len(eval_frames)
        trace_models: list[InferenceTrace] = []

        # Execute Frame-by-Frame Inference Loop
        for idx, f in enumerate(eval_frames):
            gt_dict = f.ground_truth or {}
            gt_action = gt_dict.get("action", {"steering": 0.0, "brake": 0.0, "throttle": 0.5})
            gt_hazards = gt_dict.get("hazards", [])
            gt_ttc = gt_dict.get("ttc_seconds")
            ego_dict = f.ego_state or {"speed_mps": 10.0}

            # Build Observation
            obs = Observation(
                scenario_id=run.scenario_id,
                frame_idx=f.frame_idx,
                timestamp_ms=f.timestamp_ms,
                image_uri=f.image_uri,
                ego=ego_dict,
                metadata={
                    "hazards": gt_hazards,
                    "conditions": scenario.metadata_json.get("conditions", {}) if scenario.metadata_json else {}
                }
            )

            # Apply sensor/temporal perturbation if configured
            if perturbation_cfg:
                obs = PerturbationEngine.apply_to_observation(obs, perturbation_cfg)

            # Run Model Inference
            vla_out = adapter.infer(obs)

            # Record Trace
            trace_entry = InferenceTrace(
                run_id=run.id,
                frame_idx=f.frame_idx,
                timestamp_ms=obs.timestamp_ms,
                image_uri=obs.image_uri,
                ego_speed_mps=obs.ego.speed_mps,
                model_reasoning=vla_out.reasoning,
                predicted_action=vla_out.action,
                ground_truth_action=Action(**gt_action),
                hazards_present=gt_hazards,
                hazards_detected=vla_out.extracted_hazards,
                confidence=vla_out.confidence,
                latency_ms=vla_out.latency_ms,
                ttc_seconds=gt_ttc
            )
            trace_models.append(trace_entry)

            # Persist Trace to DB
            db_trace = InferenceTraceDB(
                run_id=run.id,
                frame_idx=trace_entry.frame_idx,
                timestamp_ms=trace_entry.timestamp_ms,
                image_uri=trace_entry.image_uri,
                ego_speed_mps=trace_entry.ego_speed_mps,
                model_reasoning=trace_entry.model_reasoning,
                predicted_action=trace_entry.predicted_action.model_dump(),
                ground_truth_action=trace_entry.ground_truth_action.model_dump(),
                hazards_present=trace_entry.hazards_present,
                hazards_detected=trace_entry.hazards_detected,
                confidence=trace_entry.confidence,
                latency_ms=trace_entry.latency_ms,
                ttc_seconds=trace_entry.ttc_seconds
            )
            db.add(db_trace)

            # Update progress
            run.progress = round((idx + 1) / total_frames, 2)
            if (idx + 1) % 5 == 0 or idx == total_frames - 1:
                db.commit()

        # Transition to EVALUATING state
        run.status = RunStatus.EVALUATING.value
        db.commit()

        # Run Evaluation Engine
        eval_profile = run.experiment.eval_profile if run.experiment else "standard"
        metrics, failures = EvaluationEngine.evaluate_run(
            run_id=run.id,
            traces=trace_models,
            profile=eval_profile
        )

        # If this is a perturbation run with parent run, compute robustness curves
        parent_id = run.perturbation_config.get("parent_run_id") if run.perturbation_config else None
        if parent_id:
            parent_metrics_db = db.query(MetricDB).filter(MetricDB.run_id == parent_id).all()
            parent_metrics = [
                Metric(run_id=parent_id, metric_name=m.metric_name, metric_group=m.metric_group, value=m.value)
                for m in parent_metrics_db
            ]
            if parent_metrics:
                rob_metrics = compute_robustness_metrics(
                    baseline_metrics=parent_metrics,
                    perturbed_metrics=metrics,
                    perturbed_run_id=run.id,
                    perturbation_type=run.perturbation_config.get("type", "unknown"),
                    intensity=float(run.perturbation_config.get("intensity", 1.0))
                )
                metrics.extend(rob_metrics)

        # Persist Metrics
        for m in metrics:
            db_m = MetricDB(
                run_id=m.run_id,
                metric_name=m.metric_name,
                metric_group=m.metric_group,
                value=m.value,
                aggregation=m.aggregation,
                version=m.version,
                metadata_json=m.metadata_payload
            )
            db.add(db_m)

        # Persist Failures
        for fl in failures:
            db_f = FailureDB(
                run_id=fl.run_id,
                frame_idx=fl.frame_idx,
                failure_class=fl.failure_class.value,
                severity=fl.severity.value,
                evidence=fl.evidence
            )
            db.add(db_f)

        # Calculate Manifest Hash
        raw_manifest_str = f"{run.id}:{run.scenario_id}:{run.model_id}:{run.seed}:{len(trace_models)}"
        manifest_hash = hashlib.sha256(raw_manifest_str.encode()).hexdigest()

        run.manifest_hash = manifest_hash
        run.status = RunStatus.COMPLETED.value
        run.ended_at = datetime.utcnow()
        run.progress = 1.0

        db.commit()
        return {"status": "success", "run_id": run.id, "manifest_hash": manifest_hash}

    except Exception as e:
        logger.exception(f"Execution failed for run {run_id}: {e}")
        if run:
            run.status = RunStatus.FAILED.value
            run.error_message = str(e)
            run.ended_at = datetime.utcnow()
            db.commit()
        return {"status": "failed", "run_id": run_id, "error": str(e)}

    finally:
        if close_db:
            db.close()
