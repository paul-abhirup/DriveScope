from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.analysis_service import AnalysisService

router = APIRouter(prefix="/failures", tags=["Failures"])


@router.get("")
def list_failures(
    failure_class: Optional[str] = None,
    severity: Optional[str] = None,
    run_id: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    failures = AnalysisService.list_failures(
        db=db,
        failure_class=failure_class,
        severity=severity,
        run_id=run_id,
        limit=limit
    )
    return [
        {
            "id": f.id,
            "run_id": f.run_id,
            "frame_idx": f.frame_idx,
            "failure_class": f.failure_class,
            "severity": f.severity,
            "evidence": f.evidence,
            "detected_at": f.detected_at.isoformat() if f.detected_at else None,
            "resolved": f.resolved,
            "notes": f.notes
        } for f in failures
    ]


@router.get("/summary")
def get_failures_summary(db: Session = Depends(get_db)):
    summary = AnalysisService.get_dashboard_summary(db)
    return {
        "total_failures": summary["total_failures_detected"],
        "distribution": summary["failure_distribution"]
    }
