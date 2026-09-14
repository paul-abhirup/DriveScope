from typing import List
from drivescope_schema.models import InferenceTrace, Metric


def compute_temporal_metrics(traces: List[InferenceTrace], run_id: str) -> List[Metric]:
    """
    Computes temporal metrics including decision latency distribution (mean, p95)
    and reaction delay to hazard occurrences.
    """
    if not traces:
        return []

    latencies = [t.latency_ms for t in traces]
    latencies_sorted = sorted(latencies)
    n = len(latencies)

    mean_latency = sum(latencies) / n
    p95_idx = min(int(n * 0.95), n - 1)
    p95_latency = latencies_sorted[p95_idx]
    max_latency = latencies_sorted[-1]

    # Reaction time: first frame where hazard is present vs first frame model brakes or mentions hazard
    reaction_delay_ms = 0.0
    first_hazard_idx = None
    first_reaction_idx = None

    for t in traces:
        if t.hazards_present and first_hazard_idx is None:
            first_hazard_idx = t.frame_idx
        if first_hazard_idx is not None and first_reaction_idx is None:
            if t.predicted_action.brake > 0.3 or t.hazards_detected:
                first_reaction_idx = t.frame_idx

    if first_hazard_idx is not None and first_reaction_idx is not None:
        delta_frames = max(0, first_reaction_idx - first_hazard_idx)
        # Assuming nominal 20 FPS = 50ms per frame
        reaction_delay_ms = delta_frames * 50.0

    return [
        Metric(run_id=run_id, metric_name="temporal_mean_latency_ms", metric_group="temporal", value=round(mean_latency, 2), aggregation="mean"),
        Metric(run_id=run_id, metric_name="temporal_p95_latency_ms", metric_group="temporal", value=round(p95_latency, 2), aggregation="p95"),
        Metric(run_id=run_id, metric_name="temporal_max_latency_ms", metric_group="temporal", value=round(max_latency, 2), aggregation="max"),
        Metric(run_id=run_id, metric_name="temporal_hazard_reaction_delay_ms", metric_group="temporal", value=round(reaction_delay_ms, 2), aggregation="point"),
    ]
