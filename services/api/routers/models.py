from typing import List
from fastapi import APIRouter
from models.adapters.registry import list_available_adapters
from drivescope_schema.models import AdapterHealth

router = APIRouter(prefix="/models", tags=["Models"])


@router.get("", response_model=List[AdapterHealth])
def get_model_adapters():
    """List all available VLA model adapters and their health statuses."""
    return list_available_adapters()
