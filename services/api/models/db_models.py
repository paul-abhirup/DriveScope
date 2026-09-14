import json
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    DateTime,
    Boolean,
    Text,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import relationship
from ..database import Base


class ScenarioDB(Base):
    __tablename__ = "scenarios"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    tags = Column(JSON, default=list)
    metadata_version = Column(String, default="1.0.0")
    source_ref = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    total_frames = Column(Integer, default=0)
    fps = Column(Integer, default=20)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    frames = relationship("ScenarioFrameDB", back_populates="scenario", cascade="all, delete-orphan")
    runs = relationship("RunDB", back_populates="scenario")


class ScenarioFrameDB(Base):
    __tablename__ = "scenario_frames"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scenario_id = Column(String, ForeignKey("scenarios.id", ondelete="CASCADE"), index=True)
    frame_idx = Column(Integer, nullable=False, index=True)
    timestamp_ms = Column(Integer, nullable=False)
    image_uri = Column(String, nullable=False)
    ego_state = Column(JSON, default=dict)
    ground_truth = Column(JSON, default=dict)
    sensor_meta = Column(JSON, default=dict)

    scenario = relationship("ScenarioDB", back_populates="frames")


class ExperimentDB(Base):
    __tablename__ = "experiments"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    scenario_ids = Column(JSON, default=list)
    model_id = Column(String, nullable=False)
    eval_profile = Column(String, default="standard")
    frame_stride = Column(Integer, default=1)
    perturbation_profile = Column(JSON, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    runs = relationship("RunDB", back_populates="experiment", cascade="all, delete-orphan")


class RunDB(Base):
    __tablename__ = "runs"

    id = Column(String, primary_key=True, index=True)
    experiment_id = Column(String, ForeignKey("experiments.id", ondelete="CASCADE"), index=True)
    scenario_id = Column(String, ForeignKey("scenarios.id"), index=True)
    model_id = Column(String, nullable=False)
    status = Column(String, default="CREATED", index=True)
    seed = Column(Integer, default=42)
    frame_stride = Column(Integer, default=1)
    progress = Column(Float, default=0.0)
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    manifest_hash = Column(String, nullable=True)
    share_token = Column(String, nullable=True, index=True)
    error_message = Column(Text, nullable=True)
    perturbation_config = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    experiment = relationship("ExperimentDB", back_populates="runs")
    scenario = relationship("ScenarioDB", back_populates="runs")
    traces = relationship("InferenceTraceDB", back_populates="run", cascade="all, delete-orphan")
    metrics = relationship("MetricDB", back_populates="run", cascade="all, delete-orphan")
    failures = relationship("FailureDB", back_populates="run", cascade="all, delete-orphan")


class InferenceTraceDB(Base):
    __tablename__ = "inference_traces"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, ForeignKey("runs.id", ondelete="CASCADE"), index=True)
    frame_idx = Column(Integer, nullable=False, index=True)
    timestamp_ms = Column(Integer, nullable=False)
    image_uri = Column(String, nullable=False)
    ego_speed_mps = Column(Float, default=0.0)
    model_reasoning = Column(Text, nullable=True)
    predicted_action = Column(JSON, nullable=False)
    ground_truth_action = Column(JSON, nullable=False)
    hazards_present = Column(JSON, default=list)
    hazards_detected = Column(JSON, default=list)
    confidence = Column(Float, default=1.0)
    latency_ms = Column(Float, default=0.0)
    ttc_seconds = Column(Float, nullable=True)

    run = relationship("RunDB", back_populates="traces")


class MetricDB(Base):
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, ForeignKey("runs.id", ondelete="CASCADE"), index=True)
    metric_name = Column(String, nullable=False, index=True)
    metric_group = Column(String, nullable=False, index=True)
    value = Column(Float, nullable=False)
    aggregation = Column(String, default="mean")
    version = Column(String, default="1.0.0")
    metadata_json = Column(JSON, nullable=True)

    run = relationship("RunDB", back_populates="metrics")


class FailureDB(Base):
    __tablename__ = "failures"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, ForeignKey("runs.id", ondelete="CASCADE"), index=True)
    frame_idx = Column(Integer, nullable=False)
    failure_class = Column(String, nullable=False, index=True)
    severity = Column(String, nullable=False, index=True)
    evidence = Column(JSON, nullable=False)
    detected_at = Column(DateTime, default=datetime.utcnow)
    resolved = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)

    run = relationship("RunDB", back_populates="failures")


class ArtifactDB(Base):
    __tablename__ = "artifacts"

    id = Column(String, primary_key=True, index=True)
    run_id = Column(String, ForeignKey("runs.id", ondelete="CASCADE"), index=True)
    artifact_type = Column(String, nullable=False)  # "manifest", "replay_package", "export_csv"
    uri = Column(String, nullable=False)
    checksum = Column(String, nullable=True)
    size_bytes = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
