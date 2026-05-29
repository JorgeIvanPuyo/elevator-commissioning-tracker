"use client";

import { useEffect, useMemo, useState } from "react";

import { api } from "@/lib/api";
import type {
  ElevatorFloor,
  LevelingDirection,
  LevelingMeasurement,
  LevelingMeasurementBulkItem,
  LevelingMeasurementStage,
  LevelingMeasurementSummary,
  LevelingTravelType,
  TestRun,
} from "@/types/api";

type MeasurementGroup = {
  key: GroupKey;
  label: string;
  direction: LevelingDirection;
  travel_type: LevelingTravelType;
};

type GroupKey = `${LevelingTravelType}:${LevelingDirection}`;

type MeasurementDraftRow = {
  local_id: string;
  measurement_id?: string;
  origin_floor_id: string;
  destination_floor_id: string;
  landing_mm: string;
  final_mm: string;
  notes: string;
};

type MeasurementForm = Omit<MeasurementDraftRow, "local_id" | "measurement_id">;
type DraftGroups = Record<GroupKey, MeasurementDraftRow[]>;
type FormsByGroup = Record<GroupKey, MeasurementForm>;
type EditingByGroup = Record<GroupKey, string | null>;
type ErrorsByGroup = Record<GroupKey, string | null>;

const measurementGroups: MeasurementGroup[] = [
  { key: "short:up", label: "Corto / Subiendo", direction: "up", travel_type: "short" },
  { key: "short:down", label: "Corto / Bajando", direction: "down", travel_type: "short" },
  { key: "long:up", label: "Largo / Subiendo", direction: "up", travel_type: "long" },
  { key: "long:down", label: "Largo / Bajando", direction: "down", travel_type: "long" },
];

const emptySummary: LevelingMeasurementSummary = {
  total: 0,
  with_values: 0,
  within_tolerance: 0,
  outside_tolerance: 0,
  within_tolerance_percentage: 0,
};

const emptyDraftGroups = (): DraftGroups =>
  measurementGroups.reduce(
    (groups, group) => ({
      ...groups,
      [group.key]: [],
    }),
    {} as DraftGroups,
  );

const emptyFormsByGroup = (): FormsByGroup =>
  Object.fromEntries(measurementGroups.map((group) => [group.key, emptyMeasurementForm()])) as FormsByGroup;

const emptyEditingByGroup = (): EditingByGroup =>
  Object.fromEntries(measurementGroups.map((group) => [group.key, null])) as EditingByGroup;

const emptyErrorsByGroup = (): ErrorsByGroup =>
  Object.fromEntries(measurementGroups.map((group) => [group.key, null])) as ErrorsByGroup;

function emptyMeasurementForm(): MeasurementForm {
  return {
    origin_floor_id: "",
    destination_floor_id: "",
    landing_mm: "",
    final_mm: "",
    notes: "",
  };
}

