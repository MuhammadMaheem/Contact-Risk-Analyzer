"use client";

import { RadialBar, RadialBarChart, PolarAngleAxis } from "recharts";
import { gradeColor } from "@/lib/utils/risk-colors";

const GRADE_HEX: Record<string, string> = {
  A: "#15803d",
  B: "#4d7c0f",
  C: "#a16207",
  D: "#c2410c",
  F: "#b91c1c",
};

export function ComplianceScoreGauge({
  score,
  grade,
}: {
  score: number | null;
  grade: string | null;
}) {
  const value = score ?? 0;
  const color = grade ? GRADE_HEX[grade] ?? "#78716c" : "#78716c";

  return (
    <div className="flex flex-col items-center">
      <RadialBarChart
        width={200}
        height={140}
        cx={100}
        cy={120}
        innerRadius={70}
        outerRadius={100}
        startAngle={180}
        endAngle={0}
        data={[{ value, fill: color }]}
      >
        <PolarAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
        <RadialBar background dataKey="value" cornerRadius={8} />
      </RadialBarChart>
      <div className="-mt-16 flex flex-col items-center">
        <span className="font-display text-3xl font-bold tabular-nums text-ink">
          {score !== null ? score.toFixed(0) : "—"}
        </span>
        <span className={`font-display text-lg font-semibold ${gradeColor(grade)}`}>
          Grade {grade ?? "—"}
        </span>
      </div>
    </div>
  );
}
