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

export type TestRunParameterValuesResponse = {
  test_run_id: string;
  values: TestRunParameterValue[];
  validation_warnings: string[];
};

export type TestRunParameterValueInput = {
  parameter_code: string;
  hex_value?: string | null;
  source?: string | null;
  notes?: string | null;
};
