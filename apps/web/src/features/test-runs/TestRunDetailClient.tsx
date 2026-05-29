"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";

import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";
import { fromDatetimeLocalValue, previewHexDecimal, toDatetimeLocalValue } from "@/lib/hex";
import { LevelingMeasurementEditor } from "@/features/test-runs/LevelingMeasurementEditor";
import { LevelingSummaryPanel } from "@/features/test-runs/LevelingSummaryPanel";
import { TechnicalParameterMatrix } from "@/features/test-runs/TechnicalParameterMatrix";
import { TestRunComparisonPanel } from "@/features/test-runs/TestRunComparisonPanel";
import { ZoneLevelingAnalysisPanel } from "@/features/test-runs/ZoneLevelingAnalysisPanel";
import type {
  ComparisonCandidate,
  Elevator,
  LevelingSummary,
  ParameterDefinition,
  ParameterValidationWarning,
  TestRun,
  TestRunParameterValue,
  TestRunParameterValueInput,
  TestRunProcessStep,
  TestRunStatus,
  TestType,
  ZoneLevelingAnalysis,
} from "@/types/api";

const statusLabels: Record<TestRunStatus, string> = {
  draft: "Borrador",
  in_progress: "En proceso",
  completed: "Completada",
  cancelled: "Cancelada",
};

type ParameterDraft = {
  hex_value: string;
  source: string;
  notes: string;
};

type DraftByCode = Record<string, ParameterDraft>;

