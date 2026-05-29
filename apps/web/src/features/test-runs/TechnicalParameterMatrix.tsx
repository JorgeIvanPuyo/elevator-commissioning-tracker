import Link from "next/link";

import { previewHexDecimal } from "@/lib/hex";
import type { LevelingDirection, ZoneLevelingAnalysis, ZoneLevelingEntry } from "@/types/api";

type ParameterDraftValue = {
  hex_value: string;
};

type BiasMatrixRowDefinition = {
  zone: ZoneLevelingEntry["zone"];
  direction: LevelingDirection;
  minCode: string;
  maxCode: string;
};

type MatrixStatus = "OK" | "WARN_MAX_NOT_GREATER" | "WARN_WINDOW_LOW" | "WARN_WINDOW_HIGH" | "MISSING" | "INVALID_HEX";

const biasRows: BiasMatrixRowDefinition[] = [
  { zone: "low", direction: "up", minCode: "026D", maxCode: "273" },
  { zone: "low", direction: "down", minCode: "026E", maxCode: "274" },
  { zone: "mid", direction: "up", minCode: "026F", maxCode: "275" },
  { zone: "mid", direction: "down", minCode: "270", maxCode: "276" },
  { zone: "high", direction: "up", minCode: "271", maxCode: "277" },
  { zone: "high", direction: "down", minCode: "272", maxCode: "278" },
];

const zoneLabels: Record<BiasMatrixRowDefinition["zone"], string> = {
  low: "Baja",
  mid: "Media",
  high: "Alta",
};

const directionLabels: Record<LevelingDirection, string> = {
  up: "Subida",
  down: "Bajada",
};

const statusLabels: Record<MatrixStatus, string> = {
  OK: "OK",
  WARN_MAX_NOT_GREATER: "MAX <= MIN",
  WARN_WINDOW_LOW: "Ventana baja",
  WARN_WINDOW_HIGH: "Ventana alta",
  MISSING: "Faltan valores",
  INVALID_HEX: "HEX inválido",
};

export function TechnicalParameterMatrix({
  analysis,
  draftValues,
}: {
  analysis: ZoneLevelingAnalysis | null;
  draftValues: Record<string, ParameterDraftValue>;
}) {
  const rows = biasRows.map((definition) => buildMatrixRow(definition, draftValues, analysis));
  const okCount = rows.filter((row) => row.status === "OK").length;
  const warningCount = rows.length - okCount;

  return (
    <section className="mt-6 border border-field-line bg-white shadow-panel" id="parameter-matrix">
      <div className="flex flex-col gap-3 border-b border-field-line p-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h3 className="text-lg font-semibold">Matriz técnica de parámetros</h3>
          <p className="mt-1 text-sm text-field-muted">Bias de nivelación fina 026D-278 con ventana MIN/MAX y sugerencias por zona.</p>
        </div>
        <div className="flex flex-wrap gap-2 text-xs font-semibold">
          <span className="border border-field-ok px-2.5 py-1 text-field-ok">{okCount} OK</span>
          <span className={`border px-2.5 py-1 ${warningCount > 0 ? "border-field-warn text-field-warn" : "border-field-line text-field-muted"}`}>
            {warningCount} warnings
          </span>
          <Link className="border border-field-line px-2.5 py-1 text-field-info hover:bg-field-bg" href="#parameter-editor">
            Editar HEX
          </Link>
        </div>
      </div>

      <div className="hidden border-b border-field-line bg-field-bg px-3 py-2 text-xs font-semibold uppercase text-field-muted xl:grid xl:grid-cols-[74px_86px_116px_116px_78px_136px_136px_1fr_120px]">
        <span>Zona</span>
        <span>Dirección</span>
        <span>MIN actual</span>
        <span>MAX actual</span>
        <span>Ventana</span>
        <span>MIN sugerido</span>
        <span>MAX sugerido</span>
        <span>Base cálculo</span>
        <span>Estado</span>
      </div>

      <div className="grid gap-0">
        {rows.map((row) => (
          <MatrixRow key={`${row.definition.zone}-${row.definition.direction}`} row={row} />
        ))}
      </div>
    </section>
  );
}

