import type { RiskSeverity } from "@/lib/types";

export const SEVERITY_STYLES: Record<
  RiskSeverity,
  { bar: string; text: string; bg: string; label: string }
> = {
  critical: {
    bar: "bg-severity-critical",
    text: "text-severity-critical",
    bg: "bg-severity-critical/10",
    label: "Critical",
  },
  high: {
    bar: "bg-severity-high",
    text: "text-severity-high",
    bg: "bg-severity-high/10",
    label: "High",
  },
  medium: {
    bar: "bg-severity-medium",
    text: "text-severity-medium",
    bg: "bg-severity-medium/10",
    label: "Medium",
  },
  low: {
    bar: "bg-severity-low",
    text: "text-severity-low",
    bg: "bg-severity-low/10",
    label: "Low",
  },
};

export function gradeColor(grade: string | null | undefined): string {
  switch (grade) {
    case "A":
      return "text-success";
    case "B":
      return "text-severity-low";
    case "C":
      return "text-severity-medium";
    case "D":
      return "text-severity-high";
    case "F":
      return "text-severity-critical";
    default:
      return "text-ink-faint";
  }
}
