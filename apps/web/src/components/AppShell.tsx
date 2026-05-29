import Link from "next/link";
import type { ReactNode } from "react";

const navigationItems = [
  { label: "Dashboard", href: "/" },
  { label: "Proyectos", href: "/projects" },
  { label: "Elevadores", href: "/elevators" },
  { label: "Pruebas", href: "/test-runs" },
  { label: "Documentación", href: "/docs" },
];

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <main className="min-h-screen bg-field-bg text-field-ink">
      <div className="mx-auto flex min-h-screen w-full max-w-7xl flex-col px-4 py-4 sm:px-6 lg:flex-row lg:gap-6 lg:py-6">
        <aside className="border-field-line bg-white shadow-panel lg:sticky lg:top-6 lg:h-[calc(100vh-3rem)] lg:w-64 lg:border lg:p-4">
          <div className="flex items-center justify-between border-b border-field-line pb-4 lg:block lg:border-b-0 lg:pb-0">
            <Link href="/">
              <p className="text-xs font-semibold uppercase tracking-wide text-field-muted">Proyecto 62 pisos</p>
              <h1 className="mt-1 text-xl font-semibold">Megapolis Traceability</h1>
            </Link>
            <span className="rounded border border-field-line px-2 py-1 text-xs font-medium text-field-muted lg:mt-4 lg:inline-block">
              MVP
            </span>
          </div>

          <nav className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-5 lg:grid-cols-1">
            {navigationItems.map((item) => (
              <Link
                className="border-field-line bg-field-bg px-3 py-3 text-sm font-medium hover:border-field-info hover:text-field-info lg:border"
                href={item.href}
                key={item.label}
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </aside>

        <section className="flex-1 py-6 lg:py-0">{children}</section>
      </div>
    </main>
  );
}
