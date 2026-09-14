import logging
from .celery_app import celery_app
from .runner import execute_run_sync

logger = logging.getLogger(__name__)


@celery_app.task(name="drivescope.run_inference_task", bind=True)
def run_inference_task(self, run_id: str):
    """Celery task wrapper for running scenario inference & evaluation."""
    logger.info(f"Starting Celery execution for run {run_id}")
    result = execute_run_sync(run_id)
    logger.info(f"Finished Celery execution for run {run_id}: {result}")
    return result
