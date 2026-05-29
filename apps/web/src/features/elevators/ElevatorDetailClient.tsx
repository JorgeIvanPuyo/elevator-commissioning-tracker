"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";

import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";
import { fromDatetimeLocalValue } from "@/lib/hex";
import type {
  CommissioningStep,
  CommissioningStepStatus,
  CommissioningWorkflow,
  CommissioningWorkflowStatus,
  ElevatorFloor,
  ElevatorOperationalDashboard,
  OperationalParameterValue,
  TestRun,
  TestRunStatus,
  TestType,
} from "@/types/api";

const testRunStatusLabels: Record<TestRunStatus, string> = {
  draft: "Borrador",
  in_progress: "En proceso",
  completed: "Completada",
  cancelled: "Cancelada",
};

const workflowStatusLabels: Record<CommissioningWorkflowStatus, string> = {
  not_started: "No iniciado",
  in_progress: "En proceso",
  completed: "Completado",
  blocked: "Bloqueado",
  cancelled: "Cancelado",
};

const stepStatusLabels: Record<CommissioningStepStatus, string> = {
  pending: "Pendiente",
  in_progress: "En proceso",
  completed: "Completado",
  skipped: "Omitido",
  not_applicable: "No aplica",
  blocked: "Bloqueado",
};

const criticalParameterCodes = ["026D", "273", "026E", "274", "026F", "275", "270", "276", "271", "277", "272", "278"];

