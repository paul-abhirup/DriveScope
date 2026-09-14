# ADR-001: Prerecorded Dataset Sequences as Initial ScenarioSource

## Status
Accepted

## Context
Running full photorealistic simulators like CARLA or Unreal Engine requires heavy GPU compute and complex environment setup, posing an obstacle to rapid local testing and development.

## Decision
Implement `DatasetScenarioSource` as the first scenario source, reading structured frame directories and ground-truth metadata.

## Consequences
- Enables full experiment orchestration on laptops, portable systems, and CI/CD pipelines with zero GPU requirements.
- The `ScenarioSource` Protocol ensures future CARLA or live-rig implementations plug directly into the platform without modifying evaluation or UI layers.
