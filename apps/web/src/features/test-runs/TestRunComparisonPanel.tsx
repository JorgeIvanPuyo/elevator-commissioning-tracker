"use client";

import { useState } from "react";

import { api } from "@/lib/api";
import type { ComparisonCandidate, ComparisonTrend, FloorComparisonTrend, LevelingStatus, TestRunComparison } from "@/types/api";

const trendLabels: Record<ComparisonTrend | FloorComparisonTrend, string> = {
  improved: "Mejoró",
  worsened: "Empeoró",
  mixed: "Mixto",
  unchanged: "Igual",
  not_comparable: "No comparable",
  newly_measured: "Nuevo",
  missing_current: "Falta actual",
};

const trendClass: Record<ComparisonTrend | FloorComparisonTrend, string> = {
  improved: "border-field-ok text-field-ok",
  worsened: "border-field-fail text-field-fail",
  mixed: "border-field-warn text-field-warn",
  unchanged: "border-field-line text-field-muted",
  not_comparable: "border-field-line text-field-muted",
  newly_measured: "border-field-info text-field-info",
  missing_current: "border-field-warn text-field-warn",
};

const statusLabels: Record<LevelingStatus | "not_comparable", string> = {
  pending: "Pendiente",
  ok: "OK",
  warning: "Alerta",
  critical: "Crítico",
  not_required: "No requerido",
  not_comparable: "No comparable",
};

