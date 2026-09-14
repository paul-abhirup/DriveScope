#!/usr/bin/env python3
"""
Generates TypeScript API type definitions directly from FastAPI's OpenAPI JSON specification.
"""

import json
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.api.main import app

def generate_openapi():
    output_path = Path("./apps/web/src/types/openapi.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    openapi_schema = app.openapi()
    with open(output_path, "w") as f:
        json.dump(openapi_schema, f, indent=2)
    print(f"Exported OpenAPI spec to {output_path}")

if __name__ == "__main__":
    generate_openapi()
