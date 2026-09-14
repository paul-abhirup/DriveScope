from typing import List, Tuple
from drivescope_schema.models import (
    InferenceTrace,
    Metric,
    FailureRecord,
    FailureClass,
    FailureSeverity,
)


def compute_safety_metrics_and_failures(
    traces: List[InferenceTrace],
    run_id: str,
    ttc_critical_threshold: float = 1.5
) -> Tuple[List[Metric], List[FailureRecord]]:
    """
    Computes proxy safety metrics:
    - Minimum Time-To-Collision (TTC)
    - Critical TTC breach events
    - Missed hazard detection count
    - Unsafe braking anomalies
    """
    if not traces:
        return [], []

    failures: List[FailureRecord] = []
    min_ttc = 999.0
    ttc_breaches = 0
    missed_hazards = 0
    unsafe_brakings = 0

    for t in traces:
        # Check TTC
        if t.ttc_seconds is not None:
            min_ttc = min(min_ttc, t.ttc_seconds)
            if t.ttc_seconds < ttc_critical_threshold:
                ttc_breaches += 1
                failures.append(FailureRecord(
                    run_id=run_id,
                    frame_idx=t.frame_idx,
                    failure_class=FailureClass.TTC_BREACH,
                    severity=FailureSeverity.CRITICAL if t.ttc_seconds < 1.0 else FailureSeverity.HIGH,
                    evidence={
                        "ttc_seconds": t.ttc_seconds,
                        "threshold": ttc_critical_threshold,
                        "ego_speed_mps": t.ego_speed_mps,
                        "predicted_brake": t.predicted_action.brake
                    }
                ))

        # Check Missed Hazard (hazard present in scene, ground truth requires brake > 0.5, but model didn't detect & brake < 0.2)
        if t.hazards_present and t.ground_truth_action.brake > 0.4:
            if not t.hazards_detected and t.predicted_action.brake < 0.2:
                missed_hazards += 1
                failures.append(FailureRecord(
                    run_id=run_id,
                    frame_idx=t.frame_idx,
                    failure_class=FailureClass.MISSED_HAZARD,
                    severity=FailureSeverity.HIGH,
                    evidence={
                        "hazards_present": t.hazards_present,
                        "ground_truth_brake": t.ground_truth_action.brake,
                        "predicted_brake": t.predicted_action.brake,
                        "reasoning": t.model_reasoning
                    }
                ))

        # Check Unnecessary / Unsafe abrupt braking on empty road (speed high, no hazard, GT brake == 0, pred brake > 0.8)
        if not t.hazards_present and t.ground_truth_action.brake == 0.0 and t.predicted_action.brake > 0.7:
            unsafe_brakings += 1
            failures.append(FailureRecord(
                run_id=run_id,
                frame_idx=t.frame_idx,
                failure_class=FailureClass.UNNECESSARY_INTERVENTION,
                severity=FailureSeverity.MEDIUM,
                evidence={
                    "predicted_brake": t.predicted_action.brake,
                    "ground_truth_brake": 0.0,
                    "reasoning": t.model_reasoning
                }
            ))

    metrics = [
        Metric(run_id=run_id, metric_name="safety_min_ttc_seconds", metric_group="safety", value=round(min_ttc, 2) if min_ttc < 900 else -1.0, aggregation="min"),
        Metric(run_id=run_id, metric_name="safety_ttc_breach_count", metric_group="safety", value=float(ttc_breaches), aggregation="count"),
        Metric(run_id=run_id, metric_name="safety_missed_hazard_count", metric_group="safety", value=float(missed_hazards), aggregation="count"),
        Metric(run_id=run_id, metric_name="safety_unsafe_braking_count", metric_group="safety", value=float(unsafe_brakings), aggregation="count"),
    ]

    return metrics, failures
