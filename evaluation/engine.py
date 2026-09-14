from typing import List, Tuple
from drivescope_schema.models import InferenceTrace, Metric, FailureRecord

from .action import compute_action_metrics
from .temporal import compute_temporal_metrics
from .safety import compute_safety_metrics_and_failures
from .reasoning import compute_reasoning_action_consistency


class EvaluationEngine:
    """
    Central orchestration engine for executing evaluation profiles on inference traces.
    """

    @classmethod
    def evaluate_run(
        cls,
        run_id: str,
        traces: List[InferenceTrace],
        profile: str = "standard"
    ) -> Tuple[List[Metric], List[FailureRecord]]:
        """
        Runs all metric calculators for the specified profile and aggregates results.
        """
        all_metrics: List[Metric] = []
        all_failures: List[FailureRecord] = []

        # 1. Action error metrics
        action_metrics = compute_action_metrics(traces, run_id)
        all_metrics.extend(action_metrics)

        # 2. Temporal metrics
        temporal_metrics = compute_temporal_metrics(traces, run_id)
        all_metrics.extend(temporal_metrics)

        # 3. Safety proxy metrics & failure detection
        safety_metrics, safety_failures = compute_safety_metrics_and_failures(traces, run_id)
        all_metrics.extend(safety_metrics)
        all_failures.extend(safety_failures)

        # 4. Reasoning/Action consistency analysis
        reasoning_metrics, reasoning_failures = compute_reasoning_action_consistency(traces, run_id)
        all_metrics.extend(reasoning_metrics)
        all_failures.extend(reasoning_failures)

        return all_metrics, all_failures