export function LevelingMeasurementEditor({
  measurementStage = "floor_by_floor",
  onMeasurementsChanged,
  testRun,
  title = "Mediciones de nivelación",
}: {
  measurementStage?: LevelingMeasurementStage;
  onMeasurementsChanged?: () => void | Promise<void>;
  testRun: TestRun;
  title?: string;
}) {
  const [floors, setFloors] = useState<ElevatorFloor[]>([]);
  const [draftGroups, setDraftGroups] = useState<DraftGroups>(emptyDraftGroups);
  const [formByGroup, setFormByGroup] = useState<FormsByGroup>(emptyFormsByGroup);
  const [editingByGroup, setEditingByGroup] = useState<EditingByGroup>(emptyEditingByGroup);
  const [formErrors, setFormErrors] = useState<ErrorsByGroup>(emptyErrorsByGroup);
  const [serverSummary, setServerSummary] = useState<LevelingMeasurementSummary>(emptySummary);
  const [hasLocalDraft, setHasLocalDraft] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const sortedFloors = useMemo(() => [...floors].sort((a, b) => a.sort_order - b.sort_order), [floors]);
  const destinationFloors = useMemo(() => sortedFloors.filter((floor) => floor.is_leveling_required), [sortedFloors]);
  const floorLabelById = useMemo(() => new Map(sortedFloors.map((floor) => [floor.id, floorLabel(floor)])), [sortedFloors]);
  const draftKey = `elevator-commissioning:test-run:${testRun.id}:leveling-groups-draft:${measurementStage}`;
  const visibleSummary = useMemo(() => buildSummaryFromDraft(draftGroups), [draftGroups]);
  const summary = visibleSummary.total > 0 || hasLocalDraft ? visibleSummary : serverSummary;

  useEffect(() => {
    async function load() {
      setIsLoading(true);
      setError(null);
      try {
        const [floorResponse, measurementResponse] = await Promise.all([
          api.listElevatorFloors(testRun.elevator_id),
          api.listLevelingMeasurements(testRun.id, undefined, undefined, measurementStage),
        ]);
        const sorted = [...floorResponse].sort((a, b) => a.sort_order - b.sort_order);
        setFloors(sorted);
        setServerSummary(measurementResponse.summary);

        const localDraft = window.localStorage.getItem(draftKey);
        if (localDraft) {
          try {
            setDraftGroups(normalizeDraftGroups(JSON.parse(localDraft) as Partial<DraftGroups>));
            setHasLocalDraft(true);
            return;
          } catch {
            window.localStorage.removeItem(draftKey);
          }
        }

        setDraftGroups(groupsFromMeasurements(measurementResponse.items));
        setHasLocalDraft(false);
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : "No se pudieron cargar mediciones");
      } finally {
        setIsLoading(false);
      }
    }

    void load();
  }, [testRun.id, testRun.elevator_id, draftKey, measurementStage]);

  function updateGroupForm(groupKey: GroupKey, patch: Partial<MeasurementForm>) {
    setSuccessMessage(null);
    setFormErrors((current) => ({ ...current, [groupKey]: null }));
    setFormByGroup((current) => ({ ...current, [groupKey]: { ...current[groupKey], ...patch } }));
  }

  function persistDraft(nextDraft: DraftGroups) {
    setDraftGroups(nextDraft);
    window.localStorage.setItem(draftKey, JSON.stringify(nextDraft));
    setHasLocalDraft(true);
  }

  function addOrUpdateMeasurement(group: MeasurementGroup) {
    const form = formByGroup[group.key];
    const validationError = validateMeasurementForm(form);
    if (validationError) {
      setFormErrors((current) => ({ ...current, [group.key]: validationError }));
      return;
    }

    const editingId = editingByGroup[group.key];
    const existingRow = editingId ? draftGroups[group.key].find((row) => row.local_id === editingId) : undefined;
    const nextRow: MeasurementDraftRow = {
      ...form,
      local_id: editingId ?? crypto.randomUUID(),
      measurement_id: existingRow?.measurement_id,
    };
    const nextDraft = {
      ...draftGroups,
      [group.key]: editingId ? draftGroups[group.key].map((row) => (row.local_id === editingId ? { ...row, ...nextRow } : row)) : [...draftGroups[group.key], nextRow],
    };

    persistDraft(nextDraft);
    setFormByGroup((current) => ({ ...current, [group.key]: emptyMeasurementForm() }));
    setEditingByGroup((current) => ({ ...current, [group.key]: null }));
    setFormErrors((current) => ({ ...current, [group.key]: null }));
  }

  function editMeasurement(groupKey: GroupKey, row: MeasurementDraftRow) {
    setSuccessMessage(null);
    setFormByGroup((current) => ({
      ...current,
      [groupKey]: {
        origin_floor_id: row.origin_floor_id,
        destination_floor_id: row.destination_floor_id,
        landing_mm: row.landing_mm,
        final_mm: row.final_mm,
        notes: row.notes,
      },
    }));
    setEditingByGroup((current) => ({ ...current, [groupKey]: row.local_id }));
    setFormErrors((current) => ({ ...current, [groupKey]: null }));
  }

  async function deleteMeasurement(groupKey: GroupKey, row: MeasurementDraftRow) {
    setError(null);
    setSuccessMessage(null);
    try {
      if (row.measurement_id) {
        setDeletingId(row.local_id);
        await api.deleteLevelingMeasurement(row.measurement_id);
      }
      const nextDraft = {
        ...draftGroups,
        [groupKey]: draftGroups[groupKey].filter((item) => item.local_id !== row.local_id),
      };
      persistDraft(nextDraft);
      await onMeasurementsChanged?.();
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : "No se pudo eliminar la medición");
    } finally {
      setDeletingId(null);
    }
  }

  async function saveMeasurements() {
    setIsSaving(true);
    setError(null);
    setSuccessMessage(null);

    const items: LevelingMeasurementBulkItem[] = measurementGroups.flatMap((group) =>
      draftGroups[group.key].map((row) => ({
        origin_floor_id: row.origin_floor_id,
        destination_floor_id: row.destination_floor_id,
        direction: group.direction,
        travel_type: group.travel_type,
        measurement_stage: measurementStage,
        landing_mm: parseIntegerOrNull(row.landing_mm),
        final_mm: parseIntegerOrNull(row.final_mm),
        notes: row.notes.trim() || null,
      })),
    );

    try {
      const response = await api.saveLevelingMeasurements(testRun.id, items);
      setDraftGroups(groupsFromMeasurements(response.items));
      setServerSummary(response.summary);
      window.localStorage.removeItem(draftKey);
      setHasLocalDraft(false);
      setSuccessMessage("Mediciones guardadas");
      await onMeasurementsChanged?.();
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "No se pudieron guardar mediciones");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="mt-6 border border-field-line bg-white shadow-panel">
      <div className="flex flex-col gap-3 border-b border-field-line p-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h3 className="text-lg font-semibold">{title}</h3>
          <p className="mt-1 text-sm text-field-muted">Piso a piso en mm. Positivo: cabina alta. Negativo: cabina baja.</p>
        </div>
        <button className="bg-field-info px-4 py-3 text-sm font-semibold text-white hover:bg-field-ink disabled:opacity-60" disabled={isSaving} onClick={saveMeasurements}>
          {isSaving ? "Guardando..." : "Guardar mediciones"}
        </button>
      </div>

      <div className="grid gap-2 border-b border-field-line p-4 text-sm md:grid-cols-5">
        <SummaryItem label="Total" value={summary.total} />
        <SummaryItem label="Con datos" value={summary.with_values} />
        <SummaryItem label="Dentro" value={summary.within_tolerance} />
        <SummaryItem label="Fuera" value={summary.outside_tolerance} />
        <SummaryItem label="%" value={`${summary.within_tolerance_percentage}%`} />
      </div>

      {isLoading ? <p className="border-b border-field-line p-4 text-sm text-field-muted">Cargando mediciones...</p> : null}
      {hasLocalDraft ? <p className="border-b border-field-line bg-field-bg p-3 text-sm text-field-warn">Hay mediciones locales sin guardar.</p> : null}
      {successMessage ? <p className="border-b border-field-line p-3 text-sm text-field-ok">{successMessage}</p> : null}
      {error ? <p className="border-b border-field-line p-3 text-sm text-field-fail">{error}</p> : null}

      <div className="grid gap-4 bg-field-bg p-4">
        {measurementGroups.map((group) => (
          <MeasurementGroupCard
            deletingId={deletingId}
            destinationFloors={destinationFloors}
            editingId={editingByGroup[group.key]}
            error={formErrors[group.key]}
            floorLabelById={floorLabelById}
            form={formByGroup[group.key]}
            group={group}
            key={group.key}
            onAdd={() => addOrUpdateMeasurement(group)}
            onDelete={(row) => void deleteMeasurement(group.key, row)}
            onEdit={(row) => editMeasurement(group.key, row)}
            onFormChange={(patch) => updateGroupForm(group.key, patch)}
            originFloors={sortedFloors}
            rows={draftGroups[group.key]}
          />
        ))}
      </div>
    </div>
  );
}

