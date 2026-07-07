import { HTMLAttributes } from "react";
import { AlertTriangle, Info, CheckCircle2 } from "lucide-react";
import { cn } from "@/lib/utils/cn";

type AlertVariant = "info" | "warning" | "error" | "success";

const VARIANT_STYLES: Record<AlertVariant, { wrap: string; icon: typeof Info }> = {
  info: { wrap: "border-border-strong bg-surface-sunken text-ink-muted", icon: Info },
  warning: { wrap: "border-severity-medium/30 bg-severity-medium/10 text-severity-medium", icon: AlertTriangle },
  error: { wrap: "border-danger/30 bg-danger/10 text-danger", icon: AlertTriangle },
  success: { wrap: "border-success/30 bg-success/10 text-success", icon: CheckCircle2 },
};

interface AlertProps extends HTMLAttributes<HTMLDivElement> {
  variant?: AlertVariant;
}

export function Alert({ className, variant = "info", children, ...props }: AlertProps) {
  const { wrap, icon: Icon } = VARIANT_STYLES[variant];
  return (
    <div
      className={cn("flex items-start gap-2.5 rounded-md border px-4 py-3 text-sm", wrap, className)}
      {...props}
    >
      <Icon className="mt-0.5 h-4 w-4 shrink-0" />
      <div>{children}</div>
    </div>
  );
}
