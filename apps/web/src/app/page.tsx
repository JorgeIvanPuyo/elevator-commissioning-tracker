import Link from "next/link";

import { AppShell } from "@/components/AppShell";

const focusElevators = ["#9", "#10", "#11", "#12", "#13"];

export default function Home() {
  return (
    <AppShell>
          <div className="border-b border-field-line pb-5">
            <p className="text-sm font-medium text-field-muted">Pruebas de carga y nivelación fina</p>
            <h2 className="mt-2 max-w-3xl text-3xl font-semibold sm:text-4xl">
              Trazabilidad técnica para elevadores en campo
            </h2>
            <Link
              className="mt-4 inline-flex bg-field-info px-4 py-3 text-sm font-semibold text-white hover:bg-field-ink"
              href="/projects"
            >
              Abrir proyectos
            </Link>
          </div>

          <div className="mt-6 grid gap-4 md:grid-cols-3">
            <div className="border border-field-line bg-white p-4 shadow-panel">
              <p className="text-sm text-field-muted">Elevadores iniciales</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {focusElevators.map((elevator) => (
                  <span className="border border-field-line bg-field-bg px-3 py-2 text-sm font-semibold" key={elevator}>
                    {elevator}
                  </span>
                ))}
              </div>
            </div>
            <div className="border border-field-line bg-white p-4 shadow-panel">
              <p className="text-sm text-field-muted">Alcance del proyecto</p>
              <p className="mt-2 text-2xl font-semibold">16 elevadores</p>
              <p className="mt-1 text-sm text-field-muted">62 pisos por torre operativa.</p>
            </div>
            <div className="border border-field-line bg-white p-4 shadow-panel">
              <p className="text-sm text-field-muted">Estado del backend</p>
              <p className="mt-2 text-2xl font-semibold text-field-ok">Healthcheck listo</p>
              <p className="mt-1 text-sm text-field-muted">API base preparada para el siguiente slice.</p>
            </div>
          </div>

          <div className="mt-6 border border-field-line bg-white p-4 shadow-panel">
            <div className="grid gap-4 md:grid-cols-4">
              {["Carga", "Nivelación", "Parámetros HEX", "Evidencias"].map((label) => (
                <div className="border-l-4 border-field-info bg-field-bg p-4" key={label}>
                  <p className="text-sm font-semibold">{label}</p>
                  <p className="mt-2 text-sm text-field-muted">Pendiente de implementación operativa.</p>
                </div>
              ))}
            </div>
          </div>
    </AppShell>
  );
}
