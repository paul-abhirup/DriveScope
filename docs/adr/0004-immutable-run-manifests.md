# ADR-004: Immutable Run Manifests for Experiment Reproducibility

## Status
Accepted

## Context
Scientific evaluation requires that repeating an experiment with the same random seed, scenario version, and model parameters produces identical results.

## Decision
Generate a SHA-256 configuration hash and an immutable `RunManifest` upon completion of each experiment run.

## Consequences
Run results can be exported and cryptographically verified, ensuring experiment provenance across research teams.
