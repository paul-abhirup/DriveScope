from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from ..models.db_models import RunDB, FailureDB, MetricDB, ExperimentDB, ScenarioDB


class AnalysisService:
    @staticmethod
    def get_dashboard_summary(db: Session) -> Dict[str, Any]:
        total_runs = db.query(RunDB).count()
        completed_runs = db.query(RunDB).filter(RunDB.status == "COMPLETED").count()
        failed_runs = db.query(RunDB).filter(RunDB.status == "FAILED").count()
        total_scenarios = db.query(ScenarioDB).count()
        total_failures = db.query(FailureDB).count()

        # Failure distribution
        failures = db.query(FailureDB).all()
        failure_classes: Dict[str, int] = {}
        for f in failures:
            failure_classes[f.failure_class] = failure_classes.get(f.failure_class, 0) + 1

        recent_runs = db.query(RunDB).order_by(RunDB.created_at.desc()).limit(10).all()

        return {
            "total_runs": total_runs,
            "completed_runs": completed_runs,
            "failed_runs": failed_runs,
            "success_rate": round((completed_runs / max(1, total_runs)) * 100, 1),
            "total_scenarios": total_scenarios,
            "total_failures_detected": total_failures,
            "failure_distribution": failure_classes,
            "recent_runs": [
                {
                    "id": r.id,
                    "experiment_id": r.experiment_id,
                    "scenario_id": r.scenario_id,
                    "model_id": r.model_id,
                    "status": r.status,
                    "progress": r.progress,
                    "created_at": r.created_at.isoformat() if r.created_at else None
                } for r in recent_runs
            ]
        }

    @staticmethod
    def list_failures(
        db: Session,
        failure_class: Optional[str] = None,
        severity: Optional[str] = None,
        run_id: Optional[str] = None,
        limit: int = 100
    ) -> List[FailureDB]:
        query = db.query(FailureDB)
        if failure_class:
            query = query.filter(FailureDB.failure_class == failure_class)
        if severity:
            query = query.filter(FailureDB.severity == severity)
        if run_id:
            query = query.filter(FailureDB.run_id == run_id)
        return query.order_by(FailureDB.detected_at.desc()).limit(limit).all()

    @staticmethod
    def compare_runs(db: Session, baseline_run_id: str, comparison_run_id: str) -> Dict[str, Any]:
        base_run = db.query(RunDB).filter(RunDB.id == baseline_run_id).first()
        comp_run = db.query(RunDB).filter(RunDB.id == comparison_run_id).first()

        if not base_run or not comp_run:
            raise ValueError("One or both runs not found for comparison")

        base_metrics = {m.metric_name: m.value for m in base_run.metrics}
        comp_metrics = {m.metric_name: m.value for m in comp_run.metrics}

        all_keys = set(base_metrics.keys()).union(set(comp_metrics.keys()))
        metric_deltas = {}

        for k in sorted(all_keys):
            b_val = base_metrics.get(k, 0.0)
            c_val = comp_metrics.get(k, 0.0)
            delta = c_val - b_val
            pct_change = (delta / max(0.0001, abs(b_val))) * 100.0 if b_val != 0 else 0.0
            metric_deltas[k] = {
                "baseline": round(b_val, 4),
                "comparison": round(c_val, 4),
                "delta": round(delta, 4),
                "pct_change": round(pct_change, 2)
            }

        return {
            "baseline_run": {
                "id": base_run.id,
                "model_id": base_run.model_id,
                "scenario_id": base_run.scenario_id,
                "perturbation": base_run.perturbation_config,
                "failures_count": len(base_run.failures)
            },
            "comparison_run": {
                "id": comp_run.id,
                "model_id": comp_run.model_id,
                "scenario_id": comp_run.scenario_id,
                "perturbation": comp_run.perturbation_config,
                "failures_count": len(comp_run.failures)
            },
            "metric_deltas": metric_deltas
        }
