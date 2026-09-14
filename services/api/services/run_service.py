import hashlib
import json
import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from ..config import settings
from ..models.db_models import ExperimentDB, RunDB, InferenceTraceDB, MetricDB, FailureDB
from drivescope_schema.models import RunStatus, PerturbationConfig, RunManifest


class RunService:
    @staticmethod
    def create_experiment(
        db: Session,
        name: str,
        scenario_ids: List[str],
        model_id: str,
        eval_profile: str = "standard",
        frame_stride: int = 1,
        perturbation_profile: Optional[dict] = None,
        description: Optional[str] = None
    ) -> ExperimentDB:
        exp_id = f"exp_{uuid.uuid4().hex[:8]}"
        exp = ExperimentDB(
            id=exp_id,
            name=name,
            scenario_ids=scenario_ids,
            model_id=model_id,
            eval_profile=eval_profile,
            frame_stride=frame_stride,
            perturbation_profile=perturbation_profile,
            description=description
        )
        db.add(exp)
        db.commit()
        db.refresh(exp)
        return exp

    @staticmethod
    def queue_run(
        db: Session,
        experiment_id: str,
        scenario_id: str,
        model_id: Optional[str] = None,
        seed: int = 42,
        frame_stride: Optional[int] = None,
        perturbation_config: Optional[dict] = None
    ) -> RunDB:
        exp = db.query(ExperimentDB).filter(ExperimentDB.id == experiment_id).first()
        if not exp:
            raise ValueError(f"Experiment {experiment_id} not found")

        chosen_model = model_id or exp.model_id
        stride = frame_stride or exp.frame_stride or 1
        run_id = f"run_{uuid.uuid4().hex[:8]}"
        share_token = uuid.uuid4().hex
        
        # Merge perturbation config if provided or inherit from experiment
        p_cfg = perturbation_config or exp.perturbation_profile

        run = RunDB(
            id=run_id,
            experiment_id=experiment_id,
            scenario_id=scenario_id,
            model_id=chosen_model,
            status=RunStatus.QUEUED.value,
            seed=seed,
            frame_stride=stride,
            share_token=share_token,
            progress=0.0,
            perturbation_config=p_cfg
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        # Dispatch execution
        if settings.MODE == "minimal":
            from services.worker.runner import execute_run_sync
            # Execute synchronously in minimal mode or dispatch via async background task
            execute_run_sync(run_id, db)
        else:
            try:
                from services.worker.tasks import run_inference_task
                run_inference_task.delay(run_id)
            except Exception as e:
                # Fallback to sync execution if celery/redis not reachable
                from services.worker.runner import execute_run_sync
                execute_run_sync(run_id, db)

        db.refresh(run)
        return run

    @staticmethod
    def get_run(db: Session, run_id: str) -> Optional[RunDB]:
        return db.query(RunDB).filter(RunDB.id == run_id).first()

    @staticmethod
    def list_runs(db: Session, experiment_id: Optional[str] = None, limit: int = 50) -> List[RunDB]:
        query = db.query(RunDB)
        if experiment_id:
            query = query.filter(RunDB.experiment_id == experiment_id)
        return query.order_by(RunDB.created_at.desc()).limit(limit).all()

    @staticmethod
    def get_traces(db: Session, run_id: str, limit: int = 1000) -> List[InferenceTraceDB]:
        return db.query(InferenceTraceDB).filter(
            InferenceTraceDB.run_id == run_id
        ).order_by(InferenceTraceDB.frame_idx.asc()).limit(limit).all()

    @staticmethod
    def get_metrics(db: Session, run_id: str) -> List[MetricDB]:
        return db.query(MetricDB).filter(MetricDB.run_id == run_id).all()

    @staticmethod
    def generate_manifest(db: Session, run_id: str) -> RunManifest:
        run = db.query(RunDB).filter(RunDB.id == run_id).first()
        if not run:
            raise ValueError(f"Run {run_id} not found")

        metrics = db.query(MetricDB).filter(MetricDB.run_id == run_id).all()
        failures = db.query(FailureDB).filter(FailureDB.run_id == run_id).all()

        metrics_map = {m.metric_name: m.value for m in metrics}
        failures_map = {}
        for f in failures:
            failures_map[f.failure_class] = failures_map.get(f.failure_class, 0) + 1

        raw_config = f"{run.experiment_id}:{run.scenario_id}:{run.model_id}:{run.seed}:{json.dumps(run.perturbation_config, sort_keys=True)}"
        config_hash = hashlib.sha256(raw_config.encode()).hexdigest()

        return RunManifest(
            run_id=run.id,
            experiment_id=run.experiment_id,
            timestamp=run.created_at.isoformat(),
            code_version="0.1.0",
            scenario_id=run.scenario_id,
            scenario_version="1.0.0",
            model_id=run.model_id,
            model_version="1.0.0",
            eval_profile=run.experiment.eval_profile if run.experiment else "standard",
            frame_stride=run.frame_stride or 1,
            perturbation_profile=run.perturbation_config,
            seed=run.seed,
            config_hash=config_hash,
            share_token=run.share_token,
            metrics_summary=metrics_map,
            failures_summary=failures_map
        )
