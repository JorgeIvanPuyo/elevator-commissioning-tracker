export type Project = {
  id: string;
  name: string;
  client_name: string | null;
  location: string | null;
  description: string | null;
  total_elevators: number | null;
  default_floor_count: number;
  status: string;
  created_at: string;
  updated_at: string;
};

export type ProjectCreate = {
  name: string;
  client_name?: string;
  location?: string;
  total_elevators?: number;
  default_floor_count?: number;
};

export type ProjectUpdate = {
  name?: string;
  client_name?: string | null;
  location?: string | null;
  description?: string | null;
  total_elevators?: number | null;
  default_floor_count?: number;
  status?: string;
};

export type Elevator = {
  id: string;
  project_id: string;
  code: string;
  name: string | null;
  floor_count: number;
  controller_model: string | null;
  machine_room: string | null;
  notes: string | null;
  status: string;
  created_at: string;
  updated_at: string;
};

export type ElevatorListItem = {
  id: string;
  code: string;
  name: string | null;
  status: string;
  floor_count: number;
  project_id: string;
  project_name: string;
  created_at: string;
  updated_at: string;
};

export type ElevatorCreate = {
  code: string;
  name?: string;
  floor_count?: number;
  controller_model?: string;
  machine_room?: string;
};

export type TestType = {
  id: string;
  code: string;
  name: string;
  description: string | null;
  documentation_slug: string | null;
  is_active: boolean;
  sort_order: number;
  created_at: string;
  updated_at: string;
};