function MeasurementGroupCard({
  group,
  form,
  rows,
  originFloors,
  destinationFloors,
  floorLabelById,
  error,
  editingId,
  deletingId,
  onFormChange,
  onAdd,
  onEdit,
  onDelete,
}: {
  group: MeasurementGroup;
  form: MeasurementForm;
  rows: MeasurementDraftRow[];
  originFloors: ElevatorFloor[];
  destinationFloors: ElevatorFloor[];
  floorLabelById: Map<string, string>;
  error: string | null;
  editingId: string | null;
  deletingId: string | null;
  onFormChange: (patch: Partial<MeasurementForm>) => void;
  onAdd: () => void;
  onEdit: (row: MeasurementDraftRow) => void;
  onDelete: (row: MeasurementDraftRow) => void;
}) {
  return (
    <section className="border border-field-line bg-white">
      <div className="flex flex-col gap-1 border-b border-field-line p-4 sm:flex-row sm:items-center sm:justify-between">
        <h4 className="font-semibold">{group.label}</h4>
        <p className="text-sm text-field-muted">{rows.length === 1 ? "1 medición" : `${rows.length} mediciones`}</p>
      </div>

      <div className="grid gap-3 border-b border-field-line p-4 lg:grid-cols-[1fr_1fr_120px_120px_1.4fr_auto]">
        <FloorSelect floors={originFloors} label="Piso origen" onChange={(value) => onFormChange({ origin_floor_id: value })} value={form.origin_floor_id} />
        <FloorSelect floors={destinationFloors} label="Piso destino" onChange={(value) => onFormChange({ destination_floor_id: value })} value={form.destination_floor_id} />
        <MillimeterInput label="Aterrizaje mm" onChange={(value) => onFormChange({ landing_mm: value })} value={form.landing_mm} />
        <MillimeterInput label="Final mm" onChange={(value) => onFormChange({ final_mm: value })} value={form.final_mm} />
        <label className="grid gap-1 text-xs text-field-muted">
          Notas
          <input className="border border-field-line px-3 py-2 text-sm text-field-ink" onChange={(event) => onFormChange({ notes: event.currentTarget.value })} value={form.notes} />
        </label>
        <button className="self-end bg-field-ink px-4 py-2 text-sm font-semibold text-white hover:bg-field-info" onClick={onAdd} type="button">
          {editingId ? "Guardar edición" : "Agregar medición"}
        </button>
      </div>
      {error ? <p className="border-b border-field-line px-4 py-2 text-sm text-field-fail">{error}</p> : null}

      {rows.length === 0 ? (
        <p className="p-4 text-sm text-field-muted">Sin mediciones en este grupo.</p>
      ) : (
        <div className="divide-y divide-field-line">
          <div className="hidden grid-cols-[1fr_1fr_110px_110px_90px_130px_1.4fr_130px] gap-3 bg-field-bg px-4 py-2 text-xs font-semibold uppercase text-field-muted lg:grid">
            <span>Origen</span>
            <span>Destino</span>
            <span>Aterrizaje</span>
            <span>Final</span>
            <span>Reniveló</span>
            <span>Dentro de ±5 mm</span>
            <span>Notas</span>
            <span>Acciones</span>
          </div>
          {rows.map((row) => (
            <MeasurementRow
              deletingId={deletingId}
              floorLabelById={floorLabelById}
              key={row.local_id}
              onDelete={() => onDelete(row)}
              onEdit={() => onEdit(row)}
              row={row}
            />
          ))}
        </div>
      )}
    </section>
  );
}

