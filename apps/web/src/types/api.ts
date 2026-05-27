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

export type LevelingMeasurement = {
  id: string;
  test_run_id: string;
  origin_floor_id: string;
  destination_floor_id: string;
  direction: LevelingDirection;
  travel_type: LevelingTravelType;
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