function MatrixRow({ row }: { row: ReturnType<typeof buildMatrixRow> }) {
  const toneClass = statusTone(row.status);
  const analysisStatus = row.analysis?.status;
  const statusText =
    row.status === "OK" && analysisStatus === "missing_measurements"
      ? "Sin mediciones"
      : row.status === "OK" && analysisStatus === "missing_parameters"
        ? "Faltan parámetros"
        : statusLabels[row.status];

  return (
    <div className="grid gap-3 border-b border-field-line p-3 text-sm xl:grid-cols-[74px_86px_116px_116px_78px_136px_136px_1fr_120px] xl:items-start">
      <LabeledValue label="Zona" value={`${zoneLabels[row.definition.zone]}${row.analysis?.floor_range_label ? ` ${row.analysis.floor_range_label}` : ""}`} />
      <LabeledValue label="Dirección" value={directionLabels[row.definition.direction]} />
      <ParameterDisplay code={row.definition.minCode} decimal={row.minPreview.decimal} error={row.minPreview.error} hex={row.minPreview.normalized} label="MIN actual" />
      <ParameterDisplay code={row.definition.maxCode} decimal={row.maxPreview.decimal} error={row.maxPreview.error} hex={row.maxPreview.normalized} label="MAX actual" />
      <LabeledValue label="Ventana" value={row.windowDecimal === null ? "-" : String(row.windowDecimal)} valueClassName={windowTone(row.status)} />
      <SuggestedValue code={row.definition.minCode} decimal={row.analysis?.min_parameter.suggested_decimal ?? null} hex={row.analysis?.min_parameter.suggested_hex ?? null} label="MIN sugerido" />
      <SuggestedValue code={row.definition.maxCode} decimal={row.analysis?.max_parameter.suggested_decimal ?? null} hex={row.analysis?.max_parameter.suggested_hex ?? null} label="MAX sugerido" />
      <div>
        <p className="text-xs uppercase text-field-muted xl:hidden">Base cálculo</p>
        <p className={`font-semibold ${mmTone(row.analysis?.average_landing_mm ?? null)}`}>{formatMm(row.analysis?.average_landing_mm ?? null)}</p>
        <p className="mt-1 text-xs text-field-muted">{formatExplanation(row.analysis)}</p>
      </div>
      <div>
        <p className={`font-semibold ${toneClass}`}>{statusText}</p>
        {row.warningText ? <p className={`mt-1 text-xs ${toneClass}`}>{row.warningText}</p> : null}
        {row.analysis?.warnings.map((warning) => (
          <p className={warning.severity === "critical" ? "mt-1 text-xs text-field-fail" : "mt-1 text-xs text-field-warn"} key={`${warning.type}-${warning.message}`}>
            {warning.message}
          </p>
        ))}
      </div>
    </div>
  );
}

function buildMatrixRow(definition: BiasMatrixRowDefinition, draftValues: Record<string, ParameterDraftValue>, analysis: ZoneLevelingAnalysis | null) {
  const minPreview = previewHexDecimal(draftValues[definition.minCode]?.hex_value ?? "");
  const maxPreview = previewHexDecimal(draftValues[definition.maxCode]?.hex_value ?? "");
  const zoneAnalysis = analysis?.zones.find((entry) => entry.zone === definition.zone && entry.direction === definition.direction) ?? null;
  const windowDecimal = minPreview.decimal === null || maxPreview.decimal === null ? null : maxPreview.decimal - minPreview.decimal;
  const status = classifyMatrixStatus(minPreview, maxPreview, windowDecimal);

  return {
    analysis: zoneAnalysis,
    definition,
    maxPreview,
    minPreview,
    status,
    warningText: statusWarningText(status),
    windowDecimal,
  };
}

function classifyMatrixStatus(
  minPreview: ReturnType<typeof previewHexDecimal>,
  maxPreview: ReturnType<typeof previewHexDecimal>,
  windowDecimal: number | null,
): MatrixStatus {
  if (minPreview.error || maxPreview.error) {
    return "INVALID_HEX";
  }
  if (minPreview.decimal === null || maxPreview.decimal === null || windowDecimal === null) {
    return "MISSING";
  }
  if (maxPreview.decimal <= minPreview.decimal) {
    return "WARN_MAX_NOT_GREATER";
  }
  if (windowDecimal < 4) {
    return "WARN_WINDOW_LOW";
  }
  if (windowDecimal > 6) {
    return "WARN_WINDOW_HIGH";
  }
  return "OK";
}