export type ElevatorFloor = {
  id: string;
  elevator_id: string;
  sort_order: number;
  label: string | null;
  is_served: boolean;
  is_leveling_required: boolean;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type ElevatorFloorUpdate = {
  sort_order?: number;
  label?: string | null;
  is_served?: boolean;
  is_leveling_required?: boolean;
  notes?: string | null;
};

export type TestRunStatus = "draft" | "in_progress" | "completed" | "cancelled";

export type TestRun = {
  id: string;
  elevator_id: string;
  test_type_id: string;
  test_type_code: string;
  test_type_name: string;
  status: TestRunStatus;
  technician_name: string;
  started_at: string | null;
  completed_at: string | null;
  title: string | null;
  summary: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type TestRunListItem = {
  id: string;
  title: string | null;
  name: string;
  status: TestRunStatus;
  test_type_id: string;
  test_type_code: string;
  test_type_name: string;
  elevator_id: string;
  elevator_code: string;
  project_id: string;
  project_name: string;
  responsible_technician: string;
  created_at: string;
  updated_at: string;
};

export type TestRunCreate = {
  test_type_id: string;
  status?: TestRunStatus;
  technician_name: string;
  started_at?: string | null;
  completed_at?: string | null;
  title?: string | null;
  summary?: string | null;
  notes?: string | null;
};

export type TestRunUpdate = Partial<TestRunCreate>;

export type ParameterDefinition = {
  id: string;
  code: string;
  name: string;
  description: string | null;
  category: string | null;
  zone: string | null;
  direction: string | null;
  bound_type: string | null;
  pair_code: string | null;
  is_editable: boolean;
  sort_order: number;
  created_at: string;
  updated_at: string;
};

export type TestRunParameterValue = {
  id: string;
  test_run_id: string;
  parameter_definition_id: string;
  parameter_code: string;
  parameter_name: string;
  hex_value: string | null;
  decimal_value: number | null;
  source: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type ParameterValidationWarning = {
  type: string;
  parameter_code: string;
  paired_parameter_code: string;
  message: string;
  severity: "warning";
};

export type TestRunParameterValuesResponse = {
  test_run_id: string;
  values: TestRunParameterValue[];
  validation_warnings: ParameterValidationWarning[];
};

export type TestRunParameterValueInput = {
  parameter_code: string;
  hex_value?: string | null;
  source?: string | null;
  notes?: string | null;
};

export type TestRunProcessStep = {
  id: string;
  test_run_id: string;
  code: string;
  name: string;
  description: string | null;
  is_completed: boolean;
  completed_at: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type TestRunProcessStepUpdate = {
  is_completed?: boolean;
  completed_at?: string | null;
  notes?: string | null;
};

export type LevelingDirection = "up" | "down";
export type LevelingTravelType = "short" | "long";
export type LevelingMeasurementStage = "zone_tuning" | "floor_by_floor" | "final_validation";

export type LevelingMeasurement = {
  id: string;
  test_run_id: string;
  origin_floor_id: string;
  destination_floor_id: string;
  direction: LevelingDirection;
  travel_type: LevelingTravelType;
  measurement_stage: LevelingMeasurementStage;
  landing_mm: number | null;
  final_mm: number | null;
  did_relevel: boolean;
  renivelation_occurred: boolean;
  effective_final_mm: number | null;
  is_final_within_tolerance: boolean | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type LevelingMeasurementBulkItem = {
  origin_floor_id: string;
  destination_floor_id: string;
  direction: LevelingDirection;
  travel_type: LevelingTravelType;
  measurement_stage?: LevelingMeasurementStage;
  landing_mm?: number | null;
  final_mm?: number | null;
  notes?: string | null;
};

export type LevelingMeasurementSummary = {
  total: number;
  with_values: number;
  within_tolerance: number;
  outside_tolerance: number;
  within_tolerance_percentage: number;
};

export type LevelingMeasurementBulkResponse = {
  items: LevelingMeasurement[];
  summary: LevelingMeasurementSummary;
};

export type LevelingStatus = "pending" | "ok" | "warning" | "critical" | "not_required";

export type LevelingFinalValues = {
  short_up: number | null;
  short_down: number | null;
  long_up: number | null;
  long_down: number | null;
};

export type LevelingHysteresisSummary = {
  short_up_vs_down_mm: number | null;
  short_up_vs_down_ok: boolean | null;
  long_up_vs_down_mm: number | null;
  long_up_vs_down_ok: boolean | null;
  short_vs_long_up_mm: number | null;
  short_vs_long_up_ok: boolean | null;
  short_vs_long_down_mm: number | null;
  short_vs_long_down_ok: boolean | null;
  max_difference_mm: number | null;
  overall_ok: boolean | null;
};

export type LevelingFloorSummary = {
  floor_id: string;
  floor_label: string;
  sort_order: number;
  is_served: boolean;
  is_leveling_required: boolean;
  measurements_count: number;
  final_values_mm: LevelingFinalValues;
  within_final_tolerance: boolean | null;
  has_out_of_tolerance_measurement: boolean;
  has_renivelation: boolean;
  renivelation_ok: boolean | null;
  hysteresis: LevelingHysteresisSummary;
  status: LevelingStatus;
};

export type LevelingSummary = {
  test_run_id: string;
  elevator_id: string;
  measurement_count: number;
  required_floor_count: number;
  measured_required_floor_count: number;
  coverage_percentage: number;
  within_final_tolerance_count: number;
  within_final_tolerance_percentage: number;
  out_of_final_tolerance_count: number;
  renivelation_count: number;
  acceptable_renivelation_count: number;
  acceptable_renivelation_percentage: number;
  hysteresis_pairs_count: number;
  hysteresis_ok_count: number;
  hysteresis_ok_percentage: number;
  overall_status: LevelingStatus;
  floor_summaries: LevelingFloorSummary[];
};

export type ZoneLevelingStatus = "ok" | "warning" | "missing_measurements" | "missing_parameters";

export type ZoneLevelingParameterSuggestion = {
  code: string;
  current_hex: string | null;
  current_decimal: number | null;
  suggested_decimal: number | null;
  suggested_hex: string | null;
};

export type ZoneLevelingWarning = {
  type: string;
  severity: "warning" | "critical";
  message: string;
};

export type ZoneLevelingEntry = {
  zone: "low" | "mid" | "high";
  direction: LevelingDirection;
  floor_range_label: string;
  measurement_count: number;
  average_landing_mm: number | null;
  rounded_delta_decimal: number | null;
  min_parameter: ZoneLevelingParameterSuggestion;
  max_parameter: ZoneLevelingParameterSuggestion;
  current_window_decimal: number | null;
  suggested_window_decimal: number | null;
  warnings: ZoneLevelingWarning[];
  status: ZoneLevelingStatus;
};

export type ZoneLevelingAnalysis = {
  test_run_id: string;
  elevator_id: string;
  zones: ZoneLevelingEntry[];
  global_warnings: ZoneLevelingWarning[];
};

export type FlagAdjustmentStatus = "ok" | "requires_adjustment" | "partial_data" | "missing_data" | "not_required";

export type FlagAdjustmentSummary = {
  total_required_floors: number;
  floors_with_complete_data: number;
  floors_within_tolerance: number;
  floors_requiring_flag_adjustment: number;
  floors_missing_data: number;
  floors_partial_data: number;
  max_abs_recommended_movement_mm: number | null;
};

export type FlagAdjustmentRow = {
  floor_id: string;
  floor_label: string;
  sort_order: number;
  down_final_mm: number | null;
  up_final_mm: number | null;
  average_final_mm: number | null;
  recommended_flag_movement_mm: number | null;
  status: FlagAdjustmentStatus;
  within_tolerance: boolean | null;
  notes: string[];
};

export type FlagAdjustmentRecommendations = {
  test_run_id: string;
  elevator_id: string;
  tolerance_mm: number;
  summary: FlagAdjustmentSummary;
  rows: FlagAdjustmentRow[];
};

export type FinalValidationStatus = "ok" | "out_of_tolerance" | "partial_data" | "missing_data" | "not_required";

export type FinalValidationSummaryMetrics = {
  total_required_floors: number;
  floors_with_complete_data: number;
  floors_within_tolerance: number;
  floors_out_of_tolerance: number;
  floors_missing_data: number;
  floors_partial_data: number;
  completion_percent: number;
  within_tolerance_percent: number;
  max_abs_final_mm: number | null;
};

export type FinalValidationRow = {
  floor_id: string;
  floor_label: string;
  sort_order: number;
  down_final_mm: number | null;
  up_final_mm: number | null;
  status: FinalValidationStatus;
  within_tolerance: boolean | null;
};

export type FinalValidationSummary = {
  test_run_id: string;
  elevator_id: string;
  tolerance_mm: number;
  fhm_completed: boolean;
  fhm_step_status: CommissioningStepStatus | null;
  summary: FinalValidationSummaryMetrics;
  rows: FinalValidationRow[];
};

export type ComparisonTrend = "improved" | "worsened" | "mixed" | "unchanged" | "not_comparable";
export type FloorComparisonTrend = ComparisonTrend | "newly_measured" | "missing_current";

export type ComparisonTestRunBrief = {
  id: string;
  title: string | null;
  name: string;
  test_type_code: string;
  test_type_name: string;
  status: TestRunStatus;
  technician_name: string;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
};

export type ComparisonCandidate = ComparisonTestRunBrief & {
  coverage_percentage: number;
  within_final_tolerance_percentage: number;
  acceptable_renivelation_percentage: number;
};

export type ComparisonMetric = {
  metric: string;
  label: string;
  baseline_value: number | null;
  current_value: number | null;
  delta: number | null;
  trend: ComparisonTrend;
};

export type FloorComparison = {
  floor_id: string;
  floor_label: string;
  baseline_status: LevelingStatus | "not_comparable";
  current_status: LevelingStatus | "not_comparable";
  baseline_final_mm: number | null;
  current_final_mm: number | null;
  absolute_delta_mm: number | null;
  trend: FloorComparisonTrend;
};

export type ParameterComparison = {
  parameter_code: string;
  name: string;
  baseline_hex_value: string | null;
  baseline_decimal_value: number | null;
  current_hex_value: string | null;
  current_decimal_value: number | null;
  decimal_delta: number | null;
  changed: boolean;
  warning: string | null;
};

export type TestRunComparison = {
  baseline_test_run: ComparisonTestRunBrief;
  current_test_run: ComparisonTestRunBrief;
  global_metrics: ComparisonMetric[];
  floor_comparisons: FloorComparison[];
  parameter_comparisons: ParameterComparison[];
  overall_trend: ComparisonTrend;
  summary_text: string;
};

export type CommissioningWorkflowStatus = "not_started" | "in_progress" | "completed" | "blocked" | "cancelled";
export type CommissioningStepStatus = "pending" | "in_progress" | "completed" | "skipped" | "not_applicable" | "blocked";

export type CommissioningStep = {
  id: string;
  workflow_id: string;
  code: string;
  title: string;
  description: string | null;
  status: CommissioningStepStatus;
  is_required: boolean;
  is_blocking: boolean;
  sort_order: number;
  completed_at: string | null;
  technician_name: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type CommissioningWorkflow = {
  id: string;
  elevator_id: string;
  status: CommissioningWorkflowStatus;
  technician_name: string | null;
  started_at: string | null;
  completed_at: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  steps: CommissioningStep[];
};

export type CommissioningWorkflowUpdate = {
  status?: CommissioningWorkflowStatus;
  technician_name?: string | null;
  notes?: string | null;
};

export type CommissioningStepUpdate = {
  status?: CommissioningStepStatus;
  technician_name?: string | null;
  notes?: string | null;
  completed_at?: string | null;
};

export type OperationalWorkflowSummary = {
  id: string;
  status: CommissioningWorkflowStatus;
  technician_name: string | null;
  total_steps: number;
  completed_steps: number;
  required_steps: number;
  required_pending_steps: number;
  required_blocking_steps_incomplete: number;
  progress_percentage: number;
};

export type OperationalLatestTestRun = {
  id: string;
  title: string | null;
  name: string;
  status: TestRunStatus;
  test_type_code: string;
  test_type_name: string;
  technician_name: string;
  created_at: string;
  updated_at: string;
};

export type OperationalLevelingSummary = {
  test_run_id: string;
  measurement_count: number;
  required_floor_count: number;
  measured_required_floor_count: number;
  coverage_percentage: number;
  within_final_tolerance_percentage: number;
  overall_status: LevelingStatus;
};

export type OperationalParameterValue = {
  parameter_code: string;
  parameter_name: string;
  hex_value: string | null;
  decimal_value: number | null;
};

export type OperationalParameterSummary = {
  latest_test_run_id: string | null;
  warning_count: number;
  critical_values: OperationalParameterValue[];
};

export type ElevatorOperationalDashboard = {
  elevator: {
    id: string;
    project_id: string;
    code: string;
    name: string | null;
    status: string;
    floor_count: number;
    controller_model: string | null;
    machine_room: string | null;
  };
  project: {
    id: string;
    name: string;
    client_name: string | null;
    location: string | null;
  };
  workflow: OperationalWorkflowSummary | null;
  latest_test_run: OperationalLatestTestRun | null;
  leveling_summary: OperationalLevelingSummary | null;
  parameter_summary: OperationalParameterSummary;
  quick_links: {
    latest_test_run_id: string | null;
    project_id: string;
    elevator_id: string;
  };
};

export type DashboardLatestProject = {
  id: string;
  name: string;
  status: string;
  elevators_count: number;
  created_at: string;
  updated_at: string;
};

export type DashboardLatestTestRun = {
  id: string;
  title: string | null;
  name: string;
  test_type: string;
  status: TestRunStatus;
  elevator_id: string;
  elevator_code: string;
  project_id: string;
  project_name: string;
  responsible_technician: string;
  created_at: string;
  updated_at: string;
};

export type DashboardOverview = {
  projects_count: number;
  active_projects_count: number;
  elevators_count: number;
  test_runs_count: number;
  completed_test_runs_count: number;
  in_progress_test_runs_count: number;
  draft_test_runs_count: number;
  latest_test_runs: DashboardLatestTestRun[];
  latest_projects: DashboardLatestProject[];
};
