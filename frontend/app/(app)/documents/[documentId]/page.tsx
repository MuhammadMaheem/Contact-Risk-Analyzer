"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Search as SearchIcon, FileDown, ArrowLeft } from "lucide-react";
import { documentsApi } from "@/lib/api/documents";
import { analysisApi } from "@/lib/api/analysis";
import type { AnalysisOut, DocumentOut, RiskFindingOut, RiskSeverity } from "@/lib/types";
import { PageHeader } from "@/components/layout/page-header";
import { DocumentStatusBadge } from "@/components/documents/document-status-badge";
import { RiskFindingCard } from "@/components/analysis/risk-finding-card";
import { ComplianceScoreGauge } from "@/components/analysis/compliance-score-gauge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { formatDate } from "@/lib/utils/format";

const SEVERITY_ORDER: RiskSeverity[] = ["critical", "high", "medium", "low"];

export default function DocumentDetailPage() {
  const params = useParams<{ documentId: string }>();
  const documentId = Number(params.documentId);
  const router = useRouter();

  const [document, setDocument] = useState<DocumentOut | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisOut | null>(null);
  const [findings, setFindings] = useState<RiskFindingOut[]>([]);
  const [severityFilter, setSeverityFilter] = useState<RiskSeverity | "all">("all");

  useEffect(() => {
    let cancelled = false;

    async function poll() {
      const doc = await documentsApi.get(documentId);
      if (cancelled) return;
      setDocument(doc);

      if (doc.status === "analyzed" || doc.status === "partial") {
        const [a, r] = await Promise.all([analysisApi.get(documentId), analysisApi.risks(documentId)]);
        if (cancelled) return;
        setAnalysis(a);
        setFindings(r);
      }

      if (doc.status !== "uploaded" && doc.status !== "processing") {
        clearInterval(intervalId);
      }
    }

    poll();
    const intervalId = setInterval(poll, 2500);
    return () => {
      cancelled = true;
      clearInterval(intervalId);
    };
  }, [documentId]);

  const filteredFindings = useMemo(
    () => (severityFilter === "all" ? findings : findings.filter((f) => f.severity === severityFilter)),
    [findings, severityFilter]
  );

  const sortedFindings = useMemo(
    () =>
      [...filteredFindings].sort(
        (a, b) => SEVERITY_ORDER.indexOf(a.severity) - SEVERITY_ORDER.indexOf(b.severity)
      ),
    [filteredFindings]
  );

  if (!document) {
    return (
      <div>
        <Skeleton className="mb-6 h-10 w-1/2" />
        <Skeleton className="h-64" />
      </div>
    );
  }

  const isProcessing = document.status === "uploaded" || document.status === "processing";
  const isFailed = document.status === "failed";

  return (
    <div>
      <button
        onClick={() => router.push("/documents")}
        className="mb-4 flex items-center gap-1.5 text-sm text-ink-faint hover:text-ink"
      >
        <ArrowLeft className="h-3.5 w-3.5" />
        Back to documents
      </button>

      <PageHeader
        title={document.original_filename}
        description={analysis?.contract_type ?? "Contract analysis"}
        actions={
          <>
            <DocumentStatusBadge status={document.status} />
            {analysis && (
              <>
                <Link
                  href={`/documents/${documentId}/search`}
                  className="inline-flex items-center gap-2 rounded-md border border-border-strong bg-surface-raised px-4 py-2 text-sm font-medium text-ink hover:bg-surface-sunken"
                >
                  <SearchIcon className="h-4 w-4" />
                  Semantic Search
                </Link>
                <Link
                  href={`/documents/${documentId}/report`}
                  className="inline-flex items-center gap-2 rounded-md bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-accent-hover"
                >
                  <FileDown className="h-4 w-4" />
                  Generate Report
                </Link>
              </>
            )}
          </>
        }
      />

      {isProcessing && (
        <Alert variant="info" className="mb-6">
          AI analysis is in progress — extracting clauses, detecting risks, and generating a summary.
          This page updates automatically.
        </Alert>
      )}

      {isFailed && (
        <Alert variant="error" className="mb-6">
          Analysis failed: {document.status_detail ?? "Unknown error."}
        </Alert>
      )}

      {document.status === "partial" && (
        <Alert variant="warning" className="mb-6">
          Analysis completed with some degraded steps: {document.status_detail ?? "check audit logs for detail."}
        </Alert>
      )}

      {document.used_ocr && (
        <Alert variant="warning" className="mb-6">
          This document&apos;s text was extracted via OCR (scanned document). Please verify extracted clauses
          manually, as OCR accuracy can vary.
        </Alert>
      )}

      {analysis && (
        <Tabs defaultValue="overview">
          <TabsList>
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="risks">Risk Findings ({findings.length})</TabsTrigger>
            <TabsTrigger value="summary">Summary</TabsTrigger>
            <TabsTrigger value="compliance">Compliance</TabsTrigger>
          </TabsList>

          <TabsContent value="overview">
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle>Parties Involved</CardTitle>
                </CardHeader>
                <CardContent>
                  {analysis.parties.length === 0 ? (
                    <p className="text-sm text-ink-faint">No parties identified.</p>
                  ) : (
                    <ul className="space-y-2">
                      {analysis.parties.map((party, i) => (
                        <li key={i} className="flex items-center justify-between text-sm">
                          <span className="font-medium text-ink">{party.name}</span>
                          <span className="text-ink-faint">{party.role ?? "—"}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Key Dates</CardTitle>
                </CardHeader>
                <CardContent>
                  <dl className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <dt className="text-ink-faint">Effective Date</dt>
                      <dd className="font-medium text-ink">{analysis.effective_date ?? "—"}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-ink-faint">Expiry Date</dt>
                      <dd className="font-medium text-ink">{analysis.expiry_date ?? "—"}</dd>
                    </div>
                  </dl>
                </CardContent>
              </Card>

              <Card className="lg:col-span-2">
                <CardHeader>
                  <CardTitle>Clause Analysis</CardTitle>
                </CardHeader>
                <CardContent>
                  <dl className="space-y-4 text-sm">
                    {[
                      ["Payment Terms", analysis.payment_terms],
                      ["Renewal Clause", analysis.renewal_clause],
                      ["Confidentiality Clause", analysis.confidentiality_clause],
                      ["Termination Clause", analysis.termination_clause],
                    ].map(([label, value]) => (
                      <div key={label}>
                        <dt className="font-medium text-ink-muted">{label}</dt>
                        <dd className="mt-0.5 text-ink">{value || "Not found in document"}</dd>
                      </div>
                    ))}
                  </dl>
                </CardContent>
              </Card>

              <Card className="lg:col-span-2">
                <CardHeader>
                  <CardTitle>Responsibilities</CardTitle>
                </CardHeader>
                <CardContent>
                  {analysis.responsibilities.length === 0 ? (
                    <p className="text-sm text-ink-faint">No specific responsibilities extracted.</p>
                  ) : (
                    <ul className="space-y-2 text-sm">
                      {analysis.responsibilities.map((r, i) => (
                        <li key={i}>
                          <span className="font-medium text-ink">{r.party}:</span>{" "}
                          <span className="text-ink-muted">{r.obligation}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="risks">
            <div className="mb-4 flex flex-wrap gap-2">
              {(["all", ...SEVERITY_ORDER] as const).map((s) => (
                <button
                  key={s}
                  onClick={() => setSeverityFilter(s)}
                  className={`rounded-full border px-3 py-1 text-xs font-medium capitalize transition-colors ${
                    severityFilter === s
                      ? "border-accent bg-accent-tint text-accent"
                      : "border-border-strong text-ink-muted hover:bg-surface-sunken"
                  }`}
                >
                  {s}
                </button>
              ))}
            </div>
            {sortedFindings.length === 0 ? (
              <p className="py-8 text-center text-sm text-ink-faint">No findings match this filter.</p>
            ) : (
              <div className="space-y-3">
                {sortedFindings.map((finding) => (
                  <RiskFindingCard key={finding.id} finding={finding} />
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="summary">
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
              <Card className="lg:col-span-2">
                <CardHeader>
                  <CardTitle>Executive Summary</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm leading-relaxed text-ink-muted">
                    {analysis.executive_summary ?? "Summary unavailable — try reprocessing this document."}
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Key Obligations</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="list-disc space-y-1.5 pl-4 text-sm text-ink-muted">
                    {analysis.key_obligations.map((o, i) => (
                      <li key={i}>{o}</li>
                    ))}
                  </ul>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Important Dates</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-1.5 text-sm">
                    {analysis.important_dates.map((d, i) => (
                      <li key={i} className="flex justify-between">
                        <span className="text-ink-faint">{d.label}</span>
                        <span className="font-medium text-ink">{d.date}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Important Clauses</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="list-disc space-y-1.5 pl-4 text-sm text-ink-muted">
                    {analysis.important_clauses.map((c, i) => (
                      <li key={i}>{c}</li>
                    ))}
                  </ul>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Recommended Actions</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="list-disc space-y-1.5 pl-4 text-sm text-ink-muted">
                    {analysis.recommended_actions.map((a, i) => (
                      <li key={i}>{a}</li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="compliance">
            <Card className="max-w-md">
              <CardHeader>
                <CardTitle>Compliance Score</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-col items-center">
                <ComplianceScoreGauge score={analysis.compliance_score} grade={analysis.compliance_grade} />
                <p className="mt-4 text-center text-sm text-ink-faint">
                  Derived from {findings.length} risk finding{findings.length === 1 ? "" : "s"}, weighted by
                  severity and AI confidence. Analyzed {formatDate(analysis.created_at)} using{" "}
                  {analysis.model_used ?? "Groq LLM"}.
                </p>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}
    </div>
  );
}
