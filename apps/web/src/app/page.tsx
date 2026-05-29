"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";
import type { DashboardOverview } from "@/types/api";

export default function Home() {
  const [overview, setOverview] = useState<DashboardOverview | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadOverview() {
      setIsLoading(true);
      setError(null);
      try {
        setOverview(await api.getDashboardOverview());
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : "No se pudo cargar el dashboard");
      } finally {
        setIsLoading(false);
      }
    }

    void loadOverview();
  }, []);

  return (
    <AppShell>
      <div className="border-b border-field-line pb-5">
        <p className="text-sm font-medium text-field-muted">Pruebas de carga y nivelación fina</p>
        <h2 className="mt-2 max-w-3xl text-3xl font-semibold sm:text-4xl">Dashboard técnico</h2>
        <div className="mt-4 flex flex-wrap gap-2">
          <Link className="border border-field-line bg-white px-4 py-3 text-sm font-semibold hover:border-field-info" href="/projects">
            Ver proyectos
          </Link>
          <Link className="border border-field-line bg-white px-4 py-3 text-sm font-semibold hover:border-field-info" href="/elevators">
            Ver elevadores
          </Link>
          <Link className="border border-field-line bg-white px-4 py-3 text-sm font-semibold hover:border-field-info" href="/test-runs">
            Ver pruebas
          </Link>
        </div>
      </div>

      {isLoading ? <p className="mt-6 text-sm text-field-muted">Cargando dashboard...</p> : null}
      {error ? <p className="mt-6 border border-field-fail bg-white p-3 text-sm text-field-fail">{error}</p> : null}

      {overview ? (
        <>
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <KpiCard label="Proyectos" value={overview.projects_count} detail={`${overview.active_projects_count} activos`} />
            <KpiCard label="Elevadores" value={overview.elevators_count} detail="Registrados en proyectos" />
            <KpiCard label="Pruebas" value={overview.test_runs_count} detail={`${overview.in_progress_test_runs_count} en proceso`} />
            <KpiCard label="Completadas" value={overview.completed_test_runs_count} detail={`${overview.draft_test_runs_count} borradores`} />
          </div>

          <div className="mt-6 grid gap-4 lg:grid-cols-2">
            <section className="border border-field-line bg-white shadow-panel">
              <div className="border-b border-field-line p-4">
                <h3 className="font-semibold">Últimas pruebas</h3>
              </div>
              {overview.latest_test_runs.length === 0 ? (
                <p className="p-4 text-sm text-field-muted">Todavía no hay pruebas registradas.</p>
              ) : (
                <div className="divide-y divide-field-line">
                  {overview.latest_test_runs.map((testRun) => (
                    <Link className="block p-4 hover:bg-field-bg" href={`/test-runs/${testRun.id}`} key={testRun.id}>
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="font-semibold">{testRun.name}</p>
                          <p className="mt-1 text-sm text-field-muted">
                            {testRun.project_name} · {testRun.elevator_code} · {testRun.test_type}
                          </p>
                        </div>
                        <span className="border border-field-line px-2 py-1 text-xs font-medium">{testRun.status}</span>
                      </div>
                      <p className="mt-2 text-sm text-field-muted">{testRun.responsible_technician}</p>
                    </Link>
                  ))}
                </div>
              )}
            </section>

            <section className="border border-field-line bg-white shadow-panel">
              <div className="border-b border-field-line p-4">
                <h3 className="font-semibold">Proyectos recientes</h3>
              </div>
              {overview.latest_projects.length === 0 ? (
                <p className="p-4 text-sm text-field-muted">Todavía no hay proyectos registrados.</p>
              ) : (
                <div className="divide-y divide-field-line">
                  {overview.latest_projects.map((project) => (
                    <Link className="block p-4 hover:bg-field-bg" href={`/projects/${project.id}`} key={project.id}>
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="font-semibold">{project.name}</p>
                          <p className="mt-1 text-sm text-field-muted">{project.elevators_count} elevadores</p>
                        </div>
                        <span className="border border-field-line px-2 py-1 text-xs font-medium">{project.status}</span>
                      </div>
                    </Link>
                  ))}
                </div>
              )}
            </section>
          </div>
        </>
      ) : null}
    </AppShell>
  );
}

function KpiCard({ label, value, detail }: { label: string; value: number; detail: string }) {
  return (
    <div className="border border-field-line bg-white p-4 shadow-panel">
      <p className="text-sm text-field-muted">{label}</p>
      <p className="mt-2 text-3xl font-semibold">{value}</p>
      <p className="mt-1 text-sm text-field-muted">{detail}</p>
    </div>
  );
}