export function ElevatorDetailClient({ elevatorId }: { elevatorId: string }) {
  const [dashboard, setDashboard] = useState<ElevatorOperationalDashboard | null>(null);
  const [workflow, setWorkflow] = useState<CommissioningWorkflow | null>(null);
  const [floors, setFloors] = useState<ElevatorFloor[]>([]);
  const [testRuns, setTestRuns] = useState<TestRun[]>([]);
  const [testTypes, setTestTypes] = useState<TestType[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isInitializingWorkflow, setIsInitializingWorkflow] = useState(false);
  const [isSavingTestRun, setIsSavingTestRun] = useState(false);
  const [savingStepId, setSavingStepId] = useState<string | null>(null);
  const [savingFloorId, setSavingFloorId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function loadElevator() {
    setIsLoading(true);
    setError(null);
    try {
      const workflowRequest = api.getCommissioningWorkflow(elevatorId).catch((workflowError) => {
        if (workflowError instanceof Error && workflowError.message.toLowerCase().includes("workflow not found")) {
          return null;
        }
        throw workflowError;
      });
      const [dashboardResponse, workflowResponse, floorResponse, testRunResponse, testTypeResponse] = await Promise.all([
        api.getElevatorOperationalDashboard(elevatorId),
        workflowRequest,
        api.listElevatorFloors(elevatorId),
        api.listElevatorTestRuns(elevatorId),
        api.listTestTypes(),
      ]);
      setDashboard(dashboardResponse);
      setWorkflow(workflowResponse);
      setFloors(floorResponse);
      setTestRuns(testRunResponse);
      setTestTypes(testTypeResponse);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "No se pudo cargar el elevador");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadElevator();
  }, [elevatorId]);

  const parametersByCode = useMemo(() => {
    const values = dashboard?.parameter_summary.critical_values ?? [];
    return Object.fromEntries(values.map((value) => [value.parameter_code, value]));
  }, [dashboard?.parameter_summary.critical_values]);

  const blockingStepsIncomplete = workflow?.steps.filter((step) => step.is_blocking && step.status !== "completed") ?? [];
  const loadPrerequisitesComplete = blockingStepsIncomplete.length === 0;

  async function initializeWorkflow() {
    setIsInitializingWorkflow(true);
    setError(null);
    try {
      const initialized = await api.initializeCommissioningWorkflow(elevatorId);
      setWorkflow(initialized);
      await refreshDashboard();
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "No se pudo inicializar el commissioning");
    } finally {
      setIsInitializingWorkflow(false);
    }
  }

  async function refreshDashboard() {
    setDashboard(await api.getElevatorOperationalDashboard(elevatorId));
  }

  async function updateStep(step: CommissioningStep, status: CommissioningStepStatus) {
    setSavingStepId(step.id);
    setError(null);
    try {
      const updated = await api.updateCommissioningStep(step.id, { status });
      setWorkflow((current) => (current ? { ...current, steps: current.steps.map((item) => (item.id === updated.id ? updated : item)) } : current));
      await refreshDashboard();
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "No se pudo actualizar el paso");
    } finally {
      setSavingStepId(null);
    }
  }

  async function updateStepNotes(step: CommissioningStep, notes: string) {
    setSavingStepId(step.id);
    setError(null);
    try {
      const updated = await api.updateCommissioningStep(step.id, { notes: notes || null });
      setWorkflow((current) => (current ? { ...current, steps: current.steps.map((item) => (item.id === updated.id ? updated : item)) } : current));
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "No se pudieron guardar las notas del paso");
    } finally {
      setSavingStepId(null);
    }
  }

  async function updateFloor(floor: ElevatorFloor, payload: Partial<Pick<ElevatorFloor, "label" | "is_served" | "is_leveling_required">>) {
    setSavingFloorId(floor.id);
    setError(null);
    try {
      const updatedFloor = await api.updateElevatorFloor(floor.id, payload);
      setFloors((current) => current.map((item) => (item.id === updatedFloor.id ? updatedFloor : item)));
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "No se pudo actualizar el piso");
    } finally {
      setSavingFloorId(null);
    }
  }

  async function handleCreateTestRun(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formElement = event.currentTarget;
    setIsSavingTestRun(true);
    setError(null);
    const form = new FormData(formElement);

    try {
      await api.createTestRun(elevatorId, {
        test_type_id: String(form.get("test_type_id") || ""),
        technician_name: String(form.get("technician_name") || ""),
        status: String(form.get("status") || "draft") as TestRunStatus,
        started_at: fromDatetimeLocalValue(form.get("started_at")),
        completed_at: fromDatetimeLocalValue(form.get("completed_at")),
        title: String(form.get("title") || "") || null,
        summary: String(form.get("summary") || "") || null,
        notes: String(form.get("notes") || "") || null,
      });
      formElement.reset();
      await loadElevator();
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "No se pudo crear la prueba");
    } finally {
      setIsSavingTestRun(false);
    }
  }

  return (
    <AppShell>
      {isLoading ? <p className="text-sm text-field-muted">Cargando elevador...</p> : null}
      {error ? <p className="border border-field-fail bg-white p-3 text-sm text-field-fail">{error}</p> : null}

      {dashboard ? (
        <>
          <div className="border-b border-field-line pb-4">
            <p className="text-sm font-medium text-field-muted">
              {dashboard.project.name}
              {dashboard.project.location ? ` · ${dashboard.project.location}` : ""}
            </p>
            <div className="mt-2 flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <h2 className="text-3xl font-semibold">{dashboard.elevator.name || dashboard.elevator.code}</h2>
                <p className="mt-1 text-sm text-field-muted">
                  Código {dashboard.elevator.code} · {dashboard.elevator.floor_count} pisos · {dashboard.elevator.controller_model || "Controlador pendiente"}
                </p>
              </div>
              <div className="flex flex-wrap gap-2 text-sm">
                <StatusBadge label={dashboard.elevator.status} tone="neutral" />
                <StatusBadge label={dashboard.workflow ? workflowStatusLabels[dashboard.workflow.status] : "Sin workflow"} tone={dashboard.workflow ? "info" : "warn"} />
                {dashboard.workflow?.technician_name ? <StatusBadge label={dashboard.workflow.technician_name} tone="neutral" /> : null}
              </div>
            </div>
          </div>

          <section className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-5">
            <KpiTile label="Workflow" value={dashboard.workflow ? `${dashboard.workflow.completed_steps}/${dashboard.workflow.total_steps}` : "No iniciado"} detail="pasos completados" />
            <KpiTile label="Pendientes requeridos" value={dashboard.workflow ? String(dashboard.workflow.required_pending_steps) : "-"} detail="incluye validación final" />
            <KpiTile
              label="Bloqueos críticos"
              value={dashboard.workflow ? String(dashboard.workflow.required_blocking_steps_incomplete) : "-"}
              detail="pesacargas, memoria y 110%"
              tone={dashboard.workflow?.required_blocking_steps_incomplete ? "warn" : "ok"}
            />
            <KpiTile
              label="Última prueba"
              value={dashboard.latest_test_run ? dashboard.latest_test_run.name : "Sin pruebas"}
              detail={dashboard.latest_test_run ? testRunStatusLabels[dashboard.latest_test_run.status] : "crear iteración"}
            />
            <KpiTile
              label="Nivelación"
              value={dashboard.leveling_summary ? `${dashboard.leveling_summary.within_final_tolerance_percentage}%` : "Sin datos"}
              detail={dashboard.leveling_summary ? "dentro de tolerancia" : "mediciones pendientes"}
              tone={dashboard.leveling_summary?.overall_status === "critical" ? "fail" : dashboard.leveling_summary?.overall_status === "warning" ? "warn" : "neutral"}
            />
          </section>

          <div className="mt-4 grid gap-4 xl:grid-cols-[minmax(0,1.35fr)_minmax(360px,0.65fr)]">
            <section className="border border-field-line bg-white shadow-panel">
              <div className="flex flex-col gap-3 border-b border-field-line p-4 md:flex-row md:items-center md:justify-between">
                <div>
                  <h3 className="text-lg font-semibold">Workflow guiado de commissioning</h3>
                  <p className="mt-1 text-sm text-field-muted">Orden operativo validado para carga, nivelación fina y cierre técnico.</p>
                </div>
                {!workflow ? (
                  <button className="bg-field-info px-4 py-3 text-sm font-semibold text-white hover:bg-field-ink" disabled={isInitializingWorkflow} onClick={initializeWorkflow}>
                    {isInitializingWorkflow ? "Inicializando..." : "Inicializar proceso de commissioning"}
                  </button>
                ) : null}
              </div>

              {!workflow ? (
                <div className="p-4 text-sm text-field-muted">Este elevador todavía no tiene workflow activo. Inicialízalo para guiar el trabajo de campo paso a paso.</div>
              ) : (
                <div className="divide-y divide-field-line">
                  {workflow.steps.map((step) => (
                    <WorkflowStepRow
                      isDependentBlocked={!loadPrerequisitesComplete && step.sort_order > 3 && step.status !== "completed"}
                      key={step.id}
                      onNotesBlur={updateStepNotes}
                      onStatus={updateStep}
                      saving={savingStepId === step.id}
                      step={step}
                    />
                  ))}
                </div>
              )}
            </section>

            <aside className="grid gap-4">
              <section className="border border-field-line bg-white shadow-panel">
                <PanelHeader title="Parámetros críticos" subtitle={`${dashboard.parameter_summary.warning_count} warnings activos`} />
                <div className="grid grid-cols-2 gap-0 border-t border-field-line">
                  {criticalParameterCodes.map((code) => (
                    <ParameterCell key={code} parameter={parametersByCode[code]} code={code} />
                  ))}
                </div>
                {dashboard.quick_links.latest_test_run_id ? (
                  <Link className="block border-t border-field-line p-3 text-sm font-semibold text-field-info" href={`/test-runs/${dashboard.quick_links.latest_test_run_id}`}>
                    Abrir editor de parámetros
                  </Link>
                ) : (
                  <p className="border-t border-field-line p-3 text-sm text-field-muted">Crea una prueba para capturar parámetros.</p>
                )}
              </section>

              <section className="border border-field-line bg-white shadow-panel">
                <PanelHeader title="Nivelación por zonas" subtitle={dashboard.quick_links.latest_test_run_id ? "Análisis disponible en última prueba" : "Crea una prueba para analizar zonas"} />
                <div className="divide-y divide-field-line text-sm">
                  {["Baja 1-20", "Media 21-41", "Alta 42-62"].map((zone) => (
                    <div className="grid grid-cols-4 gap-2 p-3" key={zone}>
                      <span className="font-semibold">{zone}</span>
                      <span className="text-field-muted">Subida -</span>
                      <span className="text-field-muted">Bajada -</span>
                      <span className="text-field-muted">Delta -</span>
                    </div>
                  ))}
                </div>
                {dashboard.quick_links.latest_test_run_id ? (
                  <Link className="block border-t border-field-line p-3 text-sm font-semibold text-field-info" href={`/test-runs/${dashboard.quick_links.latest_test_run_id}#zone-analysis`}>
                    Abrir análisis por zonas
                  </Link>
                ) : null}
              </section>

              <section className="border border-field-line bg-white shadow-panel">
                <PanelHeader title="Resumen de nivelación" subtitle={dashboard.latest_test_run ? dashboard.latest_test_run.name : "Sin prueba base"} />
                {dashboard.leveling_summary ? (
                  <div className="grid grid-cols-2 gap-0 border-t border-field-line text-sm">
                    <MetricCell label="Cobertura" value={`${dashboard.leveling_summary.coverage_percentage}%`} />
                    <MetricCell label="Tolerancia" value={`${dashboard.leveling_summary.within_final_tolerance_percentage}%`} />
                    <MetricCell label="Mediciones" value={String(dashboard.leveling_summary.measurement_count)} />
                    <MetricCell label="Estado" value={dashboard.leveling_summary.overall_status} />
                  </div>
                ) : (
                  <p className="border-t border-field-line p-3 text-sm text-field-muted">No hay resumen disponible todavía.</p>
                )}
              </section>

              <section className="border border-field-line bg-white shadow-panel">
                <PanelHeader title="Acciones rápidas" subtitle="Trabajo frecuente en campo" />
                <div className="grid gap-2 border-t border-field-line p-3 text-sm">
                  {dashboard.quick_links.latest_test_run_id ? (
                    <Link className="border border-field-line px-3 py-2 font-semibold hover:bg-field-bg" href={`/test-runs/${dashboard.quick_links.latest_test_run_id}`}>
                      Abrir última prueba
                    </Link>
                  ) : null}
                  <a className="border border-field-line px-3 py-2 font-semibold hover:bg-field-bg" href="#new-test-run">
                    Crear TestRun
                  </a>
                  <a className="border border-field-line px-3 py-2 font-semibold hover:bg-field-bg" href="#floors">
                    Editar pisos
                  </a>
                  <Link className="border border-field-line px-3 py-2 font-semibold hover:bg-field-bg" href="/docs">
                    Abrir documentación
                  </Link>
                </div>
              </section>
            </aside>
          </div>

          <section className="mt-4 border border-field-line bg-white shadow-panel" id="new-test-run">
            <div className="border-b border-field-line p-4">
              <h3 className="text-lg font-semibold">Pruebas técnicas</h3>
              <p className="mt-1 text-sm text-field-muted">Iteraciones de carga, parámetros y medición vinculadas al elevador.</p>
            </div>

            <form className="grid gap-3 border-b border-field-line p-4 md:grid-cols-3" onSubmit={handleCreateTestRun}>
              <select className="border border-field-line px-3 py-3 text-sm" name="test_type_id" required>
                <option value="">Tipo de prueba</option>
                {testTypes.map((testType) => (
                  <option key={testType.id} value={testType.id}>
                    {testType.name}
                  </option>
                ))}
              </select>
              <input className="border border-field-line px-3 py-3 text-sm" name="technician_name" placeholder="Responsable" required />
              <select className="border border-field-line px-3 py-3 text-sm" defaultValue="draft" name="status">
                <option value="draft">Borrador</option>
                <option value="in_progress">En proceso</option>
                <option value="completed">Completada</option>
                <option value="cancelled">Cancelada</option>
              </select>
              <input className="border border-field-line px-3 py-3 text-sm" name="started_at" type="datetime-local" />
              <input className="border border-field-line px-3 py-3 text-sm" name="completed_at" type="datetime-local" />
              <input className="border border-field-line px-3 py-3 text-sm" name="title" placeholder="Título" />
              <textarea className="border border-field-line px-3 py-3 text-sm md:col-span-3" name="summary" placeholder="Resumen técnico" rows={2} />
              <textarea className="border border-field-line px-3 py-3 text-sm md:col-span-3" name="notes" placeholder="Notas" rows={2} />
              <button className="bg-field-info px-4 py-3 text-sm font-semibold text-white hover:bg-field-ink md:col-span-3" disabled={isSavingTestRun}>
                {isSavingTestRun ? "Creando..." : "Nueva prueba"}
              </button>
            </form>

            {testRuns.length === 0 ? <p className="p-4 text-sm text-field-muted">No hay pruebas registradas para este elevador.</p> : null}
            <div className="grid gap-0">
              {testRuns.slice(0, 6).map((testRun) => (
                <Link className="grid gap-2 border-b border-field-line p-4 hover:bg-field-bg md:grid-cols-[1fr_120px_180px]" href={`/test-runs/${testRun.id}`} key={testRun.id}>
                  <div>
                    <p className="text-sm font-semibold">{testRun.title || testRun.test_type_name}</p>
                    <p className="mt-1 text-sm text-field-muted">{testRun.summary || testRun.notes || "Sin resumen técnico"}</p>
                  </div>
                  <span className="text-sm">{testRunStatusLabels[testRun.status]}</span>
                  <span className="text-sm text-field-muted">{testRun.technician_name}</span>
                </Link>
              ))}
            </div>
          </section>

          <section className="mt-4 border border-field-line bg-white shadow-panel" id="floors">
            <div className="border-b border-field-line p-4">
              <h3 className="text-lg font-semibold">Pisos del elevador</h3>
              <p className="mt-1 text-sm text-field-muted">Labels y flags editables por elevador.</p>
            </div>
            <div className="max-h-[520px] overflow-y-auto">
              {floors.map((floor) => (
                <div className="grid gap-3 border-b border-field-line p-3 md:grid-cols-[72px_1fr_130px_170px]" key={floor.id}>
                  <span className="text-sm font-semibold">#{floor.sort_order}</span>
                  <input
                    className="border border-field-line px-3 py-2 text-sm"
                    defaultValue={floor.label ?? ""}
                    disabled={savingFloorId === floor.id}
                    onBlur={(event) => {
                      if (event.currentTarget.value !== (floor.label ?? "")) {
                        void updateFloor(floor, { label: event.currentTarget.value });
                      }
                    }}
                  />
                  <label className="flex items-center gap-2 text-sm">
                    <input checked={floor.is_served} disabled={savingFloorId === floor.id} onChange={(event) => void updateFloor(floor, { is_served: event.currentTarget.checked })} type="checkbox" />
                    Atiende
                  </label>
                  <label className="flex items-center gap-2 text-sm">
                    <input
                      checked={floor.is_leveling_required}
                      disabled={savingFloorId === floor.id || !floor.is_served}
                      onChange={(event) => void updateFloor(floor, { is_leveling_required: event.currentTarget.checked })}
                      type="checkbox"
                    />
                    Requiere nivelación
                  </label>
                </div>
              ))}
            </div>
          </section>

          <Link className="mt-4 inline-flex border border-field-line bg-white px-4 py-3 text-sm font-semibold" href={`/projects/${dashboard.project.id}`}>
            Volver al proyecto
          </Link>
        </>
      ) : null}
    </AppShell>
  );
}

