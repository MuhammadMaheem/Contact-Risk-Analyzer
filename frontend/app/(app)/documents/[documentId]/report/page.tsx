"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, FileText, FileType2 } from "lucide-react";
import { documentsApi } from "@/lib/api/documents";
import { reportsApi } from "@/lib/api/reports";
import { PageHeader } from "@/components/layout/page-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert } from "@/components/ui/alert";

export default function ReportPage() {
  const params = useParams<{ documentId: string }>();
  const documentId = Number(params.documentId);
  const router = useRouter();

  const [generating, setGenerating] = useState<"pdf" | "docx" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  async function handleGenerate(format: "pdf" | "docx") {
    setGenerating(format);
    setError(null);
    setSuccess(null);
    try {
      const report = await reportsApi.generate(documentId, format);
      const document = await documentsApi.get(documentId);
      const baseName = document.original_filename.replace(/\.[^.]+$/, "");
      await reportsApi.download(report.id, `${baseName}_risk_report.${format}`);
      setSuccess(`${format.toUpperCase()} report downloaded successfully.`);
    } catch {
      setError("Report generation failed. Please try again.");
    } finally {
      setGenerating(null);
    }
  }

  return (
    <div>
      <button
        onClick={() => router.push(`/documents/${documentId}`)}
        className="mb-4 flex items-center gap-1.5 text-sm text-ink-faint hover:text-ink"
      >
        <ArrowLeft className="h-3.5 w-3.5" />
        Back to document
      </button>

      <PageHeader
        title="Generate Report"
        description="Export a full AI risk assessment report — executive summary, clause analysis, and recommendations."
      />

      {error && (
        <Alert variant="error" className="mb-4">
          {error}
        </Alert>
      )}
      {success && (
        <Alert variant="success" className="mb-4">
          {success}
        </Alert>
      )}

      <div className="grid max-w-2xl grid-cols-1 gap-4 sm:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-accent" />
              PDF Report
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="mb-4 text-sm text-ink-faint">
              A print-ready PDF with risk assessment, executive summary, clause analysis, and
              recommendations.
            </p>
            <Button
              className="w-full"
              onClick={() => handleGenerate("pdf")}
              isLoading={generating === "pdf"}
            >
              Generate PDF
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileType2 className="h-5 w-5 text-accent" />
              DOCX Report
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="mb-4 text-sm text-ink-faint">
              An editable Word document with the same sections, ready for internal review or
              redlining.
            </p>
            <Button
              className="w-full"
              variant="secondary"
              onClick={() => handleGenerate("docx")}
              isLoading={generating === "docx"}
            >
              Generate DOCX
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
