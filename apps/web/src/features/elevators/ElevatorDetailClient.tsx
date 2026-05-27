"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";
import type { Elevator, ElevatorFloor } from "@/types/api";

const futureLinks = ["Pruebas", "Nivelación", "Parámetros", "Evidencias"];

export function ElevatorDetailClient({ elevatorId }: { elevatorId: string }) {
  const [elevator, setElevator] = useState<Elevator | null>(null);
  const [floors, setFloors] = useState<ElevatorFloor[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [savingFloorId, setSavingFloorId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadElevator() {
      setIsLoading(true);
      setError(null);
      try {
        const [elevatorResponse, floorResponse] = await Promise.all([api.getElevator(elevatorId), api.listElevatorFloors(elevatorId)]);
        setElevator(elevatorResponse);
        setFloors(floorResponse);
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : "No se pudo cargar el elevador");
      } finally {
        setIsLoading(false);
      }
    }

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

          <div className="mt-6 grid gap-4 md:grid-cols-4">
            {futureLinks.map((label) => (
              <div className="border border-field-line bg-white p-4 shadow-panel" key={label}>
                <p className="text-sm font-semibold">{label}</p>
                <p className="mt-2 text-sm text-field-muted">Pendiente</p>
              </div>
            ))}
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
