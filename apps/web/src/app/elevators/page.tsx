"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";

import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";
import type { ElevatorListItem } from "@/types/api";

export default function ElevatorsPage() {
  const [elevators, setElevators] = useState<ElevatorListItem[]>([]);
  const [search, setSearch] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadElevators(nextSearch = search) {
    setIsLoading(true);
    setError(null);
    try {
      setElevators(await api.listElevators({ search: nextSearch || undefined }));
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "No se pudieron cargar elevadores");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadElevators("");
  }, []);

  function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void loadElevators(search);
  }

  return (
    <AppShell>
      <div className="border-b border-field-line pb-5">
        <p className="text-sm font-medium text-field-muted">Listado global</p>
        <h2 className="mt-2 text-3xl font-semibold">Elevadores</h2>
      </div>

      <form className="mt-6 grid gap-3 border border-field-line bg-white p-4 shadow-panel md:grid-cols-[1fr_auto]" onSubmit={handleSearch}>
        <input
          className="border border-field-line px-3 py-3 text-sm"
          onChange={(event) => setSearch(event.currentTarget.value)}
          placeholder="Buscar por código, nombre o proyecto"
          value={search}
        />
        <button className="bg-field-info px-4 py-3 text-sm font-semibold text-white hover:bg-field-ink">Buscar</button>
      </form>

      {error ? <p className="mt-4 border border-field-fail bg-white p-3 text-sm text-field-fail">{error}</p> : null}
      {isLoading ? <p className="mt-6 text-sm text-field-muted">Cargando elevadores...</p> : null}
      {!isLoading && elevators.length === 0 ? (
        <div className="mt-6 border border-field-line bg-white p-6 text-sm text-field-muted shadow-panel">No hay elevadores registrados.</div>
      ) : null}

      <div className="mt-6 grid gap-4 md:grid-cols-2">
        {elevators.map((elevator) => (
          <Link className="border border-field-line bg-white p-4 shadow-panel hover:border-field-info" href={`/elevators/${elevator.id}`} key={elevator.id}>
            <div className="flex items-start justify-between gap-3">
              <div>
                <h3 className="text-lg font-semibold">{elevator.name || elevator.code}</h3>
                <p className="mt-1 text-sm text-field-muted">{elevator.project_name}</p>
              </div>
              <span className="border border-field-line px-2 py-1 text-xs font-medium">{elevator.status}</span>
            </div>
            <div className="mt-4 flex flex-wrap gap-2 text-sm text-field-muted">
              <span>{elevator.code}</span>
              <span>{elevator.floor_count} pisos</span>
            </div>
          </Link>
        ))}
      </div>
    </AppShell>
  );
}