function WorkflowStepRow({
  isDependentBlocked,
  onNotesBlur,
  onStatus,
  saving,
  step,
}: {
  isDependentBlocked: boolean;
  onNotesBlur: (step: CommissioningStep, notes: string) => Promise<void>;
  onStatus: (step: CommissioningStep, status: CommissioningStepStatus) => Promise<void>;
  saving: boolean;
  step: CommissioningStep;
}) {
  return (
    <div className={`grid gap-3 p-3 lg:grid-cols-[42px_1fr_220px] ${isDependentBlocked ? "bg-field-bg" : ""}`}>
      <div className="flex h-8 w-8 items-center justify-center border border-field-line text-sm font-semibold">{step.sort_order}</div>
      <div>
        <div className="flex flex-wrap items-center gap-2">
          <StatusBadge label={stepStatusLabels[step.status]} tone={step.status === "completed" ? "ok" : step.status === "blocked" || isDependentBlocked ? "warn" : "neutral"} />
          <p className="text-sm font-semibold">{step.title}</p>
          <span className="text-xs uppercase text-field-muted">{step.is_required ? "Requerido" : "Opcional"}</span>
          {step.is_blocking ? <span className="text-xs uppercase text-field-warn">Bloqueante</span> : null}
        </div>
        <p className="mt-1 text-sm text-field-muted">{step.description}</p>
        {isDependentBlocked ? <p className="mt-1 text-xs font-semibold text-field-warn">Dependiente de pasos críticos de carga.</p> : null}
        {step.completed_at ? <p className="mt-1 text-xs text-field-muted">Completado: {new Date(step.completed_at).toLocaleString()}</p> : null}
      </div>
      <div className="grid gap-2">
        <div className="grid grid-cols-2 gap-2">
          <button className="border border-field-line px-2 py-2 text-xs font-semibold hover:bg-field-bg" disabled={saving} onClick={() => void onStatus(step, "in_progress")}>
            Start
          </button>
          <button className="bg-field-ok px-2 py-2 text-xs font-semibold text-white disabled:opacity-60" disabled={saving} onClick={() => void onStatus(step, "completed")}>
            Complete
          </button>
          <button className="border border-field-line px-2 py-2 text-xs font-semibold hover:bg-field-bg" disabled={saving || step.is_required} onClick={() => void onStatus(step, "not_applicable")}>
            N/A
          </button>
          <button className="border border-field-warn px-2 py-2 text-xs font-semibold text-field-warn" disabled={saving} onClick={() => void onStatus(step, "blocked")}>
            Block
          </button>
        </div>
        <input
          className="border border-field-line px-3 py-2 text-sm"
          defaultValue={step.notes ?? ""}
          disabled={saving}
          onBlur={(event) => {
            if (event.currentTarget.value !== (step.notes ?? "")) {
              void onNotesBlur(step, event.currentTarget.value);
            }
          }}
          placeholder="Notas del paso"
        />
      </div>
    </div>
  );
}

