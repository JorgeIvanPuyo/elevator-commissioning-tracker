"use client";

import type { ReactNode } from "react";

import type { LevelingFloorSummary, LevelingStatus, LevelingSummary } from "@/types/api";

const statusLabels: Record<LevelingStatus, string> = {
  pending: "Pendiente",
  ok: "OK",
  warning: "Alerta",
  critical: "Crítico",
  not_required: "No requerido",
};

const statusClass: Record<LevelingStatus, string> = {
  pending: "border-field-line text-field-muted",
  ok: "border-field-ok text-field-ok",
  warning: "border-field-warn text-field-warn",
  critical: "border-field-fail text-field-fail",
  not_required: "border-field-line text-field-muted",
};

export function LevelingSummaryPanel({ summary }: { summary: LevelingSummary | null }) {
  if (!summary) {
    return (
      <section className="mt-6 border border-field-line bg-white p-4 shadow-panel">
        <h3 className="text-lg font-semibold">Resumen técnico de nivelación</h3>
        <p className="mt-2 text-sm text-field-muted">Cargando KPIs de nivelación...</p>
      </section>
    );
  }

  const hasMeasurements = summary.measurement_count > 0;
  const hasHysteresisPairs = summary.hysteresis_pairs_count > 0;

  return (
    <section className="mt-6 border border-field-line bg-white shadow-panel">
      <div className="flex flex-col gap-2 border-b border-field-line p-4 md:flex-row md:items-start md:justify-between">
        <div>
          <h3 className="text-lg font-semibold">Resumen técnico de nivelación</h3>
          <p className="mt-1 text-sm text-field-muted">KPIs por prueba con tolerancia final ±5 mm, renivelación e histerisis inicial.</p>
        </div>
        <span className={`inline-flex border px-3 py-2 text-sm font-semibold ${statusClass[summary.overall_status]}`}>{statusLabels[summary.overall_status]}</span>
      </div>

      {!hasMeasurements ? (
        <p className="border-b border-field-line p-4 text-sm text-field-muted">Aún no hay mediciones suficientes para calcular KPIs de nivelación.</p>
      ) : null}
      {hasMeasurements && !hasHysteresisPairs ? (
        <p className="border-b border-field-line p-4 text-sm text-field-muted">Aún no hay pares subida/bajada suficientes para calcular histerisis.</p>
      ) : null}

      <div className="grid gap-2 border-b border-field-line p-4 sm:grid-cols-2 lg:grid-cols-6">
        <KpiCard label="Mediciones" value={summary.measurement_count} />
        <KpiCard label="Cobertura" value={`${summary.coverage_percentage}%`} detail={`${summary.measured_required_floor_count}/${summary.required_floor_count} pisos`} />
        <KpiCard
          label="Tolerancia final"
          value={`${summary.within_final_tolerance_percentage}%`}
          detail={`${summary.within_final_tolerance_count} OK / ${summary.out_of_final_tolerance_count} fuera`}
        />
        <KpiCard
          label="Renivelación"
          value={`${summary.acceptable_renivelation_percentage}%`}
          detail={`${summary.acceptable_renivelation_count}/${summary.renivelation_count} aceptables`}
        />
        <KpiCard label="Histerisis" value={`${summary.hysteresis_ok_percentage}%`} detail={`${summary.hysteresis_ok_count}/${summary.hysteresis_pairs_count} pares`} />
        <KpiCard label="Estado" value={statusLabels[summary.overall_status]} />
      </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[860px] border-collapse text-left text-sm">
          <thead className="bg-field-bg text-xs uppercase text-field-muted">
            <tr>
              <th className="px-4 py-3">Piso</th>
              <th className="px-4 py-3">Mediciones</th>
              <th className="px-4 py-3">Corto subiendo</th>
              <th className="px-4 py-3">Corto bajando</th>
              <th className="px-4 py-3">Largo subiendo</th>
              <th className="px-4 py-3">Largo bajando</th>
              <th className="px-4 py-3">Histerisis máx.</th>
              <th className="px-4 py-3">Estado</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-field-line">
            {summary.floor_summaries.map((floor) => (
              <FloorSummaryRow floor={floor} key={floor.floor_id} />
            ))}
          </tbody>
        </table>
      </div>

      <p className="border-t border-field-line p-4 text-xs text-field-muted">
        Criterios: nivel final OK entre -5 mm y +5 mm; histerisis OK cuando la diferencia comparable es menor o igual a 5 mm; crítico si el valor final absoluto supera 10 mm.
      </p>
    </section>
  );
}

function KpiCard({ label, value, detail }: { label: string; value: string | number; detail?: string }) {
  return (
    <div className="border border-field-line bg-white px-3 py-3">
      <p className="text-xs text-field-muted">{label}</p>
      <p className="mt-1 font-semibold">{value}</p>
      {detail ? <p className="mt-1 text-xs text-field-muted">{detail}</p> : null}
    </div>
  );
}

function FloorSummaryRow({ floor }: { floor: LevelingFloorSummary }) {
  return (
    <tr>
      <td className="px-4 py-3 font-semibold">{floor.floor_label}</td>
      <td className="px-4 py-3">{floor.measurements_count}</td>
      <td className="px-4 py-3">{formatMillimeters(floor.final_values_mm.short_up)}</td>
      <td className="px-4 py-3">{formatMillimeters(floor.final_values_mm.short_down)}</td>
      <td className="px-4 py-3">{formatMillimeters(floor.final_values_mm.long_up)}</td>
      <td className="px-4 py-3">{formatMillimeters(floor.final_values_mm.long_down)}</td>
      <td className="px-4 py-3">{floor.hysteresis.max_difference_mm === null ? "-" : `${floor.hysteresis.max_difference_mm} mm`}</td>
      <td className="px-4 py-3">
        <span className={`inline-flex border px-2 py-1 text-xs font-semibold ${statusClass[floor.status]}`}>{statusLabels[floor.status]}</span>
      </td>
    </tr>
  );
}

function formatMillimeters(value: number | null): ReactNode {
  if (value === null) {
    return "-";
  }
  const className = value > 0 ? "text-field-info" : value < 0 ? "text-field-warn" : "text-field-ink";
  const label = value > 0 ? `${value} mm alta` : value < 0 ? `${value} mm baja` : "0 mm nivelado";
  return <span className={className}>{label}</span>;
}
