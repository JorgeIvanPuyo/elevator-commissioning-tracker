"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";

import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";
import type { TestRunListItem, TestRunStatus, TestType } from "@/types/api";

const statusLabels: Record<TestRunStatus, string> = {
  draft: "Borrador",
  in_progress: "En proceso",
  completed: "Completada",
  cancelled: "Cancelada",
};

export default function TestRunsPage() {
  const [testRuns, setTestRuns] = useState<TestRunListItem[]>([]);
  const [testTypes, setTestTypes] = useState<TestType[]>([]);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [testTypeCode, setTestTypeCode] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadTestRuns() {
    setIsLoading(true);
    setError(null);
    try {
      const [runResponse, typeResponse] = await Promise.all([
        api.listTestRuns({ search: search || undefined, status: status || undefined, test_type_code: testTypeCode || undefined }),
        api.listTestTypes(),
      ]);
      setTestRuns(runResponse);
      setTestTypes(typeResponse);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "No se pudieron cargar pruebas");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadTestRuns();
  }, []);

  function handleFilter(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void loadTestRuns();
  }

  return (
    <AppShell>
      <div className="border-b border-field-line pb-5">
        <p className="text-sm font-medium text-field-muted">Listado global</p>
        <h2 className="mt-2 text-3xl font-semibold">Pruebas</h2>
      </div>

      <form className="mt-6 grid gap-3 border border-field-line bg-white p-4 shadow-panel md:grid-cols-[1fr_180px_220px_auto]" onSubmit={handleFilter}>
        <input
          className="border border-field-line px-3 py-3 text-sm"
          onChange={(event) => setSearch(event.currentTarget.value)}
          placeholder="Buscar por prueba, técnico, elevador o proyecto"
          value={search}
        />
        <select className="border border-field-line px-3 py-3 text-sm" onChange={(event) => setStatus(event.currentTarget.value)} value={status}>
          <option value="">Todos los estados</option>
          <option value="draft">Borrador</option>
          <option value="in_progress">En proceso</option>
          <option value="completed">Completada</option>
          <option value="cancelled">Cancelada</option>
        </select>
        <select className="border border-field-line px-3 py-3 text-sm" onChange={(event) => setTestTypeCode(event.currentTarget.value)} value={testTypeCode}>
          <option value="">Todos los tipos</option>
          {testTypes.map((testType) => (
            <option key={testType.id} value={testType.code}>
              {testType.name}
            </option>
          ))}
        </select>
        <button className="bg-field-info px-4 py-3 text-sm font-semibold text-white hover:bg-field-ink">Filtrar</button>
      </form>

      {error ? <p className="mt-4 border border-field-fail bg-white p-3 text-sm text-field-fail">{error}</p> : null}
      {isLoading ? <p className="mt-6 text-sm text-field-muted">Cargando pruebas...</p> : null}
      {!isLoading && testRuns.length === 0 ? (
        <div className="mt-6 border border-field-line bg-white p-6 text-sm text-field-muted shadow-panel">No hay pruebas registradas con esos filtros.</div>
      ) : null}

      <div className="mt-6 grid gap-4">
        {testRuns.map((testRun) => (
          <Link className="border border-field-line bg-white p-4 shadow-panel hover:border-field-info" href={`/test-runs/${testRun.id}`} key={testRun.id}>
            <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
              <div>
                <h3 className="text-lg font-semibold">{testRun.name}</h3>
                <p className="mt-1 text-sm text-field-muted">
                  {testRun.project_name} · {testRun.elevator_code} · {testRun.test_type_name}
                </p>
              </div>
              <span className="w-fit border border-field-line px-2 py-1 text-xs font-medium">{statusLabels[testRun.status]}</span>
            </div>
            <p className="mt-3 text-sm text-field-muted">Responsable: {testRun.responsible_technician}</p>
          </Link>
        ))}
      </div>
    </AppShell>
  );
}
