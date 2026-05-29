import type { FlagAdjustmentRecommendations, FlagAdjustmentRow, FlagAdjustmentStatus } from "@/types/api";

const statusLabels: Record<FlagAdjustmentStatus, string> = {
  ok: "Dentro de tolerancia",
  requires_adjustment: "Requiere ajuste",
  partial_data: "Datos incompletos",
  missing_data: "Sin datos",
  not_required: "No requerido",
};

export function FlagAdjustmentRecommendationsPanel({ recommendations }: { recommendations: FlagAdjustmentRecommendations | null }) {
  return (
    <section className="mt-6 border border-field-line bg-white shadow-panel" id="flag-adjustments">
      <div className="border-b border-field-line p-4">
        <h3 className="text-lg font-semibold">Recomendación de movimiento de banderas</h3>
        <p className="mt-1 text-sm text-field-muted">
          El movimiento recomendado se calcula con el promedio entre la llegada final bajando y subiendo. Si ambas medidas están dentro de ±5 mm, no se recomienda mover la bandera.
        </p>
      </div>

      {!recommendations ? (
        <p className="p-4 text-sm text-field-muted">No se pudieron cargar recomendaciones de banderas.</p>
      ) : (
        <>
          <div className="grid gap-0 border-b border-field-line md:grid-cols-4">
            <SummaryCell label="Requieren ajuste" tone="warn" value={String(recommendations.summary.floors_requiring_flag_adjustment)} />
            <SummaryCell label="Dentro de tolerancia" tone="ok" value={String(recommendations.summary.floors_within_tolerance)} />
            <SummaryCell
              label="Sin datos/parcial"
              tone="neutral"
              value={String(recommendations.summary.floors_missing_data + recommendations.summary.floors_partial_data)}
            />
            <SummaryCell label="Movimiento máximo" tone="neutral" value={formatMm(recommendations.summary.max_abs_recommended_movement_mm)} />
          </div>

          <div className="hidden border-b border-field-line bg-field-bg px-3 py-2 text-xs font-semibold uppercase text-field-muted lg:grid lg:grid-cols-[80px_120px_120px_160px_150px_1fr]">
            <span>Piso</span>
            <span>Bajada final</span>
            <span>Subida final</span>
            <span>Movimiento recomendado</span>
            <span>Estado</span>
            <span>Notas</span>
          </div>

          <div className="grid gap-0">
            {recommendations.rows.map((row) => (
              <FlagAdjustmentRowView key={row.floor_id} row={row} />
            ))}
          </div>
        </>
      )}
    </section>
  );
}

function FlagAdjustmentRowView({ row }: { row: FlagAdjustmentRow }) {
  const statusTone = row.status === "ok" ? "text-field-ok" : row.status === "requires_adjustment" ? "text-field-warn" : "text-field-muted";

  return (
    <div className="grid gap-3 border-b border-field-line p-3 text-sm lg:grid-cols-[80px_120px_120px_160px_150px_1fr] lg:items-start">
      <LabeledValue label="Piso" value={row.floor_label} />
      <LabeledValue label="Bajada final" value={formatMm(row.down_final_mm)} valueClassName={mmTone(row.down_final_mm)} />
      <LabeledValue label="Subida final" value={formatMm(row.up_final_mm)} valueClassName={mmTone(row.up_final_mm)} />
      <LabeledValue label="Movimiento recomendado" value={formatMovement(row.recommended_flag_movement_mm)} valueClassName={movementTone(row.recommended_flag_movement_mm)} />
      <div>
        <p className="text-xs uppercase text-field-muted lg:hidden">Estado</p>
        <p className={`font-semibold ${statusTone}`}>{statusLabels[row.status]}</p>
      </div>
      <div>
        <p className="text-xs uppercase text-field-muted lg:hidden">Notas</p>
        {row.notes.length > 0 ? (
          <div className="grid gap-1">
            {row.notes.map((note) => (
              <p className="text-xs text-field-muted" key={note}>
                {note}
              </p>
            ))}
          </div>
        ) : (
          <p className="text-xs text-field-muted">-</p>
        )}
      </div>
    </div>
  );
}

function SummaryCell({ label, tone, value }: { label: string; tone: "neutral" | "ok" | "warn"; value: string }) {
  const toneClass = tone === "ok" ? "text-field-ok" : tone === "warn" ? "text-field-warn" : "text-field-ink";
  return (
    <div className="border-b border-r border-field-line p-3">
      <p className="text-xs font-semibold uppercase text-field-muted">{label}</p>
      <p className={`mt-1 text-lg font-semibold ${toneClass}`}>{value}</p>
    </div>
  );
}

function LabeledValue({ label, value, valueClassName = "" }: { label: string; value: string; valueClassName?: string }) {
  return (
    <div>
      <p className="text-xs uppercase text-field-muted lg:hidden">{label}</p>
      <p className={`font-semibold ${valueClassName}`}>{value}</p>
    </div>
  );
}

function formatMm(value: number | null) {
  if (value === null) {
    return "-";
  }
  return `${value > 0 ? "+" : ""}${value} mm`;
}

function formatMovement(value: number | null) {
  if (value === null) {
    return "-";
  }
  if (value === 0) {
    return "0 mm";
  }
  return `${value > 0 ? "+" : ""}${value} mm`;
}

function mmTone(value: number | null) {
  if (value === null || value === 0) {
    return "";
  }
  return value > 0 ? "text-field-info" : "text-field-warn";
}

function movementTone(value: number | null) {
  if (value === null || value === 0) {
    return "";
  }
  return value > 0 ? "text-field-info" : "text-field-warn";
}
