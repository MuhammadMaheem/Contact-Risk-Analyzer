import type { AuditLogOut } from "@/lib/types";
import { formatDateTime } from "@/lib/utils/format";
import { cn } from "@/lib/utils/cn";

const LEVEL_STYLES = {
  info: "text-ink-faint",
  warning: "text-severity-medium",
  error: "text-danger",
};

export function AuditLogTable({ logs }: { logs: AuditLogOut[] }) {
  if (logs.length === 0) {
    return <p className="py-6 text-center text-sm text-ink-faint">No log entries yet.</p>;
  }

  return (
    <div className="max-h-96 overflow-y-auto">
      <table className="w-full text-sm">
        <thead className="sticky top-0 bg-surface-raised">
          <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-ink-faint">
            <th className="py-2 pr-4 font-medium">Time</th>
            <th className="py-2 pr-4 font-medium">Action</th>
            <th className="py-2 pr-4 font-medium">Resource</th>
            <th className="py-2 pr-0 font-medium">Level</th>
          </tr>
        </thead>
        <tbody>
          {logs.map((log) => (
            <tr key={log.id} className="border-b border-border/60 last:border-0">
              <td className="py-2 pr-4 text-xs tabular-nums text-ink-faint">
                {formatDateTime(log.created_at)}
              </td>
              <td className="py-2 pr-4 font-mono text-xs text-ink">{log.action}</td>
              <td className="py-2 pr-4 text-xs text-ink-muted">
                {log.resource_type ? `${log.resource_type}#${log.resource_id}` : "—"}
              </td>
              <td className={cn("py-2 pr-0 text-xs font-medium uppercase", LEVEL_STYLES[log.level])}>
                {log.level}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