export function TestRunDetailClient({ testRunId }: { testRunId: string }) {
  const [testRun, setTestRun] = useState<TestRun | null>(null);
  const [elevator, setElevator] = useState<Elevator | null>(null);
  const [testTypes, setTestTypes] = useState<TestType[]>([]);
  const [definitions, setDefinitions] = useState<ParameterDefinition[]>([]);
  const [savedValues, setSavedValues] = useState<TestRunParameterValue[]>([]);
  const [processSteps, setProcessSteps] = useState<TestRunProcessStep[]>([]);
  const [levelingSummary, setLevelingSummary] = useState<LevelingSummary | null>(null);
  const [zoneLevelingAnalysis, setZoneLevelingAnalysis] = useState<ZoneLevelingAnalysis | null>(null);
  const [comparisonCandidates, setComparisonCandidates] = useState<ComparisonCandidate[]>([]);
  const [parameterWarnings, setParameterWarnings] = useState<ParameterValidationWarning[]>([]);
  const [draft, setDraft] = useState<DraftByCode>({});
  const [hasLocalDraft, setHasLocalDraft] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isSavingRun, setIsSavingRun] = useState(false);
  const [isSavingParameters, setIsSavingParameters] = useState(false);
  const [savingProcessStepId, setSavingProcessStepId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [parameterError, setParameterError] = useState<string | null>(null);

  const draftKey = `elevator-commissioning:test-run:${testRunId}:parameters-draft`;

  async function loadTestRun() {
    setIsLoading(true);
    setError(null);
    try {
      const [
        runResponse,
        definitionResponse,
        parameterResponse,
        typeResponse,
        processStepResponse,
        levelingSummaryResponse,
        zoneLevelingAnalysisResponse,
        comparisonCandidateResponse,
      ] = await Promise.all([
        api.getTestRun(testRunId),
        api.listParameterDefinitions(),
        api.listTestRunParameters(testRunId),
        api.listTestTypes(),
        api.listTestRunProcessSteps(testRunId),
        api.getLevelingSummary(testRunId),
        api.getZoneLevelingAnalysis(testRunId),
        api.listComparisonCandidates(testRunId),
      ]);
      const elevatorResponse = await api.getElevator(runResponse.elevator_id);
      setTestRun(runResponse);
      setElevator(elevatorResponse);
      setDefinitions(definitionResponse);
      setSavedValues(parameterResponse.values);
      setParameterWarnings(parameterResponse.validation_warnings);
      setProcessSteps(processStepResponse);
      setLevelingSummary(levelingSummaryResponse);
      setZoneLevelingAnalysis(zoneLevelingAnalysisResponse);
      setComparisonCandidates(comparisonCandidateResponse);
      setTestTypes(typeResponse);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "No se pudo cargar la prueba");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadTestRun();
  }, [testRunId]);

  async function refreshLevelingSummary() {
    try {
      const [summaryResponse, zoneAnalysisResponse] = await Promise.all([api.getLevelingSummary(testRunId), api.getZoneLevelingAnalysis(testRunId)]);
      setLevelingSummary(summaryResponse);
      setZoneLevelingAnalysis(zoneAnalysisResponse);
    } catch (summaryError) {
      setError(summaryError instanceof Error ? summaryError.message : "No se pudo actualizar el resumen de nivelación");
    }
  }

  useEffect(() => {
    if (definitions.length === 0) {
      return;
    }

    const savedByCode = Object.fromEntries(savedValues.map((value) => [value.parameter_code, value]));
    const initialDraft = Object.fromEntries(
      definitions.map((definition) => {
        const saved = savedByCode[definition.code];
        return [
          definition.code,
          {
            hex_value: saved?.hex_value ?? "",
            source: saved?.source ?? "manual",
            notes: saved?.notes ?? "",
          },
        ];
      }),
    );

    const localValue = window.localStorage.getItem(draftKey);
    if (localValue) {
      try {
        setDraft({ ...initialDraft, ...(JSON.parse(localValue) as DraftByCode) });
        setHasLocalDraft(true);
        return;
      } catch {
        window.localStorage.removeItem(draftKey);
      }
    }

    setDraft(initialDraft);
    setHasLocalDraft(false);
  }, [definitions, savedValues, draftKey]);

  useEffect(() => {
    if (Object.keys(draft).length === 0) {
      return;
    }
    window.localStorage.setItem(draftKey, JSON.stringify(draft));
  }, [draft, draftKey]);

  const invalidCodes = useMemo(
    () => definitions.filter((definition) => previewHexDecimal(draft[definition.code]?.hex_value ?? "").error).map((definition) => definition.code),
    [definitions, draft],
  );

  function updateDraft(code: string, patch: Partial<ParameterDraft>) {
    setHasLocalDraft(true);
    setDraft((current) => ({ ...current, [code]: { ...current[code], ...patch } }));
  }

  async function handleUpdateTestRun(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!testRun) {
      return;
    }

    setIsSavingRun(true);
    setError(null);
    const form = new FormData(event.currentTarget);

    try {
      const updated = await api.updateTestRun(testRun.id, {
        test_type_id: String(form.get("test_type_id") || ""),
        technician_name: String(form.get("technician_name") || ""),
        status: String(form.get("status") || "draft") as TestRunStatus,
        started_at: fromDatetimeLocalValue(form.get("started_at")),
        completed_at: fromDatetimeLocalValue(form.get("completed_at")),
        title: String(form.get("title") || "") || null,
        summary: String(form.get("summary") || "") || null,
        notes: String(form.get("notes") || "") || null,
      });
      setTestRun(updated);
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "No se pudo actualizar la prueba");
    } finally {
      setIsSavingRun(false);
    }
  }

  async function handleSaveParameters() {
    if (invalidCodes.length > 0) {
      setParameterError(`Corrige HEX inválido en: ${invalidCodes.join(", ")}`);
      return;
    }

    setIsSavingParameters(true);
    setParameterError(null);

    const savedCodes = new Set(savedValues.map((value) => value.parameter_code));
    const values: TestRunParameterValueInput[] = definitions
      .map((definition) => {
        const row = draft[definition.code] ?? { hex_value: "", source: "manual", notes: "" };
        return {
          parameter_code: definition.code,
          hex_value: row.hex_value || null,
          source: row.source || null,
          notes: row.notes || null,
        };
      })
      .filter((value) => value.hex_value || value.notes || savedCodes.has(value.parameter_code));

    try {
      const response = await api.saveTestRunParameters(testRunId, values);
      setSavedValues(response.values);
      setParameterWarnings(response.validation_warnings);
      setZoneLevelingAnalysis(await api.getZoneLevelingAnalysis(testRunId));
      window.localStorage.removeItem(draftKey);
      setHasLocalDraft(false);
    } catch (saveError) {
      setParameterError(saveError instanceof Error ? saveError.message : "No se pudieron guardar los parámetros");
    } finally {
      setIsSavingParameters(false);
    }
  }

  async function updateProcessStep(processStep: TestRunProcessStep, patch: Partial<Pick<TestRunProcessStep, "is_completed" | "notes">>) {
    setSavingProcessStepId(processStep.id);
    setError(null);
    try {
      const updated = await api.updateTestRunProcessStep(processStep.id, patch);
      setProcessSteps((current) => current.map((item) => (item.id === updated.id ? updated : item)));
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "No se pudo actualizar el proceso");
    } finally {
      setSavingProcessStepId(null);
    }
  }

  return (
    <AppShell>
      {isLoading ? <p className="text-sm text-field-muted">Cargando prueba...</p> : null}
      {error ? <p className="border border-field-fail bg-white p-3 text-sm text-field-fail">{error}</p> : null}

      {testRun ? (
        <>
          <div className="border-b border-field-line pb-5">
            <p className="text-sm font-medium text-field-muted">
              {elevator ? `${elevator.code} · ${elevator.name || elevator.code}` : "Elevador"}
            </p>
            <h2 className="mt-2 text-3xl font-semibold">{testRun.title || testRun.test_type_name}</h2>
            <div className="mt-4 flex flex-wrap gap-2 text-sm">
              <span className="border border-field-line bg-white px-3 py-2">{statusLabels[testRun.status]}</span>
              <span className="border border-field-line bg-white px-3 py-2">{testRun.test_type_name}</span>
              <span className="border border-field-line bg-white px-3 py-2">{testRun.technician_name}</span>
            </div>
          </div>

          <form className="mt-6 grid gap-3 border border-field-line bg-white p-4 shadow-panel md:grid-cols-3" onSubmit={handleUpdateTestRun}>
            <select className="border border-field-line px-3 py-3 text-sm" defaultValue={testRun.test_type_id} name="test_type_id" required>
              {testTypes.map((testType) => (
                <option key={testType.id} value={testType.id}>
                  {testType.name}
                </option>
              ))}
            </select>
            <input className="border border-field-line px-3 py-3 text-sm" defaultValue={testRun.technician_name} name="technician_name" required />
            <select className="border border-field-line px-3 py-3 text-sm" defaultValue={testRun.status} name="status">
              <option value="draft">Borrador</option>
              <option value="in_progress">En proceso</option>
              <option value="completed">Completada</option>
              <option value="cancelled">Cancelada</option>
            </select>
            <input
              className="border border-field-line px-3 py-3 text-sm"
              defaultValue={toDatetimeLocalValue(testRun.started_at)}
              name="started_at"
              type="datetime-local"
            />
            <input
              className="border border-field-line px-3 py-3 text-sm"
              defaultValue={toDatetimeLocalValue(testRun.completed_at)}
              name="completed_at"
              type="datetime-local"
            />
            <input className="border border-field-line px-3 py-3 text-sm" defaultValue={testRun.title ?? ""} name="title" placeholder="Título" />
            <textarea className="border border-field-line px-3 py-3 text-sm md:col-span-3" defaultValue={testRun.summary ?? ""} name="summary" rows={2} />
            <textarea className="border border-field-line px-3 py-3 text-sm md:col-span-3" defaultValue={testRun.notes ?? ""} name="notes" rows={2} />
            <button className="bg-field-info px-4 py-3 text-sm font-semibold text-white hover:bg-field-ink md:col-span-3" disabled={isSavingRun}>
              {isSavingRun ? "Guardando..." : "Guardar datos de prueba"}
            </button>
          </form>

          <div className="mt-6 border border-field-line bg-white shadow-panel">
            <div className="border-b border-field-line p-4">
              <h3 className="text-lg font-semibold">Procesos ejecutados</h3>
              <p className="mt-1 text-sm text-field-muted">A61E-A67E son pasos técnicos, no parámetros HEX editables.</p>
            </div>
            <div className="grid gap-0">
              {processSteps.map((processStep) => (
                <div className="grid gap-3 border-b border-field-line p-4 md:grid-cols-[90px_1fr_160px_1fr]" key={processStep.id}>
                  <span className="text-sm font-semibold">{processStep.code}</span>
                  <div>
                    <p className="text-sm font-medium">{processStep.name}</p>
                    <p className="mt-1 text-sm text-field-muted">{processStep.description}</p>
                  </div>
                  <label className="flex items-center gap-2 text-sm">
                    <input
                      checked={processStep.is_completed}
                      disabled={savingProcessStepId === processStep.id}
                      onChange={(event) => void updateProcessStep(processStep, { is_completed: event.currentTarget.checked })}
                      type="checkbox"
                    />
                    Completado
                  </label>
                  <input
                    className="border border-field-line px-3 py-2 text-sm"
                    defaultValue={processStep.notes ?? ""}
                    disabled={savingProcessStepId === processStep.id}
                    onBlur={(event) => {
                      if (event.currentTarget.value !== (processStep.notes ?? "")) {
                        void updateProcessStep(processStep, { notes: event.currentTarget.value });
                      }
                    }}
                    placeholder="Notas del proceso"
                  />
                </div>
              ))}
            </div>
          </div>

          <TechnicalParameterMatrix analysis={zoneLevelingAnalysis} draftValues={draft} />

          <div className="mt-6 border border-field-line bg-white shadow-panel" id="parameter-editor">
            <div className="flex flex-col gap-3 border-b border-field-line p-4 md:flex-row md:items-center md:justify-between">
              <div>
                <h3 className="text-lg font-semibold">Parámetros HEX</h3>
                <p className="mt-1 text-sm text-field-muted">Valores normalizados en backend con conversión decimal.</p>
              </div>
              <button className="bg-field-info px-4 py-3 text-sm font-semibold text-white hover:bg-field-ink" disabled={isSavingParameters} onClick={handleSaveParameters}>
                {isSavingParameters ? "Guardando..." : "Guardar parámetros"}
              </button>
            </div>

            {hasLocalDraft ? <p className="border-b border-field-line bg-field-bg p-3 text-sm text-field-warn">Hay cambios locales sin guardar.</p> : null}
            {parameterError ? <p className="border-b border-field-line p-3 text-sm text-field-fail">{parameterError}</p> : null}
            {parameterWarnings.length > 0 ? (
              <div className="grid gap-2 border-b border-field-line bg-field-bg p-3">
                {parameterWarnings.map((warning) => (
                  <p className="text-sm text-field-warn" key={`${warning.type}-${warning.parameter_code}-${warning.paired_parameter_code}`}>
                    {warning.message}
                  </p>
                ))}
              </div>
            ) : null}

            <div className="grid gap-0">
              {definitions.map((definition) => {
                const row = draft[definition.code] ?? { hex_value: "", source: "manual", notes: "" };
                const preview = previewHexDecimal(row.hex_value);
                const fieldWarnings = parameterWarnings.filter(
                  (warning) => warning.parameter_code === definition.code || warning.paired_parameter_code === definition.code,
                );
                return (
                  <div className="grid gap-3 border-b border-field-line p-4 lg:grid-cols-[90px_1fr_120px_120px_140px_1fr]" key={definition.id}>
                    <span className="text-sm font-semibold">{definition.code}</span>
                    <span className="text-sm">
                      {definition.name}
                      {definition.bound_type ? <span className="ml-2 text-xs uppercase text-field-muted">{definition.bound_type}</span> : null}
                    </span>
                    <div>
                      <input
                        className="w-full border border-field-line px-3 py-2 text-sm uppercase"
                        onChange={(event) => updateDraft(definition.code, { hex_value: event.currentTarget.value })}
                        value={row.hex_value}
                      />
                      {preview.error ? <p className="mt-1 text-xs text-field-fail">{preview.error}</p> : null}
                      {fieldWarnings.map((warning) => (
                        <p className="mt-1 text-xs text-field-warn" key={warning.message}>
                          {warning.message}
                        </p>
                      ))}
                    </div>
                    <span className="text-sm text-field-muted">{preview.decimal === null ? "-" : preview.decimal}</span>
                    <input
                      className="border border-field-line px-3 py-2 text-sm"
                      onChange={(event) => updateDraft(definition.code, { source: event.currentTarget.value })}
                      value={row.source}
                    />
                    <input
                      className="border border-field-line px-3 py-2 text-sm"
                      onChange={(event) => updateDraft(definition.code, { notes: event.currentTarget.value })}
                      placeholder="Notas"
                      value={row.notes}
                    />
                  </div>
                );
              })}
            </div>
          </div>

          <LevelingSummaryPanel summary={levelingSummary} />

          <ZoneLevelingAnalysisPanel analysis={zoneLevelingAnalysis} />

          <TestRunComparisonPanel candidates={comparisonCandidates} testRunId={testRun.id} />

          <LevelingMeasurementEditor onMeasurementsChanged={refreshLevelingSummary} testRun={testRun} />

          <div className="mt-6 flex flex-wrap gap-3">
            <Link className="inline-flex border border-field-line bg-white px-4 py-3 text-sm font-semibold" href={`/elevators/${testRun.elevator_id}`}>
              Volver al elevador
            </Link>
            <span className="border border-field-line bg-white px-4 py-3 text-sm text-field-muted">Pruebas · Nivelación · Evidencias</span>
          </div>
        </>
      ) : null}
    </AppShell>
  );
}