function MeasurementRow({
  row,
  floorLabelById,
  deletingId,
  onEdit,
  onDelete,
}: {
  row: MeasurementDraftRow;
  floorLabelById: Map<string, string>;
  deletingId: string | null;
  onEdit: () => void;
  onDelete: () => void;
}) {
  const landing = parseIntegerOrNull(row.landing_mm);
  const final = parseIntegerOrNull(row.final_mm);
  const effective = final ?? landing;
  const didRelevel = final !== null && landing !== null && final !== landing;
  const withinTolerance = effective === null ? null : effective >= -5 && effective <= 5;

  return (
    <div className="grid gap-3 p-4 text-sm lg:grid-cols-[1fr_1fr_110px_110px_90px_130px_1.4fr_130px] lg:items-center">
      <MobileLabel label="Origen" value={floorLabelById.get(row.origin_floor_id) ?? "Piso"} />
      <MobileLabel label="Destino" value={floorLabelById.get(row.destination_floor_id) ?? "Piso"} />
      <MobileLabel className={millimeterTextClass(row.landing_mm)} label="Aterrizaje" value={formatMillimeters(landing)} />
      <MobileLabel className={millimeterTextClass(row.final_mm)} label="Final" value={formatMillimeters(final)} />
      <MobileLabel label="Reniveló" value={didRelevel ? "Sí" : "No"} />
      <span className={`font-semibold ${withinTolerance === true ? "text-field-ok" : withinTolerance === false ? "text-field-fail" : "text-field-muted"}`}>
        <span className="mr-2 text-xs font-normal text-field-muted lg:hidden">Dentro de ±5 mm</span>
        {withinTolerance === null ? "Sin valor" : withinTolerance ? "OK" : "Fuera de tolerancia"}
      </span>
      <MobileLabel label="Notas" value={row.notes || "Sin notas"} />
      <div className="flex gap-2">
        <button className="border border-field-line px-3 py-2 text-xs font-semibold hover:bg-field-bg" onClick={onEdit} type="button">
          Editar
        </button>
        <button className="border border-field-line px-3 py-2 text-xs font-semibold text-field-fail hover:bg-field-bg disabled:opacity-60" disabled={deletingId === row.local_id} onClick={onDelete} type="button">
          {deletingId === row.local_id ? "Eliminando" : "Eliminar"}
        </button>
      </div>
    </div>
  );
}

function SummaryItem({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="border border-field-line bg-white px-3 py-2">
      <p className="text-xs text-field-muted">{label}</p>
      <p className="font-semibold">{value}</p>
    </div>
  );
}

