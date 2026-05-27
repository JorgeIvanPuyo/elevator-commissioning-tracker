const HEX_PATTERN = /^[0-9A-F]+$/;

export function previewHexDecimal(value: string): { normalized: string; decimal: number | null; error: string | null } {
  let normalized = value.trim();
  if (!normalized) {
    return { normalized: "", decimal: null, error: null };
  }

  if (normalized.toLowerCase().startsWith("0x")) {
    normalized = normalized.slice(2);
  }
  normalized = normalized.toUpperCase();

  if (!normalized || !HEX_PATTERN.test(normalized)) {
    return { normalized, decimal: null, error: "HEX inválido" };
  }

  return { normalized, decimal: Number.parseInt(normalized, 16), error: null };
}

export function toDatetimeLocalValue(value: string | null): string {
  if (!value) {
    return "";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "";
  }
  return date.toISOString().slice(0, 16);
}

export function fromDatetimeLocalValue(value: FormDataEntryValue | null): string | null {
  const rawValue = String(value || "");
  if (!rawValue) {
    return null;
  }
  return new Date(rawValue).toISOString();
}
