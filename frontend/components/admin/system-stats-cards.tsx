import { Users, FileStack, Brain, Clock } from "lucide-react";
import type { SystemStatsOut } from "@/lib/types";
import { StatCard } from "@/components/dashboard/stat-card";

export function SystemStatsCards({ stats }: { stats: SystemStatsOut }) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <StatCard label="Total Users" value={String(stats.total_users)} icon={Users} />
      <StatCard label="Total Documents" value={String(stats.total_documents)} icon={FileStack} />
      <StatCard label="Total Groq Calls" value={String(stats.total_groq_calls)} icon={Brain} />
      <StatCard
        label="Avg. Processing Time"
        value={
          stats.average_processing_time_seconds !== null
            ? `${stats.average_processing_time_seconds.toFixed(1)}s`
            : "—"
        }
        icon={Clock}
      />
    </div>
  );
}
