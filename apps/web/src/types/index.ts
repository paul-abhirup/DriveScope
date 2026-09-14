export interface Scenario {
  id: string;
  name: string;
  tags: string[];
  total_frames: number;
  fps: number;
  description?: string;
  created_at: string;
  metadata?: {
    conditions?: Record<string, any>;
    hazards?: string[];
    expected_response?: string;
    ego?: Record<string, any>;
  };
}

export interface ScenarioFrame {
  frame_idx: number;
  timestamp_ms: number;
  image_uri: string;
  ego: {
    speed_mps: number;
  };
  ground_truth: {
    action: {
      steering: number;
      brake: number;
      throttle: number;
    };
    hazards: string[];
    ttc_seconds?: number;
  };
}

export interface Experiment {
  id: string;
  name: string;
  scenario_ids: string[];
  model_id: string;
  eval_profile: string;
  perturbation_profile?: any;
  description?: string;
  created_at: string;
  runs_count?: number;
}

export interface Run {
  id: string;
  experiment_id: string;
  scenario_id: string;
  model_id: string;
  status: "CREATED" | "QUEUED" | "RUNNING" | "EVALUATING" | "COMPLETED" | "FAILED" | "CANCELLED";
  progress: number;
  seed: number;
  started_at?: string;
  ended_at?: string;
  manifest_hash?: string;
  error_message?: string;
  perturbation_config?: any;
  created_at?: string;
  metrics_count?: number;
  failures_count?: number;
}

export interface InferenceTrace {
  frame_idx: number;
  timestamp_ms: number;
  image_uri: string;
  ego_speed_mps: number;
  model_reasoning?: string;
  predicted_action: {
    steering: number;
    brake: number;
    throttle: number;
  };
  ground_truth_action: {
    steering: number;
    brake: number;
    throttle: number;
  };
  hazards_present: string[];
  hazards_detected: string[];
  confidence: number;
  latency_ms: number;
  ttc_seconds?: number;
}

export interface Metric {
  metric_name: string;
  metric_group: string;
  value: number;
  aggregation: string;
  version: string;
  metadata?: any;
}

export interface FailureRecord {
  id: number;
  run_id: string;
  frame_idx: number;
  failure_class: string;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  evidence: Record<string, any>;
  detected_at: string;
  resolved: boolean;
  notes?: string;
}

export interface AdapterHealth {
  adapter_id: string;
  status: string;
  model_name: string;
  device: string;
  latency_p50_ms?: number;
  details?: Record<string, any>;
}
