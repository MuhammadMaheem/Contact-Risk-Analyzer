import type { RiskFindingOut } from "@/lib/types";
import { SEVERITY_STYLES } from "@/lib/utils/risk-colors";
import { formatPercent, titleCase } from "@/lib/utils/format";
import { Badge } from "@/components/ui/badge";

export function RiskFindingCard({ finding }: { finding: RiskFindingOut }) {
  const style = SEVERITY_STYLES[finding.severity];

  return (
    <div className={`flex gap-3 rounded-md border border-border bg-surface-raised paper-shadow`}>
      <div className={`w-1.5 shrink-0 rounded-l-md ${style.bar}`} />
      <div className="flex-1 py-3 pr-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${style.bg} ${style.text}`}>
              {style.label}
            </span>
            <Badge>{titleCase(finding.category)}</Badge>
          </div>
          <span className="text-xs text-ink-faint tabular-nums">
            Confidence: {formatPercent(finding.confidence)}
          </span>
        </div>

        <h4 className="mt-2 font-medium text-ink">{finding.title}</h4>
        <p className="mt-1 text-sm text-ink-muted">{finding.explanation}</p>

        {finding.supporting_clause_text && (
          <blockquote className="mt-2 border-l-2 border-border-strong pl-3 text-sm italic text-ink-faint">
            &ldquo;{finding.supporting_clause_text}&rdquo;
          </blockquote>
        )}

        {finding.suggested_action && (
          <p className="mt-2 text-sm text-accent">
            <span className="font-medium">Suggested action:</span> {finding.suggested_action}
          </p>
        )}
      </div>
    </div>
  );
}
