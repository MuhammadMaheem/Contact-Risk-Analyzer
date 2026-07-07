"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Upload } from "lucide-react";
import { documentsApi } from "@/lib/api/documents";
import type { DocumentListItem } from "@/lib/types";
import { PageHeader } from "@/components/layout/page-header";
import { DocumentsTable } from "@/components/documents/documents-table";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentListItem[] | null>(null);

  function reload() {
    documentsApi.list().then(setDocuments);
  }

  useEffect(() => {
    reload();
    const interval = setInterval(reload, 4000);
    return () => clearInterval(interval);
  }, []);

  async function handleDelete(documentId: number) {
    if (!confirm("Delete this document and its analysis? This cannot be undone.")) return;
    await documentsApi.remove(documentId);
    reload();
  }

  async function handleReprocess(documentId: number) {
    await documentsApi.reprocess(documentId);
    reload();
  }

  return (
    <div>
      <PageHeader
        title="Documents"
        description="Every contract you've uploaded, its processing status, and its risk grade."
        actions={
          <Link
            href="/documents/upload"
            className="inline-flex items-center gap-2 rounded-md bg-accent px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-accent-hover"
          >
            <Upload className="h-4 w-4" />
            Upload Document
          </Link>
        }
      />

      <Card>
        <CardContent>
          {documents === null ? (
            <Skeleton className="h-40" />
          ) : (
            <DocumentsTable documents={documents} onDelete={handleDelete} onReprocess={handleReprocess} />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
