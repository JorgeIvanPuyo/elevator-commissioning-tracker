"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";

import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";
import { fromDatetimeLocalValue } from "@/lib/hex";
import type { Elevator, ElevatorFloor, TestRun, TestRunStatus, TestType } from "@/types/api";

const statusLabels: Record<TestRunStatus, string> = {
  draft: "Borrador",
  in_progress: "En proceso",
  completed: "Completada",
  cancelled: "Cancelada",
};

export function ElevatorDetailClient({ elevatorId }: { elevatorId: string }) {
  const [elevator, setElevator] = useState<Elevator | null>(null);
  const [floors, setFloors] = useState<ElevatorFloor[]>([]);
  const [testRuns, setTestRuns] = useState<TestRun[]>([]);
  const [testTypes, setTestTypes] = useState<TestType[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSavingTestRun, setIsSavingTestRun] = useState(false);
  const [savingFloorId, setSavingFloorId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function loadElevator() {
    setIsLoading(true);
    setError(null);
    try {
      const [elevatorResponse, floorResponse, testRunResponse, testTypeResponse] = await Promise.all([
        api.getElevator(elevatorId),
        api.listElevatorFloors(elevatorId),
        api.listElevatorTestRuns(elevatorId),
        api.listTestTypes(),
      ]);
      setElevator(elevatorResponse);
      setFloors(floorResponse);
      setTestRuns(testRunResponse);
      setTestTypes(testTypeResponse);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "No se pudo cargar el elevador");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadElevator();
  }, [elevatorId]);

  async function updateFloor(floor: ElevatorFloor, payload: Partial<Pick<ElevatorFloor, "label" | "is_served" | "is_leveling_required">>) {
    setSavingFloorId(floor.id);
    setError(null);
    try {
      const updatedFloor = await api.updateElevatorFloor(floor.id, payload);
      setFloors((current) => current.map((item) => (item.id === updatedFloor.id ? updatedFloor : item)));
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "No se pudo actualizar el piso");
    } finally {
      setSavingFloorId(null);
    }
  }

  async function handleCreateTestRun(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSavingTestRun(true);
    setError(null);
    const form = new FormData(event.currentTarget);

    try {
      await api.createTestRun(elevatorId, {
        test_type_id: String(form.get("test_type_id") || ""),
        technician_name: String(form.get("technician_name") || ""),
        status: String(form.get("status") || "draft") as TestRunStatus,
        started_at: fromDatetimeLocalValue(form.get("started_at")),
        completed_at: fromDatetimeLocalValue(form.get("completed_at")),
        title: String(form.get("title") || "") || null,
        summary: String(form.get("summary") || "") || null,
        notes: String(form.get("notes") || "") || null,
      });
      event.currentTarget.reset();
      await loadElevator();
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "No se pudo crear la prueba");
    } finally {
      setIsSavingTestRun(false);
    }
  }

  return (
    <AppShell>
      {isLoading ? <p className="text-sm text-field-muted">Cargando elevador...</p> : null}
      {error ? <p className="border border-field-fail bg-white p-3 text-sm text-field-fail">{error}</p> : null}

      {elevator ? (
        <>
          <div className="border-b border-field-line pb-5">
            <p className="text-sm font-medium text-field-muted">{elevator.code}</p>
            <h2 className="mt-2 text-3xl font-semibold">{elevator.name || elevator.code}</h2>
            <div className="mt-4 flex flex-wrap gap-2 text-sm">
              <span className="border border-field-line bg-white px-3 py-2">{elevator.status}</span>
              <span className="border border-field-line bg-white px-3 py-2">{elevator.floor_count} pisos</span>
              <span className="border border-field-line bg-white px-3 py-2">{elevator.controller_model || "Controlador pendiente"}</span>
            </div>
          </div>

          <div className="mt-6 grid gap-4 md:grid-cols-3">
            <div className="border border-field-line bg-white p-4 shadow-panel">
              <p className="text-sm font-semibold">Pruebas</p>
              <p className="mt-2 text-sm text-field-muted">{testRuns.length} iteraciones registradas</p>
            </div>
            <div className="border border-field-line bg-white p-4 shadow-panel">
              <p className="text-sm font-semibold">Nivelación</p>
              <p className="mt-2 text-sm text-field-muted">Pendiente</p>
            </div>
            <div className="border border-field-line bg-white p-4 shadow-panel">
              <p className="text-sm font-semibold">Evidencias</p>
              <p className="mt-2 text-sm text-field-muted">Pendiente</p>
            </div>
          </div>

          <div className="mt-6 border border-field-line bg-white shadow-panel">
            <div className="border-b border-field-line p-4">
              <h3 className="text-lg font-semibold">Pruebas técnicas</h3>
              <p className="mt-1 text-sm text-field-muted">Iteraciones de carga, nivelación y ajustes de parámetros.</p>
            </div>

            <form className="grid gap-3 border-b border-field-line p-4 md:grid-cols-3" onSubmit={handleCreateTestRun}>
              <select className="border border-field-line px-3 py-3 text-sm" name="test_type_id" required>
                <option value="">Tipo de prueba</option>
                {testTypes.map((testType) => (
                  <option key={testType.id} value={testType.id}>
                    {testType.name}
                  </option>
                ))}
              </select>
              <input className="border border-field-line px-3 py-3 text-sm" name="technician_name" placeholder="Responsable" required />
              <select className="border border-field-line px-3 py-3 text-sm" defaultValue="draft" name="status">
                <option value="draft">Borrador</option>
                <option value="in_progress">En proceso</option>
                <option value="completed">Completada</option>
                <option value="cancelled">Cancelada</option>
              </select>
              <input className="border border-field-line px-3 py-3 text-sm" name="started_at" type="datetime-local" />
              <input className="border border-field-line px-3 py-3 text-sm" name="completed_at" type="datetime-local" />
              <input className="border border-field-line px-3 py-3 text-sm" name="title" placeholder="Título" />
              <textarea className="border border-field-line px-3 py-3 text-sm md:col-span-3" name="summary" placeholder="Resumen técnico" rows={2} />
              <textarea className="border border-field-line px-3 py-3 text-sm md:col-span-3" name="notes" placeholder="Notas" rows={2} />
              <button className="bg-field-info px-4 py-3 text-sm font-semibold text-white hover:bg-field-ink md:col-span-3" disabled={isSavingTestRun}>
                {isSavingTestRun ? "Creando..." : "Nueva prueba"}
              </button>
            </form>

            {testRuns.length === 0 ? <p className="p-4 text-sm text-field-muted">No hay pruebas registradas para este elevador.</p> : null}

            <div className="grid gap-0">
              {testRuns.map((testRun) => (
                <Link
                  className="grid gap-2 border-b border-field-line p-4 hover:bg-field-bg md:grid-cols-[1fr_120px_180px]"
                  href={`/test-runs/${testRun.id}`}
                  key={testRun.id}
                >
                  <div>
                    <p className="text-sm font-semibold">{testRun.title || testRun.test_type_name}</p>
                    <p className="mt-1 text-sm text-field-muted">{testRun.summary || testRun.notes || "Sin resumen técnico"}</p>
                  </div>
                  <span className="text-sm">{statusLabels[testRun.status]}</span>
                  <span className="text-sm text-field-muted">{testRun.technician_name}</span>
                </Link>
              ))}
            </div>
          </div>

          <div className="mt-6 border border-field-line bg-white shadow-panel">
            <div className="border-b border-field-line p-4">
              <h3 className="text-lg font-semibold">Pisos del elevador</h3>
              <p className="mt-1 text-sm text-field-muted">Labels y flags editables por elevador.</p>
            </div>
            <div className="grid gap-0">
              {floors.map((floor) => (
                <div className="grid gap-3 border-b border-field-line p-4 md:grid-cols-[80px_1fr_130px_170px]" key={floor.id}>
                  <span className="text-sm font-semibold">#{floor.sort_order}</span>
                  <input
                    className="border border-field-line px-3 py-2 text-sm"
                    defaultValue={floor.label ?? ""}
                    disabled={savingFloorId === floor.id}
                    onBlur={(event) => {
                      if (event.currentTarget.value !== (floor.label ?? "")) {
                        void updateFloor(floor, { label: event.currentTarget.value });
                      }
                    }}
                  />
                  <label className="flex items-center gap-2 text-sm">
                    <input
                      checked={floor.is_served}
                      disabled={savingFloorId === floor.id}
                      onChange={(event) => void updateFloor(floor, { is_served: event.currentTarget.checked })}
                      type="checkbox"
                    />
                    Atiende
                  </label>
                  <label className="flex items-center gap-2 text-sm">
                    <input
                      checked={floor.is_leveling_required}
                      disabled={savingFloorId === floor.id || !floor.is_served}
                      onChange={(event) => void updateFloor(floor, { is_leveling_required: event.currentTarget.checked })}
                      type="checkbox"
                    />
                    Requiere nivelación
                  </label>
                </div>
              ))}
            </div>
          </div>

          <Link className="mt-6 inline-flex border border-field-line bg-white px-4 py-3 text-sm font-semibold" href={`/projects/${elevator.project_id}`}>
            Volver al proyecto
          </Link>
        </>
      ) : null}
    </AppShell>
  );
}
