import type { FinalValidationRow, FinalValidationStatus, FinalValidationSummary } from "@/types/api";

const statusLabels: Record<FinalValidationStatus, string> = {
  ok: "Dentro de tolerancia",
  out_of_tolerance: "Fuera de tolerancia",
  partial_data: "Datos incompletos",
  missing_data: "Sin datos",
  not_required: "No requerido",
};

export function FinalValidationPanel({ summary }: { summary: FinalValidationSummary | null }) {
  return (
    <section className="mt-6 border border-field-line bg-white shadow-panel" id="final-validation">
      <div className="flex flex-col gap-3 border-b border-field-line p-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h3 className="text-lg font-semibold">Validación final de nivelación</h3>
          <p className="mt-1 text-sm text-field-muted">
            Ejecuta FHM después de mover las banderas para que el controlador almacene las nuevas referencias. Luego registra la validación final piso a piso.
          </p>
        </div>
        <a className="border border-field-line px-3 py-2 text-sm font-semibold text-field-info hover:bg-field-bg" href="#final-validation-measurements">
          Agregar mediciones
        </a>
      </div>

      {!summary ? (
        <p className="p-4 text-sm text-field-muted">No se pudo cargar la validación final.</p>
      ) : (
        <>
          <div className={`border-b border-field-line p-3 text-sm ${summary.fhm_completed ? "text-field-ok" : "text-field-warn"}`}>
            <span className="font-semibold">FHM / Medición de altura de pisos: </span>
            {summary.fhm_completed ? "FHM completado" : "FHM aún no está marcado como completado. La validación final debería registrarse después de ejecutar FHM."}
          </div>

          <div className="grid gap-0 border-b border-field-line md:grid-cols-5">
            <MetricCell label="Pisos dentro de tolerancia" tone="ok" value={String(summary.summary.floors_within_tolerance)} />
            <MetricCell label="Pisos fuera de tolerancia" tone="warn" value={String(summary.summary.floors_out_of_tolerance)} />
            <MetricCell label="Datos incompletos" tone="neutral" value={String(summary.summary.floors_partial_data)} />
            <MetricCell label="Sin datos" tone="neutral" value={String(summary.summary.floors_missing_data)} />
            <MetricCell label="% tolerancia" tone="neutral" value={`${summary.summary.within_tolerance_percent}%`} />
          </div>

          <div className="hidden border-b border-field-line bg-field-bg px-3 py-2 text-xs font-semibold uppercase text-field-muted lg:grid lg:grid-cols-[90px_140px_140px_160px_1fr]">
            <span>Piso</span>
            <span>Bajada final</span>
            <span>Subida final</span>
            <span>Estado</span>
            <span>Resultado</span>
          </div>

          <div className="grid gap-0">
            {summary.rows.map((row) => (
              <FinalValidationRowView key={row.floor_id} row={row} />
            ))}
          </div>
        </>
      )}
    </section>
  );
}

function FinalValidationRowView({ row }: { row: FinalValidationRow }) {
  const statusTone = row.status === "ok" ? "text-field-ok" : row.status === "out_of_tolerance" ? "text-field-fail" : "text-field-muted";
  return (
    <div className="grid gap-3 border-b border-field-line p-3 text-sm lg:grid-cols-[90px_140px_140px_160px_1fr] lg:items-center">
      <LabeledValue label="Piso" value={row.floor_label} />
      <LabeledValue label="Bajada final" value={formatMm(row.down_final_mm)} valueClassName={mmTone(row.down_final_mm)} />
      <LabeledValue label="Subida final" value={formatMm(row.up_final_mm)} valueClassName={mmTone(row.up_final_mm)} />
      <LabeledValue label="Estado" value={statusLabels[row.status]} valueClassName={statusTone} />
      <LabeledValue label="Resultado" value={row.within_tolerance === null ? "-" : row.within_tolerance ? "OK" : "Revisar"} valueClassName={statusTone} />
    </div>
  );
}

function MetricCell({ label, tone, value }: { label: string; tone: "neutral" | "ok" | "warn"; value: string }) {
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

function mmTone(value: number | null) {
  if (value === null || value === 0) {
    return "";
  }
  return value > 0 ? "text-field-info" : "text-field-warn";
}