function FloorSelect({ label, floors, value, onChange }: { label: string; floors: ElevatorFloor[]; value: string; onChange: (value: string) => void }) {
  return (
    <label className="grid gap-1 text-xs text-field-muted">
      {label}
      <select className="border border-field-line px-3 py-2 text-sm text-field-ink" onChange={(event) => onChange(event.currentTarget.value)} value={value}>
        <option value="">Seleccionar</option>
        {floors.map((floor) => (
          <option key={floor.id} value={floor.id}>
            {floorLabel(floor)}
          </option>
        ))}
      </select>
    </label>
  );
}

function MillimeterInput({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return (
    <label className="grid gap-1 text-xs text-field-muted">
      {label}
      <input className={`border border-field-line px-3 py-2 text-sm ${millimeterTextClass(value)}`} onChange={(event) => onChange(event.currentTarget.value)} type="number" value={value} />
    </label>
  );
}

function MobileLabel({ label, value, className = "" }: { label: string; value: string; className?: string }) {
  return (
    <span className={className}>
      <span className="mr-2 text-xs text-field-muted lg:hidden">{label}</span>
      {value}
    </span>
  );
}

function validateMeasurementForm(form: MeasurementForm): string | null {
  if (!form.origin_floor_id) {
    return "Selecciona el piso de origen.";
  }
  if (!form.destination_floor_id) {
    return "Selecciona el piso de destino.";
  }
  if (form.origin_floor_id === form.destination_floor_id) {
    return "El origen y el destino deben ser diferentes.";
  }
  if (form.landing_mm.trim() === "") {
    return "Ingresa la medida de aterrizaje.";
  }
  if (parseIntegerOrNull(form.landing_mm) === null) {
    return "La medida de aterrizaje debe ser un número entero.";
  }
  if (form.final_mm.trim() !== "" && parseIntegerOrNull(form.final_mm) === null) {
    return "La medida final debe ser un número entero.";
  }
  return null;
}

function groupsFromMeasurements(measurements: LevelingMeasurement[]): DraftGroups {
  const groups = emptyDraftGroups();
  for (const measurement of measurements) {
    const key = `${measurement.travel_type}:${measurement.direction}` as GroupKey;
    groups[key].push({
      local_id: measurement.id,
      measurement_id: measurement.id,
      origin_floor_id: measurement.origin_floor_id,
      destination_floor_id: measurement.destination_floor_id,
      landing_mm: toInputValue(measurement.landing_mm),
      final_mm: toInputValue(measurement.final_mm),
      notes: measurement.notes ?? "",
    });
  }
  return groups;
}

function normalizeDraftGroups(candidate: Partial<DraftGroups>): DraftGroups {
  const groups = emptyDraftGroups();
  for (const group of measurementGroups) {
    groups[group.key] = Array.isArray(candidate[group.key]) ? candidate[group.key]! : [];
  }
  return groups;
}

function buildSummaryFromDraft(groups: DraftGroups): LevelingMeasurementSummary {
  const rows = Object.values(groups).flat();
  const effectiveValues = rows.map((row) => effectiveFinal(row)).filter((value): value is number => value !== null);
  const withinTolerance = effectiveValues.filter((value) => value >= -5 && value <= 5).length;
  const outsideTolerance = effectiveValues.length - withinTolerance;

  return {
    total: rows.length,
    with_values: effectiveValues.length,
    within_tolerance: withinTolerance,
    outside_tolerance: outsideTolerance,
    within_tolerance_percentage: effectiveValues.length ? roundPercentage((withinTolerance / effectiveValues.length) * 100) : 0,
  };
}

function floorLabel(floor: ElevatorFloor): string {
  return floor.label ?? String(floor.sort_order);
}

function toInputValue(value: number | null | undefined): string {
  return value === null || value === undefined ? "" : String(value);
}

function parseIntegerOrNull(value: string | undefined): number | null {
  if (value === undefined || value.trim() === "") {
    return null;
  }
  const parsed = Number(value);
  return Number.isInteger(parsed) ? parsed : null;
}

function effectiveFinal(row: MeasurementDraftRow): number | null {
  const final = parseIntegerOrNull(row.final_mm);
  if (final !== null) {
    return final;
  }
  return parseIntegerOrNull(row.landing_mm);
}

function formatMillimeters(value: number | null): string {
  if (value === null) {
    return "Sin valor";
  }
  return `${value > 0 ? "+" : ""}${value} mm`;
}

function millimeterTextClass(value: string): string {
  const parsed = parseIntegerOrNull(value);
  if (parsed === null || parsed === 0) {
    return "text-field-ink";
  }
  return parsed > 0 ? "text-field-info" : "text-field-warn";
}

function roundPercentage(value: number): number {
  return Math.round(value * 100) / 100;
}