export function TestRunComparisonPanel({ testRunId, candidates }: { testRunId: string; candidates: ComparisonCandidate[] }) {
  const [selectedBaselineId, setSelectedBaselineId] = useState(candidates[0]?.id ?? "");
  const [comparison, setComparison] = useState<TestRunComparison | null>(null);
  const [showAllParameters, setShowAllParameters] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadComparison() {
    if (!selectedBaselineId) {
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      setComparison(await api.compareTestRuns(testRunId, selectedBaselineId));
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "No se pudo comparar la prueba");
    } finally {
      setIsLoading(false);
    }
  }

  const visibleParameters = comparison?.parameter_comparisons.filter((parameter) => showAllParameters || parameter.changed) ?? [];

  return (
    <section className="mt-6 border border-field-line bg-white shadow-panel">
      <div className="border-b border-field-line p-4">
        <h3 className="text-lg font-semibold">Comparar con prueba anterior</h3>
        <p className="mt-1 text-sm text-field-muted">Evalúa si esta iteración mejoró, empeoró o mantuvo la nivelación.</p>
      </div>

      {candidates.length === 0 ? (
        <p className="p-4 text-sm text-field-muted">No hay pruebas anteriores del mismo elevador para comparar.</p>
      ) : (
        <>
          <div className="grid gap-3 border-b border-field-line p-4 md:grid-cols-[1fr_auto]">
            <select className="border border-field-line px-3 py-3 text-sm" onChange={(event) => setSelectedBaselineId(event.currentTarget.value)} value={selectedBaselineId}>
              {candidates.map((candidate) => (
                <option key={candidate.id} value={candidate.id}>
                  {candidate.name} · {candidate.status} · tolerancia {candidate.within_final_tolerance_percentage}%
                </option>
              ))}
            </select>
            <button className="bg-field-info px-4 py-3 text-sm font-semibold text-white hover:bg-field-ink disabled:opacity-60" disabled={isLoading || !selectedBaselineId} onClick={loadComparison}>
              {isLoading ? "Comparando..." : "Comparar"}
            </button>
          </div>

          {error ? <p className="border-b border-field-line p-3 text-sm text-field-fail">{error}</p> : null}

          {comparison ? (
            <div className="grid gap-0">
              <div className="border-b border-field-line p-4">
                <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
                  <p className="text-sm text-field-muted">{comparison.summary_text}</p>
                  <span className={`inline-flex border px-3 py-2 text-sm font-semibold ${trendClass[comparison.overall_trend]}`}>{trendLabels[comparison.overall_trend]}</span>
                </div>
              </div>

              <div className="grid gap-2 border-b border-field-line p-4 sm:grid-cols-2 lg:grid-cols-5">
                {comparison.global_metrics.slice(0, 5).map((metric) => (
                  <ComparisonMetricCard key={metric.metric} metric={metric} />
                ))}
              </div>

              <div className="border-b border-field-line">
                <SectionHeader title="Comparación por piso" />
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[820px] text-left text-sm">
                    <thead className="bg-field-bg text-xs uppercase text-field-muted">
                      <tr>
                        <th className="px-4 py-3">Piso</th>
                        <th className="px-4 py-3">Estado anterior</th>
                        <th className="px-4 py-3">Estado actual</th>
                        <th className="px-4 py-3">Final anterior</th>
                        <th className="px-4 py-3">Final actual</th>
                        <th className="px-4 py-3">Delta</th>
                        <th className="px-4 py-3">Resultado</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-field-line">
                      {comparison.floor_comparisons.map((floor) => (
                        <tr key={floor.floor_id}>
                          <td className="px-4 py-3 font-semibold">{floor.floor_label}</td>
                          <td className="px-4 py-3">{statusLabels[floor.baseline_status]}</td>
                          <td className="px-4 py-3">{statusLabels[floor.current_status]}</td>
                          <td className="px-4 py-3">{formatMillimeters(floor.baseline_final_mm)}</td>
                          <td className="px-4 py-3">{formatMillimeters(floor.current_final_mm)}</td>
                          <td className="px-4 py-3">{floor.absolute_delta_mm === null ? "-" : `${floor.absolute_delta_mm > 0 ? "+" : ""}${floor.absolute_delta_mm} mm`}</td>
                          <td className="px-4 py-3">
                            <span className={`inline-flex border px-2 py-1 text-xs font-semibold ${trendClass[floor.trend]}`}>{trendLabels[floor.trend]}</span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div>
                <div className="flex flex-col gap-3 border-b border-field-line p-4 md:flex-row md:items-center md:justify-between">
                  <SectionHeader title="Parámetros modificados" />
                  <label className="flex items-center gap-2 text-sm text-field-muted">
                    <input checked={showAllParameters} onChange={(event) => setShowAllParameters(event.currentTarget.checked)} type="checkbox" />
                    Mostrar todos
                  </label>
                </div>
                {visibleParameters.length === 0 ? (
                  <p className="p-4 text-sm text-field-muted">No hay parámetros modificados entre estas pruebas.</p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full min-w-[760px] text-left text-sm">
                      <thead className="bg-field-bg text-xs uppercase text-field-muted">
                        <tr>
                          <th className="px-4 py-3">Parámetro</th>
                          <th className="px-4 py-3">HEX anterior</th>
                          <th className="px-4 py-3">HEX actual</th>
                          <th className="px-4 py-3">Decimal anterior</th>
                          <th className="px-4 py-3">Decimal actual</th>
                          <th className="px-4 py-3">Delta</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-field-line">
                        {visibleParameters.map((parameter) => (
                          <tr key={parameter.parameter_code}>
                            <td className="px-4 py-3">
                              <span className="font-semibold">{parameter.parameter_code}</span>
                              <span className="ml-2 text-field-muted">{parameter.name}</span>
                              {parameter.warning ? <p className="mt-1 text-xs text-field-warn">{parameter.warning}</p> : null}
                            </td>
                            <td className="px-4 py-3">{parameter.baseline_hex_value ?? "-"}</td>
                            <td className="px-4 py-3">{parameter.current_hex_value ?? "-"}</td>
                            <td className="px-4 py-3">{parameter.baseline_decimal_value ?? "-"}</td>
                            <td className="px-4 py-3">{parameter.current_decimal_value ?? "-"}</td>
                            <td className="px-4 py-3">{parameter.decimal_delta === null ? "-" : parameter.decimal_delta}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <p className="p-4 text-sm text-field-muted">Selecciona una prueba base para ver diferencias de KPIs, pisos y parámetros.</p>
          )}
        </>
      )}
    </section>
  );
}

function SectionHeader({ title }: { title: string }) {
  return <h4 className="font-semibold">{title}</h4>;
}

function ComparisonMetricCard({ metric }: { metric: TestRunComparison["global_metrics"][number] }) {
  return (
    <div className="border border-field-line bg-white p-3">
      <p className="text-xs text-field-muted">{metric.label}</p>
      <p className="mt-1 text-sm">
        <span>{formatMetricValue(metric.baseline_value)}</span>
        <span className="mx-2 text-field-muted">→</span>
        <span className="font-semibold">{formatMetricValue(metric.current_value)}</span>
      </p>
      <div className="mt-2 flex items-center justify-between gap-2">
        <span className="text-xs text-field-muted">{metric.delta === null ? "-" : `${metric.delta > 0 ? "+" : ""}${metric.delta}`}</span>
        <span className={`inline-flex border px-2 py-1 text-xs font-semibold ${trendClass[metric.trend]}`}>{trendLabels[metric.trend]}</span>
      </div>
    </div>
  );
}

function formatMetricValue(value: number | null): string {
  return value === null ? "-" : String(value);
}

function formatMillimeters(value: number | null): string {
  if (value === null) {
    return "-";
  }
  return `${value > 0 ? "+" : ""}${value} mm`;
}
