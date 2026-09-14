import math
from typing import List, Dict, Any
from drivescope_schema.models import InferenceTrace, Metric


def compute_action_metrics(traces: List[InferenceTrace], run_id: str) -> List[Metric]:
    """
    Computes Action Error metrics (MAE and RMSE) for steering, brake, and throttle
    against ground truth annotations.
    """
    if not traces:
        return []

    steering_errors = []
    brake_errors = []
    throttle_errors = []
    cumulative_drift = 0.0

    for t in traces:
        pred = t.predicted_action
        gt = t.ground_truth_action
        
        s_err = pred.steering - gt.steering
        b_err = pred.brake - gt.brake
        t_err = pred.throttle - gt.throttle

        steering_errors.append(s_err)
        brake_errors.append(b_err)
        throttle_errors.append(t_err)
        cumulative_drift += abs(s_err)

    n = len(traces)
    
    # Steering MAE & RMSE
    steering_mae = sum(abs(e) for e in steering_errors) / n
    steering_rmse = math.sqrt(sum(e**2 for e in steering_errors) / n)

    # Brake MAE & RMSE
    brake_mae = sum(abs(e) for e in brake_errors) / n
    brake_rmse = math.sqrt(sum(e**2 for e in brake_errors) / n)

    # Throttle MAE & RMSE
    throttle_mae = sum(abs(e) for e in throttle_errors) / n
    throttle_rmse = math.sqrt(sum(e**2 for e in throttle_errors) / n)

    return [
        Metric(run_id=run_id, metric_name="action_steering_mae", metric_group="action", value=round(steering_mae, 4), aggregation="mae"),
        Metric(run_id=run_id, metric_name="action_steering_rmse", metric_group="action", value=round(steering_rmse, 4), aggregation="rmse"),
        Metric(run_id=run_id, metric_name="action_brake_mae", metric_group="action", value=round(brake_mae, 4), aggregation="mae"),
        Metric(run_id=run_id, metric_name="action_brake_rmse", metric_group="action", value=round(brake_rmse, 4), aggregation="rmse"),
        Metric(run_id=run_id, metric_name="action_throttle_mae", metric_group="action", value=round(throttle_mae, 4), aggregation="mae"),
        Metric(run_id=run_id, metric_name="action_throttle_rmse", metric_group="action", value=round(throttle_rmse, 4), aggregation="rmse"),
        Metric(run_id=run_id, metric_name="action_cumulative_drift", metric_group="action", value=round(cumulative_drift, 4), aggregation="sum"),
    ]
