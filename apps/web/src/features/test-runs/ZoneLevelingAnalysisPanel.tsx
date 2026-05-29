import type { ZoneLevelingAnalysis, ZoneLevelingEntry, ZoneLevelingParameterSuggestion } from "@/types/api";

const zoneLabels: Record<ZoneLevelingEntry["zone"], string> = {
  low: "Baja",
  mid: "Media",
  high: "Alta",
};

const directionLabels: Record<ZoneLevelingEntry["direction"], string> = {
  up: "Subida",
  down: "Bajada",
};

const statusLabels: Record<ZoneLevelingEntry["status"], string> = {
  ok: "OK",
  warning: "Warning",
  missing_measurements: "Sin mediciones",
  missing_parameters: "Faltan parámetros",
};

export function ZoneLevelingAnalysisPanel({ analysis }: { analysis: ZoneLevelingAnalysis | null }) {
  return (
    <section className="mt-6 border border-field-line bg-white shadow-panel" id="zone-analysis">
      <div className="border-b border-field-line p-4">
        <h3 className="text-lg font-semibold">Análisis por zonas</h3>
        <p className="mt-1 text-sm text-field-muted">Promedio de aterrizaje y sugerencia de ajuste MIN/MAX por zona y dirección.</p>
      </div>

      {!analysis ? (
        <p className="p-4 text-sm text-field-muted">No se pudo cargar el análisis por zonas.</p>
      ) : (
        <div className="grid gap-0">
          <div className="hidden border-b border-field-line bg-field-bg px-3 py-2 text-xs font-semibold uppercase text-field-muted xl:grid xl:grid-cols-[80px_80px_80px_110px_90px_150px_150px_150px_1fr]">
            <span>Zona</span>
            <span>Dirección</span>
            <span>Med.</span>
            <span>Promedio</span>
            <span>Delta</span>
            <span>MIN actual</span>
            <span>MAX actual</span>
            <span>Sugerido</span>
            <span>Estado</span>
          </div>
          {analysis.zones.map((entry) => (
            <ZoneLevelingRow entry={entry} key={`${entry.zone}-${entry.direction}`} />
          ))}
        </div>
      )}
    </section>
  );
}

function ZoneLevelingRow({ entry }: { entry: ZoneLevelingEntry }) {
  const hasCriticalWarning = entry.warnings.some((warning) => warning.severity === "critical");
  const statusTone =
    entry.status === "ok"
      ? "text-field-ok"
      : hasCriticalWarning
        ? "text-field-fail"
        : entry.status === "missing_measurements" || entry.status === "missing_parameters"
          ? "text-field-muted"
          : "text-field-warn";

  return (
    <div className="grid gap-3 border-b border-field-line p-3 text-sm xl:grid-cols-[80px_80px_80px_110px_90px_150px_150px_150px_1fr] xl:items-start">
      <LabeledValue label="Zona" value={`${zoneLabels[entry.zone]} ${entry.floor_range_label}`} />
      <LabeledValue label="Dirección" value={directionLabels[entry.direction]} />
      <LabeledValue label="Med." value={String(entry.measurement_count)} />
      <LabeledValue label="Promedio" value={formatMm(entry.average_landing_mm)} valueClassName={mmTone(entry.average_landing_mm)} />
      <LabeledValue label="Delta" value={entry.rounded_delta_decimal === null ? "-" : String(entry.rounded_delta_decimal)} />
      <ParameterValue label="MIN actual" parameter={entry.min_parameter} mode="current" />
      <ParameterValue label="MAX actual" parameter={entry.max_parameter} mode="current" />
      <div>
        <p className="text-xs uppercase text-field-muted xl:hidden">Sugerido</p>
        <p className="font-semibold">
          {formatSuggested(entry.min_parameter)} / {formatSuggested(entry.max_parameter)}
        </p>
        <p className="mt-1 text-xs text-field-muted">
          Ventana {entry.current_window_decimal ?? "-"} a {entry.suggested_window_decimal ?? "-"}
        </p>
      </div>
      <div>
        <p className={`font-semibold ${statusTone}`}>{statusLabels[entry.status]}</p>
        {entry.warnings.length > 0 ? (
          <div className="mt-1 grid gap-1">
            {entry.warnings.map((warning) => (
              <p className={warning.severity === "critical" ? "text-xs text-field-fail" : "text-xs text-field-warn"} key={`${warning.type}-${warning.message}`}>
                {warning.message}
              </p>
            ))}
          </div>
        ) : (
          <p className="mt-1 text-xs text-field-muted">Sin warnings</p>
        )}
      </div>
    </div>
  );
}

function LabeledValue({ label, value, valueClassName = "" }: { label: string; value: string; valueClassName?: string }) {
  return (
    <div>
      <p className="text-xs uppercase text-field-muted xl:hidden">{label}</p>
      <p className={`font-semibold ${valueClassName}`}>{value}</p>
    </div>
  );
}

function ParameterValue({
  label,
  mode,
  parameter,
}: {
  label: string;
  mode: "current" | "suggested";
  parameter: ZoneLevelingParameterSuggestion;
}) {
  const hex = mode === "current" ? parameter.current_hex : parameter.suggested_hex;
  const decimal = mode === "current" ? parameter.current_decimal : parameter.suggested_decimal;
  return (
    <div>
      <p className="text-xs uppercase text-field-muted xl:hidden">{label}</p>
      <p className="font-semibold">{parameter.code}</p>
      <p className="mt-1 text-xs text-field-muted">{hex && decimal !== null ? `${hex} (${decimal})` : "-"}</p>
    </div>
  );
}

function formatSuggested(parameter: ZoneLevelingParameterSuggestion) {
  if (!parameter.suggested_hex || parameter.suggested_decimal === null) {
    return `${parameter.code} -`;
  }
  return `${parameter.code} ${parameter.suggested_hex} (${parameter.suggested_decimal})`;
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