function StatusBadge({ label, tone }: { label: string; tone: "neutral" | "info" | "ok" | "warn" | "fail" }) {
  const toneClass = {
    neutral: "border-field-line bg-white text-field-ink",
    info: "border-field-info bg-white text-field-info",
    ok: "border-field-ok bg-white text-field-ok",
    warn: "border-field-warn bg-white text-field-warn",
    fail: "border-field-fail bg-white text-field-fail",
  }[tone];
  return <span className={`border px-2.5 py-1 text-xs font-semibold ${toneClass}`}>{label}</span>;
}

function KpiTile({ detail, label, tone = "neutral", value }: { detail: string; label: string; tone?: "neutral" | "ok" | "warn" | "fail"; value: string }) {
  const toneClass = {
    neutral: "border-field-line",
    ok: "border-field-ok",
    warn: "border-field-warn",
    fail: "border-field-fail",
  }[tone];
  return (
    <div className={`border bg-white p-3 shadow-panel ${toneClass}`}>
      <p className="text-xs font-semibold uppercase text-field-muted">{label}</p>
      <p className="mt-1 truncate text-lg font-semibold">{value}</p>
      <p className="mt-1 text-xs text-field-muted">{detail}</p>
    </div>
  );
}

function PanelHeader({ subtitle, title }: { subtitle: string; title: string }) {
  return (
    <div className="p-3">
      <h3 className="text-sm font-semibold">{title}</h3>
      <p className="mt-1 text-xs text-field-muted">{subtitle}</p>
    </div>
  );
}

function ParameterCell({ code, parameter }: { code: string; parameter?: OperationalParameterValue }) {
  return (
    <div className="border-b border-r border-field-line p-2 text-sm">
      <p className="font-semibold">{code}</p>
      <p className="mt-1 text-xs text-field-muted">
        {parameter?.hex_value ?? "-"} {parameter?.decimal_value === null || parameter?.decimal_value === undefined ? "" : `(${parameter.decimal_value})`}
      </p>
    </div>
  );
}

function MetricCell({ label, value }: { label: string; value: string }) {
  return (
    <div className="border-b border-r border-field-line p-3">
      <p className="text-xs uppercase text-field-muted">{label}</p>
      <p className="mt-1 font-semibold">{value}</p>
    </div>
  );
}
