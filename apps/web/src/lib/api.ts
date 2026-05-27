import type {
  Elevator,
  ElevatorCreate,
  ElevatorFloor,
  ElevatorFloorUpdate,
  LevelingDirection,
  LevelingMeasurementBulkItem,
  LevelingMeasurementBulkResponse,
  LevelingTravelType,
  ParameterDefinition,
  Project,
  ProjectCreate,
  TestRun,
  TestRunCreate,
  TestRunParameterValueInput,
  TestRunParameterValuesResponse,
  TestRunProcessStep,
  TestRunProcessStepUpdate,
  TestRunUpdate,
  TestType,
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
  listProjects: () => request<Project[]>("/api/v1/projects"),
  createProject: (payload: ProjectCreate) => request<Project>("/api/v1/projects", { method: "POST", body: payload }),
  getProject: (projectId: string) => request<Project>(`/api/v1/projects/${projectId}`),
  listProjectElevators: (projectId: string) => request<Elevator[]>(`/api/v1/projects/${projectId}/elevators`),
  createElevator: (projectId: string, payload: ElevatorCreate) =>
    request<Elevator>(`/api/v1/projects/${projectId}/elevators`, { method: "POST", body: payload }),
  getElevator: (elevatorId: string) => request<Elevator>(`/api/v1/elevators/${elevatorId}`),
  listElevatorFloors: (elevatorId: string) => request<ElevatorFloor[]>(`/api/v1/elevators/${elevatorId}/floors?limit=300`),
  updateElevatorFloor: (floorId: string, payload: ElevatorFloorUpdate) =>
    request<ElevatorFloor>(`/api/v1/elevator-floors/${floorId}`, { method: "PATCH", body: payload }),
  listTestTypes: () => request<TestType[]>("/api/v1/test-types"),
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
};
