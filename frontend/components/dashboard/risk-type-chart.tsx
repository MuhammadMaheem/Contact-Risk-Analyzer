"use client";

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { RiskTypeFrequency } from "@/lib/types";
import { titleCase } from "@/lib/utils/format";

export function RiskTypeChart({ data }: { data: RiskTypeFrequency[] }) {
  if (data.length === 0) {
    return (
      <div className="flex h-56 items-center justify-center text-sm text-ink-faint">
        No risk findings recorded yet.
      </div>
    );
  }

  const chartData = data.map((d) => ({ name: titleCase(d.category), count: d.count }));

  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={chartData} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e7e5e4" vertical={false} />
        <XAxis
          dataKey="name"
          tick={{ fontSize: 11, fill: "#78716c" }}
          angle={-15}
          textAnchor="end"
          height={50}
        />
        <YAxis tick={{ fontSize: 11, fill: "#78716c" }} allowDecimals={false} />
        <Tooltip
          contentStyle={{
            borderRadius: 8,
            border: "1px solid #e7e5e4",
            fontSize: 12,
          }}
        />
        <Bar dataKey="count" fill="#b45309" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
