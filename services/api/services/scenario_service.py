import json
from pathlib import Path
from typing import List, Optional
from sqlalchemy.orm import Session
from ..models.db_models import ScenarioDB, ScenarioFrameDB
from drivescope_schema.models import Scenario, ScenarioMetadata, ScenarioFrame
from drivescope_vla_sdk.protocol import DatasetScenarioSource


class ScenarioService:
    @staticmethod
    def list_scenarios(db: Session, tag: Optional[str] = None) -> List[ScenarioDB]:
        query = db.query(ScenarioDB)
        if tag:
            query = query.filter(ScenarioDB.tags.contains([tag]))
        return query.all()

    @staticmethod
    def get_scenario(db: Session, scenario_id: str) -> Optional[ScenarioDB]:
        return db.query(ScenarioDB).filter(ScenarioDB.id == scenario_id).first()

    @staticmethod
    def get_scenario_frames(db: Session, scenario_id: str, limit: int = 500) -> List[ScenarioFrameDB]:
        return db.query(ScenarioFrameDB).filter(
            ScenarioFrameDB.scenario_id == scenario_id
        ).order_by(ScenarioFrameDB.frame_idx.asc()).limit(limit).all()

    @staticmethod
    def ingest_from_directory(db: Session, directory_path: str, scenario_id: Optional[str] = None) -> ScenarioDB:
        path = Path(directory_path)
        if (path / "metadata.json").exists():
            scenario_dir = path
            scenario_id = scenario_id or path.name
            parent_dir = path.parent
        else:
            scenario_id = scenario_id or path.name
            scenario_dir = path / scenario_id
            parent_dir = path

        source = DatasetScenarioSource(str(parent_dir))
        metadata = source.get_metadata(scenario_id)

        # Check if already exists, update or create
        existing = db.query(ScenarioDB).filter(ScenarioDB.id == scenario_id).first()
        if existing:
            existing.name = metadata.scenario_id.replace("_", " ").title()
            existing.tags = metadata.tags
            existing.description = metadata.description
            existing.fps = metadata.fps
            existing.metadata_json = metadata.model_dump()
            db_scenario = existing
            # Clear old frames
            db.query(ScenarioFrameDB).filter(ScenarioFrameDB.scenario_id == scenario_id).delete()
        else:
            db_scenario = ScenarioDB(
                id=scenario_id,
                name=scenario_id.replace("_", " ").title(),
                tags=metadata.tags,
                source_ref=str(scenario_dir),
                description=metadata.description,
                fps=metadata.fps,
                metadata_json=metadata.model_dump(),
            )
            db.add(db_scenario)
            db.flush()

        # Ingest frames
        frames = list(source.get_frames(scenario_id))
        db_scenario.total_frames = len(frames)

        for f in frames:
            frame_db = ScenarioFrameDB(
                scenario_id=scenario_id,
                frame_idx=f.frame_idx,
                timestamp_ms=f.timestamp_ms,
                image_uri=f.image_uri,
                ego_state=f.ego.model_dump(),
                ground_truth=f.ground_truth.model_dump(),
                sensor_meta=f.sensor_meta
            )
            db.add(frame_db)

        db.commit()
        db.refresh(db_scenario)
        return db_scenario
