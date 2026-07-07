import { CheckCircle2, Clock, AlertTriangle, XCircle, Loader2 } from "lucide-react";
import type { DocumentStatus } from "@/lib/types";
import { cn } from "@/lib/utils/cn";

const STATUS_CONFIG: Record<
  DocumentStatus,
  { label: string; icon: typeof Clock; className: string }
> = {
  uploaded: { label: "Queued", icon: Clock, className: "text-ink-faint bg-surface-sunken" },
  processing: { label: "Processing", icon: Loader2, className: "text-accent bg-accent-tint" },
  analyzed: { label: "Analyzed", icon: CheckCircle2, className: "text-success bg-success/10" },
  partial: { label: "Partial", icon: AlertTriangle, className: "text-severity-medium bg-severity-medium/10" },
  failed: { label: "Failed", icon: XCircle, className: "text-danger bg-danger/10" },
};

export function DocumentStatusBadge({ status }: { status: DocumentStatus }) {
  const { label, icon: Icon, className } = STATUS_CONFIG[status];
  return (
    <span className={cn("inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium", className)}>
      <Icon className={cn("h-3 w-3", status === "processing" && "animate-spin")} />
      {label}
    </span>
  );
}
