from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.scenario_service import ScenarioService
from drivescope_schema.models import Scenario, ScenarioFrame

router = APIRouter(prefix="/scenarios", tags=["Scenarios"])


@router.get("", response_model=List[dict])
def list_scenarios(tag: Optional[str] = None, db: Session = Depends(get_db)):
    scenarios = ScenarioService.list_scenarios(db, tag=tag)
    return [
        {
            "id": s.id,
            "name": s.name,
            "tags": s.tags,
            "total_frames": s.total_frames,
            "fps": s.fps,
            "description": s.description,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "metadata": s.metadata_json
        } for s in scenarios
    ]


@router.get("/{scenario_id}")
def get_scenario(scenario_id: str, db: Session = Depends(get_db)):
    scenario = ScenarioService.get_scenario(db, scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return {
        "id": scenario.id,
        "name": scenario.name,
        "tags": scenario.tags,
        "total_frames": scenario.total_frames,
        "fps": scenario.fps,
        "description": scenario.description,
        "created_at": scenario.created_at.isoformat() if scenario.created_at else None,
        "metadata": scenario.metadata_json
    }


@router.get("/{scenario_id}/frames")
def get_scenario_frames(scenario_id: str, limit: int = 500, db: Session = Depends(get_db)):
    frames = ScenarioService.get_scenario_frames(db, scenario_id, limit=limit)
    return [
        {
            "frame_idx": f.frame_idx,
            "timestamp_ms": f.timestamp_ms,
            "image_uri": f.image_uri,
            "ego": f.ego_state,
            "ground_truth": f.ground_truth,
            "sensor_meta": f.sensor_meta
        } for f in frames
    ]


@router.post("/ingest")
def ingest_scenario(payload: dict, db: Session = Depends(get_db)):
    dir_path = payload.get("directory_path")
    scenario_id = payload.get("scenario_id")
    if not dir_path:
        raise HTTPException(status_code=400, detail="directory_path is required")
    try:
        scenario = ScenarioService.ingest_from_directory(db, dir_path, scenario_id)
        return {"status": "success", "scenario_id": scenario.id, "total_frames": scenario.total_frames}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
