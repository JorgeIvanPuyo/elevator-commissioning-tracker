import Link from "next/link";

import { AppShell } from "@/components/AppShell";
import { technicalDocuments } from "@/content/docs/registry";

export default function DocsPage() {
  return (
    <AppShell>
      <div className="border-b border-field-line pb-5">
        <p className="text-sm font-medium text-field-muted">Procedimientos Markdown</p>
        <h2 className="mt-2 text-3xl font-semibold">Documentación técnica</h2>
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-2">
        {technicalDocuments.map((document) => (
          <Link className="border border-field-line bg-white p-4 shadow-panel hover:border-field-info" href={`/docs/${document.slug}`} key={document.slug}>
            <p className="text-sm font-medium text-field-muted">{document.category}</p>
            <h3 className="mt-2 text-lg font-semibold">{document.title}</h3>
            <p className="mt-2 text-sm text-field-muted">{document.description}</p>
            <span className="mt-4 inline-flex border border-field-line px-2 py-1 text-xs font-medium">{document.relatedTestTypeCode}</span>
          </Link>
        ))}
      </div>
    </AppShell>
  );
}
