"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface MetricsChartProps {
  data: Array<{
    date: string;
    value: number | null;
  }>;
  label: string;
  color?: string;
}

export function MetricsChart({
  data,
  label,
  color = "var(--accent)",
}: MetricsChartProps) {
  const filtered = data.filter((d) => d.value != null);

  if (filtered.length === 0) {
    return (
      <div className="card-static">
        <h3 className="text-label mb-5">
          {label}
        </h3>
        <div
          className="h-48 flex items-center justify-center text-sm"
          style={{ color: "var(--text-light)" }}
        >
          No data yet
        </div>
      </div>
    );
  }

  return (
    <div className="card-static">
      <h3 className="text-label mb-5">
        {label}
      </h3>
      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={filtered}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 11, fill: "var(--text-light)" }}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              tick={{ fontSize: 11, fill: "var(--text-light)" }}
              tickLine={false}
              axisLine={false}
              width={40}
            />
            <Tooltip
              contentStyle={{
                background: "var(--bg-card)",
                border: "1px solid var(--border)",
                borderRadius: "12px",
                boxShadow: "0 8px 30px rgba(0,0,0,0.08)",
                fontSize: 12,
                fontFamily: "var(--font-sans)",
              }}
            />
            <Line
              type="monotone"
              dataKey="value"
              stroke={color}
              strokeWidth={2}
              dot={{ r: 3, fill: color, strokeWidth: 0 }}
              activeDot={{ r: 5, strokeWidth: 0 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
