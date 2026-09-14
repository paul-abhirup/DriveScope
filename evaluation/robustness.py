from typing import Dict, List
from drivescope_schema.models import Metric


def compute_robustness_metrics(
    baseline_metrics: List[Metric],
    perturbed_metrics: List[Metric],
    perturbed_run_id: str,
    perturbation_type: str,
    intensity: float
) -> List[Metric]:
    """
    Calculates degradation percentage and sensitivity slope comparing baseline metrics
    to perturbed execution metrics.
    """
    base_map: Dict[str, float] = {m.metric_name: m.value for m in baseline_metrics}
    pert_map: Dict[str, float] = {m.metric_name: m.value for m in perturbed_metrics}

    results: List[Metric] = []

    # Calculate degradation on primary error metrics
    key_metrics = [
        "action_steering_rmse",
        "action_brake_rmse",
        "reasoning_composite_consistency_score",
        "temporal_mean_latency_ms"
    ]

    total_degradation = 0.0
    valid_count = 0

    for km in key_metrics:
        if km in base_map and km in pert_map:
            b_val = base_map[km]
            p_val = pert_map[km]

            # For consistency score, lower is worse (degradation = (base - pert) / base)
            # For error/latency, higher is worse (degradation = (pert - base) / base)
            if "score" in km or "agreement" in km:
                pct_delta = ((b_val - p_val) / max(0.001, b_val)) * 100.0
            else:
                pct_delta = ((p_val - b_val) / max(0.001, b_val)) * 100.0

            metric_name = f"robustness_delta_{km}_pct"
            results.append(Metric(
                run_id=perturbed_run_id,
                metric_name=metric_name,
                metric_group="robustness",
                value=round(pct_delta, 2),
                aggregation="pct_delta",
                metadata_payload={"perturbation_type": perturbation_type, "intensity": intensity}
            ))

            total_degradation += max(0.0, pct_delta)
            valid_count += 1

    mean_degradation = (total_degradation / valid_count) if valid_count > 0 else 0.0
    sensitivity_slope = mean_degradation / max(0.1, intensity)

    results.append(Metric(
        run_id=perturbed_run_id,
        metric_name="robustness_mean_degradation_pct",
        metric_group="robustness",
        value=round(mean_degradation, 2),
        aggregation="mean",
        metadata_payload={"perturbation_type": perturbation_type, "intensity": intensity}
    ))

    results.append(Metric(
        run_id=perturbed_run_id,
        metric_name="robustness_sensitivity_slope",
        metric_group="robustness",
        value=round(sensitivity_slope, 4),
        aggregation="slope",
        metadata_payload={"perturbation_type": perturbation_type, "intensity": intensity}
    ))

    return results
