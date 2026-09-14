# ADR-002: Celery / Redis Task Queue with In-Process Fallback

## Status
Accepted

## Context
Asynchronous job dispatching is required for long-running inference runs, but local development environments may lack Redis or Docker services.

## Decision
Use Celery with Redis for scalable queue-based worker execution, while implementing a synchronous `MODE=minimal` in-process runner that functions on SQLite without external service dependencies.

## Consequences
Developers can run the full system immediately with `uvicorn` in minimal mode, while production and multi-worker deployments seamlessly use Docker Compose and Celery.
