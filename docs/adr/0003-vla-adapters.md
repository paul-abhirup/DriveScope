# ADR-003: Strict VLA Adapter Protocol and Output Normalization

## Status
Accepted

## Context
Multimodal models and VLA agents produce heterogeneous output formats, token streams, and latency profiles.

## Decision
Enforce a strict `VLAAdapter` interface requiring all models to emit a validated `VLAOutput` model containing structured actions, natural language reasoning strings, and confidence metrics.

## Consequences
Database schemas, WebSocket broadcasts, evaluation calculators, and replay interfaces remain decoupled from specific model architectures.