function statusWarningText(status: MatrixStatus) {
  if (status === "WARN_MAX_NOT_GREATER") {
    return "La ventana queda invertida o cerrada.";
  }
  if (status === "WARN_WINDOW_LOW") {
    return "La ventana práctica queda por debajo de 4.";
  }
  if (status === "WARN_WINDOW_HIGH") {
    return "La ventana práctica queda por encima de 6.";
  }
  if (status === "MISSING") {
    return "Captura MIN y MAX para calcular la ventana.";
  }
  if (status === "INVALID_HEX") {
    return "Corrige el valor en el editor de parámetros.";
  }
  return null;
}

function LabeledValue({ label, value, valueClassName = "" }: { label: string; value: string; valueClassName?: string }) {
  return (
    <div>
      <p className="text-xs uppercase text-field-muted xl:hidden">{label}</p>
      <p className={`font-semibold ${valueClassName}`}>{value}</p>
    </div>
  );
}

function ParameterDisplay({
  code,
  decimal,
  error,
  hex,
  label,
}: {
  code: string;
  decimal: number | null;
  error: string | null;
  hex: string;
  label: string;
}) {
  return (
    <div>
      <p className="text-xs uppercase text-field-muted xl:hidden">{label}</p>
      <p className="font-semibold">{code}</p>
      <p className={error ? "mt-1 text-xs text-field-fail" : "mt-1 text-xs text-field-muted"}>{error ? "HEX inválido" : formatHexDecimal(hex, decimal)}</p>
    </div>
  );
}

function SuggestedValue({ code, decimal, hex, label }: { code: string; decimal: number | null; hex: string | null; label: string }) {
  return (
    <div>
      <p className="text-xs uppercase text-field-muted xl:hidden">{label}</p>
      <p className="font-semibold">{code}</p>
      <p className="mt-1 text-xs text-field-muted">{hex && decimal !== null ? `${hex}H (${decimal})` : "-"}</p>
    </div>
  );
}

function formatHexDecimal(hex: string, decimal: number | null) {
  if (!hex || decimal === null) {
    return "-";
  }
  return `${hex}H (${decimal})`;
}

function formatMm(value: number | null) {
  if (value === null) {
    return "Sin promedio";
  }
  return `${value > 0 ? "+" : ""}${value} mm`;
}

function formatExplanation(entry: ZoneLevelingEntry | null) {
  if (!entry || entry.status === "missing_measurements") {
    return "Sin mediciones disponibles.";
  }
  if (entry.rounded_delta_decimal === null) {
    return "Sin delta calculado.";
  }
  if (entry.rounded_delta_decimal > 0) {
    return `Aumentar MIN y MAX en ${entry.rounded_delta_decimal} unidades.`;
  }
  if (entry.rounded_delta_decimal < 0) {
    return `Reducir MIN y MAX en ${Math.abs(entry.rounded_delta_decimal)} unidades.`;
  }
  return "Sin cambio sugerido.";
}

function statusTone(status: MatrixStatus) {
  if (status === "OK") {
    return "text-field-ok";
  }
  if (status === "WARN_MAX_NOT_GREATER" || status === "INVALID_HEX") {
    return "text-field-fail";
  }
  if (status === "MISSING") {
    return "text-field-muted";
  }
  return "text-field-warn";
}

function windowTone(status: MatrixStatus) {
  if (status === "OK") {
    return "text-field-ok";
  }
  if (status === "WARN_MAX_NOT_GREATER" || status === "INVALID_HEX") {
    return "text-field-fail";
  }
  if (status === "WARN_WINDOW_LOW" || status === "WARN_WINDOW_HIGH") {
    return "text-field-warn";
  }
  return "";
}

function mmTone(value: number | null) {
  if (value === null || value === 0) {
    return "";
  }
  return value > 0 ? "text-field-info" : "text-field-warn";
}
