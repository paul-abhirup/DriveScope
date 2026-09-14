import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .config import settings
from .database import init_db, get_db
from .services.analysis_service import AnalysisService
from .services.scenario_service import ScenarioService
from .routers import scenarios, models, experiments, runs, failures, export, ws


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables
    init_db()
    
    # Auto-seed sample scenario if available and DB is empty
    db = next(get_db())
    try:
        sample_dir = Path("./data/sample/scenarios")
        if sample_dir.exists():
            for p in sample_dir.iterdir():
                if p.is_dir() and (p / "metadata.json").exists():
                    try:
                        ScenarioService.ingest_from_directory(db, str(p), p.name)
                    except Exception as e:
                        print(f"Scenario ingest warning: {e}")
    finally:
        db.close()
    
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    description="Experiment infrastructure for evaluating Vision-Language-Action (VLA) agents",
    lifespan=lifespan
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
api_v1_prefix = "/api/v1"
app.include_router(scenarios.router, prefix=api_v1_prefix)
app.include_router(models.router, prefix=api_v1_prefix)
app.include_router(experiments.router, prefix=api_v1_prefix)
app.include_router(runs.router, prefix=api_v1_prefix)
app.include_router(failures.router, prefix=api_v1_prefix)
app.include_router(export.router, prefix=api_v1_prefix)
app.include_router(ws.router)


@app.get("/health")
@app.get("/api/v1/health")
def health_check():
    return {
        "status": "healthy",
        "mode": settings.MODE,
        "version": "0.1.0",
        "service": "DriveScope Control Plane"
    }


@app.get("/api/v1/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    """Retrieve top-level platform overview metrics and recent activity."""
    return AnalysisService.get_dashboard_summary(db)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("services.api.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=True)
