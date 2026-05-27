"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";

import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";
import type { Project } from "@/types/api";

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadProjects() {
    setIsLoading(true);
    setError(null);
    try {
      setProjects(await api.listProjects());
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "No se pudo cargar proyectos");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadProjects();
  }, []);

  async function handleCreateProject(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formElement = event.currentTarget;
    setIsSaving(true);
    setError(null);

    const form = new FormData(formElement);
    const totalElevators = Number(form.get("total_elevators") || 0);
    const defaultFloorCount = Number(form.get("default_floor_count") || 62);

    try {
      await api.createProject({
        name: String(form.get("name") || ""),
        client_name: String(form.get("client_name") || ""),
        location: String(form.get("location") || ""),
        total_elevators: totalElevators || undefined,
        default_floor_count: defaultFloorCount,
      });
      formElement.reset();
      await loadProjects();
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "No se pudo crear el proyecto");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <AppShell>
      <div className="border-b border-field-line pb-5">
        <p className="text-sm font-medium text-field-muted">Base operativa</p>
        <h2 className="mt-2 text-3xl font-semibold">Proyectos</h2>
      </div>

      <form className="mt-6 grid gap-3 border border-field-line bg-white p-4 shadow-panel md:grid-cols-5" onSubmit={handleCreateProject}>
        <input className="border border-field-line px-3 py-3 text-sm md:col-span-2" name="name" placeholder="Nombre del proyecto" required />
        <input className="border border-field-line px-3 py-3 text-sm" name="client_name" placeholder="Cliente" />
        <input className="border border-field-line px-3 py-3 text-sm" name="location" placeholder="Ubicación" />
        <input
          className="border border-field-line px-3 py-3 text-sm"
          defaultValue={16}
          min={0}
          name="total_elevators"
          placeholder="Elevadores"
          type="number"
        />
        <input
          className="border border-field-line px-3 py-3 text-sm"
          defaultValue={62}
          min={1}
          name="default_floor_count"
          placeholder="Pisos"
          type="number"
        />
        <button className="bg-field-info px-4 py-3 text-sm font-semibold text-white hover:bg-field-ink md:col-span-4" disabled={isSaving}>
          {isSaving ? "Creando..." : "Crear proyecto"}
        </button>
      </form>

      {error ? <p className="mt-4 border border-field-fail bg-white p-3 text-sm text-field-fail">{error}</p> : null}
      {isLoading ? <p className="mt-6 text-sm text-field-muted">Cargando proyectos...</p> : null}

      {!isLoading && projects.length === 0 ? (
        <div className="mt-6 border border-field-line bg-white p-6 text-sm text-field-muted shadow-panel">No hay proyectos registrados.</div>
      ) : null}

      <div className="mt-6 grid gap-4 md:grid-cols-2">
        {projects.map((project) => (
          <Link className="border border-field-line bg-white p-4 shadow-panel hover:border-field-info" href={`/projects/${project.id}`} key={project.id}>
            <div className="flex items-start justify-between gap-3">
              <div>
                <h3 className="text-lg font-semibold">{project.name}</h3>
                <p className="mt-1 text-sm text-field-muted">{project.client_name || "Cliente pendiente"}</p>
              </div>
              <span className="border border-field-line px-2 py-1 text-xs font-medium">{project.status}</span>
            </div>
            <div className="mt-4 grid grid-cols-3 gap-2 text-sm">
              <span>{project.total_elevators ?? 0} elevadores</span>
              <span>{project.default_floor_count} pisos</span>
              <span>{project.location || "Sin ubicación"}</span>
            </div>
          </Link>
        ))}
      </div>
    </AppShell>
  );
}
