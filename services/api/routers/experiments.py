from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.db_models import ExperimentDB
from ..services.run_service import RunService

router = APIRouter(prefix="/experiments", tags=["Experiments"])


@router.get("")
def list_experiments(db: Session = Depends(get_db)):
    exps = db.query(ExperimentDB).order_by(ExperimentDB.created_at.desc()).all()
    return [
        {
            "id": e.id,
            "name": e.name,
            "scenario_ids": e.scenario_ids,
            "model_id": e.model_id,
            "eval_profile": e.eval_profile,
            "perturbation_profile": e.perturbation_profile,
            "description": e.description,
            "created_at": e.created_at.isoformat() if e.created_at else None,
            "runs_count": len(e.runs)
        } for e in exps
    ]


@router.post("")
def create_experiment(payload: dict, db: Session = Depends(get_db)):
    name = payload.get("name")
    scenario_ids = payload.get("scenario_ids", [])
    model_id = payload.get("model_id", "mock-vla-v1")
    eval_profile = payload.get("eval_profile", "standard")
    perturbation_profile = payload.get("perturbation_profile")
    description = payload.get("description")

    if not name or not scenario_ids:
        raise HTTPException(status_code=400, detail="name and scenario_ids are required")

    exp = RunService.create_experiment(
        db=db,
        name=name,
        scenario_ids=scenario_ids,
        model_id=model_id,
        eval_profile=eval_profile,
        perturbation_profile=perturbation_profile,
        description=description
    )
    return {
        "id": exp.id,
        "name": exp.name,
        "scenario_ids": exp.scenario_ids,
        "model_id": exp.model_id,
        "eval_profile": exp.eval_profile,
        "perturbation_profile": exp.perturbation_profile,
        "description": exp.description,
        "created_at": exp.created_at.isoformat() if exp.created_at else None
    }


@router.get("/{experiment_id}")
def get_experiment(experiment_id: str, db: Session = Depends(get_db)):
    exp = db.query(ExperimentDB).filter(ExperimentDB.id == experiment_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return {
        "id": exp.id,
        "name": exp.name,
        "scenario_ids": exp.scenario_ids,
        "model_id": exp.model_id,
        "eval_profile": exp.eval_profile,
        "perturbation_profile": exp.perturbation_profile,
        "description": exp.description,
        "created_at": exp.created_at.isoformat() if exp.created_at else None,
        "runs": [
            {
                "id": r.id,
                "scenario_id": r.scenario_id,
                "model_id": r.model_id,
                "status": r.status,
                "progress": r.progress,
                "created_at": r.created_at.isoformat() if r.created_at else None
            } for r in exp.runs
        ]
    }
