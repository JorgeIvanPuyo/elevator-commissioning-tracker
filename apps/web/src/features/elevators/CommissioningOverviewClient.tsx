"use client";

import Link from "next/link";
import type { ReactNode } from "react";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";
import type { CommissioningOverview, CommissioningOverviewStatus, CommissioningStepStatus, CommissioningWorkflowStatus, TestRunStatus } from "@/types/api";

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

const testRunStatusLabels: Record<TestRunStatus, string> = {
  draft: "Borrador",
  in_progress: "En proceso",
  completed: "Completada",
  cancelled: "Cancelada",
};

const overviewTone: Record<CommissioningOverviewStatus, "neutral" | "info" | "ok" | "warn" | "fail"> = {
  not_started: "neutral",
  in_progress: "info",
  needs_attention: "warn",
  ready_to_close: "ok",
  completed: "ok",
};

export function CommissioningOverviewClient({ elevatorId }: { elevatorId: string }) {
  const [overview, setOverview] = useState<CommissioningOverview | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadOverview() {
      setIsLoading(true);
      setError(null);
      try {
        setOverview(await api.getCommissioningOverview(elevatorId));
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : "No se pudo cargar el resumen de commissioning");
      } finally {
        setIsLoading(false);
      }
    }

    void loadOverview();
  }, [elevatorId]);

  return (
    <AppShell>
      {isLoading ? <p className="text-sm text-field-muted">Cargando resumen...</p> : null}
      {error ? <p className="border border-field-fail bg-white p-3 text-sm text-field-fail">{error}</p> : null}

      {overview ? (
        <div className="space-y-4">
          <header className="border-b border-field-line pb-4">
            <p className="text-sm font-medium text-field-muted">Proyecto: {overview.elevator.project_name}</p>
            <div className="mt-2 flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <h2 className="text-3xl font-semibold">
                  {overview.elevator.name || overview.elevator.code} - Resumen de commissioning
                </h2>
                <p className="mt-1 text-sm text-field-muted">Código {overview.elevator.code} · Estado del elevador: {overview.elevator.status}</p>
              </div>
              <StatusBadge label={`Estado general: ${overview.overall_status.label}`} tone={overviewTone[overview.overall_status.status]} />
            </div>
          </header>

          <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-6">
            <KpiTile
              detail={overview.workflow ? `${overview.workflow.completed_steps}/${overview.workflow.total_steps} pasos requeridos` : "workflow pendiente"}
              label="Progreso del proceso"
              tone={overview.workflow ? "info" : "warn"}
              value={overview.workflow ? `${overview.workflow.progress_percent}%` : "No iniciado"}
            />
            <KpiTile
              detail={overview.load_readiness.ready_for_leveling ? "prerrequisitos completos" : "revisar carga"}
              label="Pesacargas y carga"
              tone={overview.load_readiness.ready_for_leveling ? "ok" : "warn"}
              value={overview.load_readiness.ready_for_leveling ? "Listo" : "Pendiente"}
            />
            <KpiTile
              detail={`${overview.parameter_matrix.warning_windows} warnings · ${overview.parameter_matrix.missing_windows} sin datos`}
              label="Parámetros"
              tone={overview.parameter_matrix.warning_windows || overview.parameter_matrix.missing_windows ? "warn" : "ok"}
              value={`${overview.parameter_matrix.ok_windows}/6 OK`}
            />
            <KpiTile
              detail={overview.zone_analysis.available ? `${overview.zone_analysis.warnings_count} warnings` : "sin mediciones"}
              label="Análisis por zonas"
              tone={overview.zone_analysis.warnings_count ? "warn" : overview.zone_analysis.available ? "ok" : "neutral"}
              value={overview.zone_analysis.max_abs_average_landing_mm === null ? "-" : `${overview.zone_analysis.max_abs_average_landing_mm} mm`}
            />
            <KpiTile
              detail={`${overview.flag_adjustments.floors_missing_data} sin datos`}
              label="Movimiento de banderas"
              tone={overview.flag_adjustments.floors_requiring_adjustment ? "warn" : overview.flag_adjustments.available ? "ok" : "neutral"}
              value={`${overview.flag_adjustments.floors_requiring_adjustment} ajuste`}
            />
            <KpiTile
              detail={`FHM ${overview.final_validation.fhm_completed ? "completado" : "pendiente"}`}
              label="FHM y validación final"
              tone={overview.final_validation.ready_to_close ? "ok" : overview.final_validation.available ? "warn" : "neutral"}
              value={`${overview.final_validation.within_tolerance_percent}%`}
            />
          </section>

          <section className="grid gap-4 xl:grid-cols-[minmax(0,1.25fr)_minmax(340px,0.75fr)]">
            <div className="space-y-4">
              <Panel title="Checklist de workflow guiado" subtitle={overview.workflow ? workflowStatusLabels[overview.workflow.status] : "Sin workflow inicializado"}>
                {overview.workflow ? (
                  <div className="divide-y divide-field-line">
                    {overview.workflow.steps.map((step) => (
                      <div className="grid gap-2 p-3 md:grid-cols-[1fr_130px_130px]" key={step.code}>
                        <div>
                          <div className="flex flex-wrap items-center gap-2">
                            <StatusBadge label={stepStatusLabels[step.status]} tone={step.status === "completed" ? "ok" : step.status === "blocked" ? "warn" : "neutral"} />
                            <p className="text-sm font-semibold">{step.title}</p>
                            <span className="text-xs uppercase text-field-muted">{step.is_required ? "Requerido" : "Opcional"}</span>
                          </div>
                          {step.notes ? <p className="mt-1 text-xs text-field-muted">{step.notes}</p> : null}
                        </div>
                        <span className="text-sm text-field-muted">{step.completed_at ? new Date(step.completed_at).toLocaleDateString() : "-"}</span>
                        <span className="text-sm text-field-muted">{step.code}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <EmptyState actionHref={`/elevators/${overview.elevator.id}`} actionLabel="Inicializar workflow" text="Este elevador todavía no tiene workflow activo." />
                )}
              </Panel>

              <Panel title="Parámetros de nivelación fina" subtitle="Estado técnico de ventanas MIN/MAX 026D-278">
                <div className="grid gap-0 border-t border-field-line md:grid-cols-3">
                  <MetricCell label="Ventanas OK" value={String(overview.parameter_matrix.ok_windows)} />
                  <MetricCell label="Warnings" value={String(overview.parameter_matrix.warning_windows)} />
                  <MetricCell label="Sin datos" value={String(overview.parameter_matrix.missing_windows)} />
                </div>
                {overview.parameter_matrix.most_critical_warning ? (
                  <p className="border-t border-field-line p-3 text-sm text-field-warn">{overview.parameter_matrix.most_critical_warning}</p>
                ) : (
                  <p className="border-t border-field-line p-3 text-sm text-field-muted">Sin advertencias críticas de ventanas en la última prueba.</p>
                )}
                {overview.latest_test_run ? (
                  <div className="grid gap-2 border-t border-field-line p-3 text-sm md:grid-cols-2">
                    <Link className="border border-field-line px-3 py-2 font-semibold hover:bg-field-bg" href={`/test-runs/${overview.latest_test_run.id}#parameter-matrix`}>
                      Ver matriz de parámetros
                    </Link>
                    <Link className="border border-field-line px-3 py-2 font-semibold hover:bg-field-bg" href={`/test-runs/${overview.latest_test_run.id}#zone-analysis`}>
                      Ver análisis por zonas
                    </Link>
                  </div>
                ) : null}
              </Panel>

              <Panel title="Movimiento de banderas" subtitle={overview.flag_adjustments.available ? "Resumen calculado desde última prueba" : "Sin recomendaciones calculadas"}>
                <div className="grid gap-0 border-t border-field-line md:grid-cols-4">
                  <MetricCell label="Requieren ajuste" value={String(overview.flag_adjustments.floors_requiring_adjustment)} />
                  <MetricCell label="OK" value={String(overview.flag_adjustments.floors_ok)} />
                  <MetricCell label="Sin datos" value={String(overview.flag_adjustments.floors_missing_data)} />
                  <MetricCell label="Máximo" value={overview.flag_adjustments.max_abs_recommended_movement_mm === null ? "-" : `${overview.flag_adjustments.max_abs_recommended_movement_mm} mm`} />
                </div>
                {overview.latest_test_run ? (
                  <Link className="block border-t border-field-line p-3 text-sm font-semibold text-field-info" href={`/test-runs/${overview.latest_test_run.id}#flag-adjustments`}>
                    Ver recomendaciones de banderas
                  </Link>
                ) : null}
              </Panel>
            </div>

            <aside className="space-y-4">
              <Panel title="Pesacargas y carga" subtitle={overview.load_readiness.ready_for_leveling ? "Listo para nivelación" : "Pendiente antes de nivelar"}>
                <ChecklistItem done={overview.load_readiness.mechanical_calibration_completed} label="Calibración mecánica de pesacargas" />
                <ChecklistItem done={overview.load_readiness.zero_full_memory_completed} label="Escritura 0% / 100% en memoria" />
                <ChecklistItem done={overview.load_readiness.overload_110_completed} label="Prueba 110% de carga" />
                {overview.load_readiness.warnings.length ? (
                  <div className="border-t border-field-line p-3 text-xs text-field-warn">
                    {overview.load_readiness.warnings.map((warning) => (
                      <p key={warning}>{warning}</p>
                    ))}
                  </div>
                ) : null}
              </Panel>

              <Panel title="Prueba más reciente" subtitle={overview.latest_test_run ? testRunStatusLabels[overview.latest_test_run.status] : "Sin TestRun"}>
                {overview.latest_test_run ? (
                  <div className="border-t border-field-line p-3 text-sm">
                    <p className="font-semibold">{overview.latest_test_run.name}</p>
                    <p className="mt-1 text-field-muted">Responsable: {overview.latest_test_run.technician_name}</p>
                    <p className="mt-1 text-field-muted">Creada: {new Date(overview.latest_test_run.created_at).toLocaleString()}</p>
                    <Link className="mt-3 inline-flex border border-field-line px-3 py-2 font-semibold hover:bg-field-bg" href={`/test-runs/${overview.latest_test_run.id}`}>
                      Ver prueba más reciente
                    </Link>
                  </div>
                ) : (
                  <EmptyState actionHref={`/elevators/${overview.elevator.id}#new-test-run`} actionLabel="Crear prueba" text="Aún no hay prueba técnica para consolidar parámetros y mediciones." />
                )}
              </Panel>

              <Panel title="FHM y validación final" subtitle={overview.final_validation.ready_to_close ? "Listo para cierre técnico" : "Validación pendiente o con observaciones"}>
                <div className="grid gap-0 border-t border-field-line md:grid-cols-2 xl:grid-cols-1">
                  <MetricCell label="FHM" value={overview.final_validation.fhm_completed ? "Completado" : "Pendiente"} />
                  <MetricCell label="Dentro de tolerancia" value={`${overview.final_validation.within_tolerance_percent}%`} />
                  <MetricCell label="Fuera de tolerancia" value={String(overview.final_validation.floors_out_of_tolerance)} />
                  <MetricCell label="Sin datos" value={String(overview.final_validation.floors_missing_data)} />
                </div>
                {overview.latest_test_run ? (
                  <Link className="block border-t border-field-line p-3 text-sm font-semibold text-field-info" href={`/test-runs/${overview.latest_test_run.id}#final-validation`}>
                    Ver validación final
                  </Link>
                ) : null}
              </Panel>

              <Panel title={overview.final_validation.ready_to_close ? "Listo para cierre técnico" : "Pendiente antes de cierre"} subtitle={overview.overall_status.label}>
                {overview.overall_status.reasons.length ? (
                  <ul className="list-disc space-y-1 border-t border-field-line p-4 pl-7 text-sm text-field-warn">
                    {overview.overall_status.reasons.map((reason) => (
                      <li key={reason}>{reason}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="border-t border-field-line p-3 text-sm text-field-ok">El elevador cumple las condiciones actuales para cierre técnico.</p>
                )}
              </Panel>
            </aside>
          </section>

          <Link className="inline-flex border border-field-line bg-white px-4 py-3 text-sm font-semibold hover:bg-field-bg" href={`/elevators/${overview.elevator.id}`}>
            Volver al dashboard del elevador
          </Link>
        </div>
      ) : null}
    </AppShell>
  );
}

function Panel({ children, subtitle, title }: { children: ReactNode; subtitle: string; title: string }) {
  return (
    <section className="border border-field-line bg-white shadow-panel">
      <div className="p-3">
        <h3 className="text-sm font-semibold">{title}</h3>
        <p className="mt-1 text-xs text-field-muted">{subtitle}</p>
      </div>
      {children}
    </section>
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

function KpiTile({
  detail,
  label,
  tone = "neutral",
  value,
}: {
  detail: string;
  label: string;
  tone?: "neutral" | "info" | "ok" | "warn" | "fail";
  value: string;
}) {
  const toneClass = {
    neutral: "border-field-line",
    info: "border-field-info",
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

function MetricCell({ label, value }: { label: string; value: string }) {
  return (
    <div className="border-b border-r border-field-line p-3">
      <p className="text-xs uppercase text-field-muted">{label}</p>
      <p className="mt-1 font-semibold">{value}</p>
    </div>
  );
}

function ChecklistItem({ done, label }: { done: boolean; label: string }) {
  return (
    <div className="flex items-center justify-between gap-3 border-t border-field-line p-3 text-sm">
      <span>{label}</span>
      <StatusBadge label={done ? "Completado" : "Pendiente"} tone={done ? "ok" : "warn"} />
    </div>
  );
}

function EmptyState({ actionHref, actionLabel, text }: { actionHref: string; actionLabel: string; text: string }) {
  return (
    <div className="border-t border-field-line p-3 text-sm">
      <p className="text-field-muted">{text}</p>
      <Link className="mt-3 inline-flex border border-field-line px-3 py-2 font-semibold hover:bg-field-bg" href={actionHref}>
        {actionLabel}
      </Link>
    </div>
  );
}
