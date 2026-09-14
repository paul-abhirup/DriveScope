import io
import json
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.run_service import RunService
from ..services.analysis_service import AnalysisService

router = APIRouter(prefix="/export", tags=["Export & Analysis"])


@router.get("/{run_id}")
def export_run_manifest(run_id: str, db: Session = Depends(get_db)):
    """Export complete reproducible run manifest as JSON."""
    try:
        manifest = RunService.generate_manifest(db, run_id)
        return manifest.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{run_id}/csv")
def export_trace_csv(run_id: str, db: Session = Depends(get_db)):
    """Export frame-by-frame trace data as CSV."""
    traces = RunService.get_traces(db, run_id)
    if not traces:
        raise HTTPException(status_code=404, detail="No traces found for run")

    output = io.StringIO()
    output.write("frame_idx,timestamp_ms,ego_speed,pred_steer,pred_brake,pred_throttle,gt_steer,gt_brake,gt_throttle,confidence,latency_ms,ttc_seconds,reasoning\n")
    
    for t in traces:
        p_act = t.predicted_action
        g_act = t.ground_truth_action
        reasoning_escaped = (t.model_reasoning or "").replace('"', '""')
        line = f'{t.frame_idx},{t.timestamp_ms},{t.ego_speed_mps},{p_act.get("steering",0)},{p_act.get("brake",0)},{p_act.get("throttle",0)},{g_act.get("steering",0)},{g_act.get("brake",0)},{g_act.get("throttle",0)},{t.confidence},{t.latency_ms},{t.ttc_seconds or ""},"{reasoning_escaped}"\n'
        output.write(line)

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=run_{run_id}_trace.csv"}
    )


@router.get("/compare/{baseline_id}/{comparison_id}")
def compare_runs(baseline_id: str, comparison_id: str, db: Session = Depends(get_db)):
    """Compare baseline run against a perturbed or alternative model run."""
    try:
        return AnalysisService.compare_runs(db, baseline_id, comparison_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
