import type {
  DashboardOverview,
  CommissioningStep,
  CommissioningStepUpdate,
  CommissioningWorkflow,
  CommissioningWorkflowUpdate,
  Elevator,
  ElevatorCreate,
  ElevatorFloor,
  ElevatorFloorUpdate,
  ElevatorOperationalDashboard,
  ElevatorListItem,
  FlagAdjustmentRecommendations,
  ComparisonCandidate,
  LevelingDirection,
  LevelingMeasurementBulkItem,
  LevelingMeasurementBulkResponse,
  LevelingSummary,
  LevelingTravelType,
  ParameterDefinition,
  Project,
  ProjectCreate,
  ProjectUpdate,
  TestRun,
  TestRunComparison,
  TestRunCreate,
  TestRunListItem,
  TestRunParameterValueInput,
  TestRunParameterValuesResponse,
  TestRunProcessStep,
  TestRunProcessStepUpdate,
  TestRunUpdate,
  TestType,
  ZoneLevelingAnalysis,
} from "@/types/api";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

type RequestOptions = {
  method?: "GET" | "POST" | "PATCH" | "PUT" | "DELETE";
  body?: unknown;
};

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: options.method ?? "GET",
    headers: {
      "Content-Type": "application/json",
    },
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
    cache: "no-store",
  });

  if (!response.ok) {
    let message = `API error ${response.status}`;
    try {
      const errorBody = (await response.json()) as { detail?: string };
      message = errorBody.detail ?? message;
    } catch {
      // Keep the status-based message when the API does not return JSON.
    }
    throw new Error(message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export const api = {
  getDashboardOverview: () => request<DashboardOverview>("/api/v1/dashboard/overview"),
  listProjects: () => request<Project[]>("/api/v1/projects"),
  createProject: (payload: ProjectCreate) => request<Project>("/api/v1/projects", { method: "POST", body: payload }),
  updateProject: (projectId: string, payload: ProjectUpdate) =>
    request<Project>(`/api/v1/projects/${projectId}`, { method: "PATCH", body: payload }),
  deleteProject: (projectId: string) => request<void>(`/api/v1/projects/${projectId}`, { method: "DELETE" }),
  getProject: (projectId: string) => request<Project>(`/api/v1/projects/${projectId}`),
  listProjectElevators: (projectId: string) => request<Elevator[]>(`/api/v1/projects/${projectId}/elevators`),
  listElevators: (params?: { search?: string; status?: string; project_id?: string }) => {
    const searchParams = new URLSearchParams();
    if (params?.search) {
      searchParams.set("search", params.search);
    }
    if (params?.status) {
      searchParams.set("status", params.status);
    }
    if (params?.project_id) {
      searchParams.set("project_id", params.project_id);
    }
    const query = searchParams.toString();
    return request<ElevatorListItem[]>(`/api/v1/elevators${query ? `?${query}` : ""}`);
  },
  createElevator: (projectId: string, payload: ElevatorCreate) =>
    request<Elevator>(`/api/v1/projects/${projectId}/elevators`, { method: "POST", body: payload }),
  getElevator: (elevatorId: string) => request<Elevator>(`/api/v1/elevators/${elevatorId}`),
  getElevatorOperationalDashboard: (elevatorId: string) =>
    request<ElevatorOperationalDashboard>(`/api/v1/elevators/${elevatorId}/operational-dashboard`),
  getCommissioningWorkflow: (elevatorId: string) => request<CommissioningWorkflow>(`/api/v1/elevators/${elevatorId}/commissioning-workflow`),
  initializeCommissioningWorkflow: (elevatorId: string) =>
    request<CommissioningWorkflow>(`/api/v1/elevators/${elevatorId}/commissioning-workflow/initialize`, { method: "POST" }),
  updateCommissioningWorkflow: (workflowId: string, payload: CommissioningWorkflowUpdate) =>
    request<CommissioningWorkflow>(`/api/v1/commissioning-workflows/${workflowId}`, { method: "PATCH", body: payload }),
  updateCommissioningStep: (stepId: string, payload: CommissioningStepUpdate) =>
    request<CommissioningStep>(`/api/v1/commissioning-steps/${stepId}`, { method: "PATCH", body: payload }),
  listElevatorFloors: (elevatorId: string) => request<ElevatorFloor[]>(`/api/v1/elevators/${elevatorId}/floors?limit=300`),
  updateElevatorFloor: (floorId: string, payload: ElevatorFloorUpdate) =>
    request<ElevatorFloor>(`/api/v1/elevator-floors/${floorId}`, { method: "PATCH", body: payload }),
  listTestTypes: () => request<TestType[]>("/api/v1/test-types"),
  listTestRuns: (params?: { search?: string; status?: string; test_type_code?: string }) => {
    const searchParams = new URLSearchParams();
    if (params?.search) {
      searchParams.set("search", params.search);
    }
    if (params?.status) {
      searchParams.set("status", params.status);
    }
    if (params?.test_type_code) {
      searchParams.set("test_type_code", params.test_type_code);
    }
    const query = searchParams.toString();
    return request<TestRunListItem[]>(`/api/v1/test-runs${query ? `?${query}` : ""}`);
  },
  listElevatorTestRuns: (elevatorId: string) => request<TestRun[]>(`/api/v1/elevators/${elevatorId}/test-runs`),
  createTestRun: (elevatorId: string, payload: TestRunCreate) =>
    request<TestRun>(`/api/v1/elevators/${elevatorId}/test-runs`, { method: "POST", body: payload }),
  getTestRun: (testRunId: string) => request<TestRun>(`/api/v1/test-runs/${testRunId}`),
  updateTestRun: (testRunId: string, payload: TestRunUpdate) =>
    request<TestRun>(`/api/v1/test-runs/${testRunId}`, { method: "PATCH", body: payload }),
  listParameterDefinitions: () => request<ParameterDefinition[]>("/api/v1/parameter-definitions?limit=200"),
  listTestRunParameters: (testRunId: string) => request<TestRunParameterValuesResponse>(`/api/v1/test-runs/${testRunId}/parameters`),
  saveTestRunParameters: (testRunId: string, values: TestRunParameterValueInput[]) =>
    request<TestRunParameterValuesResponse>(`/api/v1/test-runs/${testRunId}/parameters`, {
      method: "PUT",
      body: { values },
    }),
  listTestRunProcessSteps: (testRunId: string) => request<TestRunProcessStep[]>(`/api/v1/test-runs/${testRunId}/process-steps`),
  updateTestRunProcessStep: (processStepId: string, payload: TestRunProcessStepUpdate) =>
    request<TestRunProcessStep>(`/api/v1/test-run-process-steps/${processStepId}`, { method: "PATCH", body: payload }),
  listLevelingMeasurements: (testRunId: string, direction?: LevelingDirection, travelType?: LevelingTravelType) => {
    const params = new URLSearchParams();
    if (direction) {
      params.set("direction", direction);
    }
    if (travelType) {
      params.set("travel_type", travelType);
    }
    const query = params.toString();
    return request<LevelingMeasurementBulkResponse>(`/api/v1/test-runs/${testRunId}/leveling-measurements${query ? `?${query}` : ""}`);
  },
  saveLevelingMeasurements: (testRunId: string, items: LevelingMeasurementBulkItem[]) =>
    request<LevelingMeasurementBulkResponse>(`/api/v1/test-runs/${testRunId}/leveling-measurements/bulk`, {
      method: "PUT",
      body: { items },
    }),
  deleteLevelingMeasurement: (measurementId: string) => request<void>(`/api/v1/leveling-measurements/${measurementId}`, { method: "DELETE" }),
  getLevelingSummary: (testRunId: string) => request<LevelingSummary>(`/api/v1/test-runs/${testRunId}/leveling-summary`),
  getZoneLevelingAnalysis: (testRunId: string) => request<ZoneLevelingAnalysis>(`/api/v1/test-runs/${testRunId}/zone-leveling-analysis`),
  getFlagAdjustmentRecommendations: (testRunId: string) =>
    request<FlagAdjustmentRecommendations>(`/api/v1/test-runs/${testRunId}/flag-adjustment-recommendations`),
  listComparisonCandidates: (testRunId: string) => request<ComparisonCandidate[]>(`/api/v1/test-runs/${testRunId}/comparison-candidates`),
  compareTestRuns: (testRunId: string, baselineTestRunId: string) =>
    request<TestRunComparison>(`/api/v1/test-runs/${testRunId}/comparison?baseline_test_run_id=${baselineTestRunId}`),
};
