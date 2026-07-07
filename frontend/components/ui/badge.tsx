import { HTMLAttributes } from "react";
import { cn } from "@/lib/utils/cn";

export function Badge({ className, ...props }: HTMLAttributes<HTMLSpanElement>) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border border-border-strong bg-surface-sunken px-2.5 py-0.5 text-xs font-medium text-ink-muted",
        className
      )}
      {...props}
    />
  );
}
