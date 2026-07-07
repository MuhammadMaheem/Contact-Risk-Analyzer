"use client";

import Link from "next/link";
import { FileText, RefreshCw, Trash2 } from "lucide-react";
import type { DocumentListItem } from "@/lib/types";
import { DocumentStatusBadge } from "@/components/documents/document-status-badge";
import { formatDate } from "@/lib/utils/format";
import { gradeColor } from "@/lib/utils/risk-colors";
import { Button } from "@/components/ui/button";

export function DocumentsTable({
  documents,
  onDelete,
  onReprocess,
}: {
  documents: DocumentListItem[];
  onDelete?: (documentId: number) => void;
  onReprocess?: (documentId: number) => void;
}) {
  if (documents.length === 0) {
    return (
      <div className="flex flex-col items-center gap-2 py-12 text-center text-ink-faint">
        <FileText className="h-8 w-8" />
        <p className="text-sm">No documents yet.</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-ink-faint">
            <th className="py-2 pr-4 font-medium">Document</th>
            <th className="py-2 pr-4 font-medium">Contract Type</th>
            <th className="py-2 pr-4 font-medium">Status</th>
            <th className="py-2 pr-4 font-medium">Grade</th>
            <th className="py-2 pr-4 font-medium">High Risk</th>
            <th className="py-2 pr-4 font-medium">Uploaded</th>
            {(onDelete || onReprocess) && <th className="py-2 pr-0 font-medium text-right">Actions</th>}
          </tr>
        </thead>
        <tbody>
          {documents.map((doc) => (
            <tr key={doc.id} className="border-b border-border/60 last:border-0 hover:bg-surface-sunken/50">
              <td className="py-3 pr-4">
                <Link
                  href={`/documents/${doc.id}`}
                  className="font-medium text-ink hover:text-accent"
                >
                  {doc.original_filename}
                </Link>
                <div className="text-xs uppercase text-ink-faint">{doc.file_type}</div>
              </td>
              <td className="py-3 pr-4 text-ink-muted">{doc.contract_type ?? "—"}</td>
              <td className="py-3 pr-4">
                <DocumentStatusBadge status={doc.status} />
              </td>
              <td className={`py-3 pr-4 font-display font-semibold ${gradeColor(doc.compliance_grade)}`}>
                {doc.compliance_grade ?? "—"}
              </td>
              <td className="py-3 pr-4 tabular-nums text-ink-muted">
                {doc.high_risk_count > 0 ? doc.high_risk_count : "—"}
              </td>
              <td className="py-3 pr-4 tabular-nums text-ink-faint">{formatDate(doc.created_at)}</td>
              {(onDelete || onReprocess) && (
                <td className="py-3 pr-0 text-right">
                  <div className="flex justify-end gap-1">
                    {onReprocess && (
                      <Button variant="ghost" size="sm" onClick={() => onReprocess(doc.id)} title="Reprocess">
                        <RefreshCw className="h-3.5 w-3.5" />
                      </Button>
                    )}
                    {onDelete && (
                      <Button variant="ghost" size="sm" onClick={() => onDelete(doc.id)} title="Delete">
                        <Trash2 className="h-3.5 w-3.5 text-danger" />
                      </Button>
                    )}
                  </div>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
