"use client";

import { useEffect, useState } from "react";
import { FileStack, Gauge, ShieldAlert } from "lucide-react";
import { dashboardApi } from "@/lib/api/dashboard";
import type { DashboardStats } from "@/lib/types";
import { PageHeader } from "@/components/layout/page-header";
import { StatCard } from "@/components/dashboard/stat-card";
import { RiskTypeChart } from "@/components/dashboard/risk-type-chart";
import { DocumentsTable } from "@/components/documents/documents-table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    dashboardApi
      .stats()
      .then(setStats)
      .finally(() => setIsLoading(false));
  }, []);

  return (
    <div>
      <PageHeader
        title="AI Insights Dashboard"
        description="An overview of your contract analysis activity and risk exposure."
      />

      {isLoading || !stats ? (
        <div className="grid grid-cols-3 gap-4">
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <StatCard label="Total Documents" value={String(stats.total_documents)} icon={FileStack} />
            <StatCard
              label="Average Compliance Score"
              value={stats.average_risk_score !== null ? stats.average_risk_score.toFixed(1) : "—"}
              icon={Gauge}
            />
            <StatCard
              label="High-Risk Documents"
              value={String(stats.high_risk_documents)}
              icon={ShieldAlert}
            />
          </div>

          <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-5">
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Frequently Detected Risks</CardTitle>
              </CardHeader>
              <CardContent>
                <RiskTypeChart data={stats.frequent_risk_types} />
              </CardContent>
            </Card>

            <Card className="lg:col-span-3">
              <CardHeader>
                <CardTitle>Processing History</CardTitle>
              </CardHeader>
              <CardContent>
                <DocumentsTable documents={stats.processing_history} />
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
