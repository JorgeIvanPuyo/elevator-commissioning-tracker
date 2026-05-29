import fs from "node:fs/promises";
import path from "node:path";

import Link from "next/link";
import { notFound } from "next/navigation";

import { AppShell } from "@/components/AppShell";
import { getTechnicalDocument, technicalDocuments } from "@/content/docs/registry";

export function generateStaticParams() {
  return technicalDocuments.map((document) => ({ slug: document.slug }));
}

export default async function DocumentPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const document = getTechnicalDocument(slug);
  if (!document) {
    notFound();
  }

  const markdownPath = path.join(process.cwd(), "src", "content", "docs", `${slug}.md`);
  const markdown = await fs.readFile(markdownPath, "utf8");

  return (
    <AppShell>
      <div className="border-b border-field-line pb-5">
        <Link className="text-sm font-medium text-field-info" href="/docs">
          Documentación
        </Link>
        <h2 className="mt-2 text-3xl font-semibold">{document.title}</h2>
        <p className="mt-2 text-sm text-field-muted">{document.description}</p>
      </div>

      <article className="mt-6 border border-field-line bg-white p-5 shadow-panel">
        <MarkdownView markdown={markdown} />
      </article>
    </AppShell>
  );
}

function MarkdownView({ markdown }: { markdown: string }) {
  return (
    <div className="grid gap-3 text-sm leading-6">
      {markdown.split("\n").map((line, index) => {
        if (line.startsWith("# ")) {
          return (
            <h1 className="text-2xl font-semibold" key={index}>
              {line.replace("# ", "")}
            </h1>
          );
        }
        if (line.startsWith("## ")) {
          return (
            <h2 className="mt-3 text-lg font-semibold" key={index}>
              {line.replace("## ", "")}
            </h2>
          );
        }
        if (line.startsWith("- ")) {
          return (
            <p className="pl-4 text-field-muted" key={index}>
              • {line.replace("- ", "")}
            </p>
          );
        }
        if (!line.trim()) {
          return <span key={index} />;
        }
        return (
          <p className="text-field-muted" key={index}>
            {line}
          </p>
        );
      })}
    </div>
  );
}
