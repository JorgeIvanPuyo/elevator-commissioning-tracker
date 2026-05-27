"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";

import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";
import type { Elevator, Project } from "@/types/api";

export function ProjectDetailClient({ projectId }: { projectId: string }) {
  const [project, setProject] = useState<Project | null>(null);
  const [elevators, setElevators] = useState<Elevator[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadProject() {
    setIsLoading(true);
    setError(null);
    try {
      const [projectResponse, elevatorResponse] = await Promise.all([
        api.getProject(projectId),
        api.listProjectElevators(projectId),
      ]);
      setProject(projectResponse);
      setElevators(elevatorResponse);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "No se pudo cargar el proyecto");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadProject();
  }, [projectId]);

  async function handleCreateElevator(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formElement = event.currentTarget;
    setIsSaving(true);
    setError(null);

    const form = new FormData(formElement);
    const floorCount = Number(form.get("floor_count") || 0);

    try {
      await api.createElevator(projectId, {
        code: String(form.get("code") || ""),
        name: String(form.get("name") || ""),
        floor_count: floorCount || undefined,
        controller_model: String(form.get("controller_model") || ""),
        machine_room: String(form.get("machine_room") || ""),
      });
      formElement.reset();
      await loadProject();
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "No se pudo crear el elevador");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <AppShell>
      {isLoading ? <p className="text-sm text-field-muted">Cargando proyecto...</p> : null}
      {error ? <p className="border border-field-fail bg-white p-3 text-sm text-field-fail">{error}</p> : null}

      {project ? (
        <>
          <div className="border-b border-field-line pb-5">
            <p className="text-sm font-medium text-field-muted">{project.client_name || "Cliente pendiente"}</p>
            <h2 className="mt-2 text-3xl font-semibold">{project.name}</h2>
            <div className="mt-4 flex flex-wrap gap-2 text-sm">
              <span className="border border-field-line bg-white px-3 py-2">{project.status}</span>
              <span className="border border-field-line bg-white px-3 py-2">{project.default_floor_count} pisos base</span>
              <span className="border border-field-line bg-white px-3 py-2">{elevators.length} elevadores registrados</span>
            </div>
          </div>

          <form className="mt-6 grid gap-3 border border-field-line bg-white p-4 shadow-panel md:grid-cols-5" onSubmit={handleCreateElevator}>
            <input className="border border-field-line px-3 py-3 text-sm" name="code" placeholder="Código" required />
            <input className="border border-field-line px-3 py-3 text-sm" name="name" placeholder="Nombre" />
            <input
              className="border border-field-line px-3 py-3 text-sm"
              defaultValue={project.default_floor_count}
              min={1}
              name="floor_count"
              placeholder="Pisos"
              type="number"
            />
            <input className="border border-field-line px-3 py-3 text-sm" name="controller_model" placeholder="Controlador" />
            <input className="border border-field-line px-3 py-3 text-sm" name="machine_room" placeholder="Cuarto de máquinas" />
            <button className="bg-field-info px-4 py-3 text-sm font-semibold text-white hover:bg-field-ink md:col-span-5" disabled={isSaving}>
              {isSaving ? "Creando..." : "Crear elevador"}
            </button>
          </form>

          {elevators.length === 0 ? (
            <div className="mt-6 border border-field-line bg-white p-6 text-sm text-field-muted shadow-panel">No hay elevadores registrados.</div>
          ) : null}

          <div className="mt-6 grid gap-4 md:grid-cols-2">
            {elevators.map((elevator) => (
              <Link
                className="border border-field-line bg-white p-4 shadow-panel hover:border-field-info"
                href={`/elevators/${elevator.id}`}
                key={elevator.id}
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h3 className="text-lg font-semibold">{elevator.name || elevator.code}</h3>
                    <p className="mt-1 text-sm text-field-muted">{elevator.code}</p>
                  </div>
                  <span className="border border-field-line px-2 py-1 text-xs font-medium">{elevator.status}</span>
                </div>
                <p className="mt-4 text-sm text-field-muted">{elevator.floor_count} pisos</p>
              </Link>
            ))}
          </div>
        </>
      ) : null}
    </AppShell>
  );
}
