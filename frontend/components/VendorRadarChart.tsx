"use client";

import { Paper, Text, Group } from "@mantine/core";
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis,
  PolarRadiusAxis, Legend, ResponsiveContainer, Tooltip,
} from "recharts";
import type { ProposalResult, ScoreCard } from "@/lib/types";

const DIMENSIONS: { key: keyof Omit<ScoreCard, "overall">; label: string }[] = [
  { key: "platform_functionality",  label: "Functionality" },
  { key: "security_and_compliance", label: "Security" },
  { key: "integration_capability",  label: "Integrations" },
  { key: "enterprise_readiness",    label: "Enterprise" },
  { key: "innovation_roadmap",      label: "Innovation" },
  { key: "support_and_training",    label: "Support" },
  { key: "pricing_transparency",    label: "Pricing" },
  { key: "accessibility_compliance",label: "Accessibility" },
  { key: "risk_level",              label: "Risk Level" },
];

// Hardcoded hex so SVG fill/stroke works without CSS variable resolution
const VENDOR_COLORS = ["#179281", "#3187f6", "#d0394e"];

interface Props {
  proposals: ProposalResult[];
}

export function VendorRadarChart({ proposals }: Props) {
  const scored = proposals.filter((p) => p.scores != null);
  if (scored.length === 0) return null;

  const data = DIMENSIONS.map(({ key, label }) => {
    const entry: Record<string, string | number> = { dimension: label };
    scored.forEach((p) => {
      entry[p.vendor_name ?? p.filename] = p.scores![key]?.score ?? 0;
    });
    return entry;
  });

  return (
    <Paper p="lg" radius="md" withBorder bg="white" className="fadeIn">
      <Group mb="md" gap="xs">
        <Text fw={700} size="lg" c="dark">Vendor Comparison</Text>
        <Text size="sm" c="dimmed">— scores by dimension (0–10)</Text>
      </Group>
      <ResponsiveContainer width="100%" height={400}>
        <RadarChart data={data} cx="50%" cy="50%" outerRadius="72%">
          <PolarGrid stroke="#dee2e6" />
          <PolarAngleAxis
            dataKey="dimension"
            tick={{ fontSize: 12, fill: "#495057" }}
          />
          <PolarRadiusAxis
            angle={90}
            domain={[0, 10]}
            tickCount={6}
            tick={{ fontSize: 10, fill: "#adb5bd" }}
          />
          {scored.map((p, i) => (
            <Radar
              key={p.filename}
              name={p.vendor_name ?? p.filename}
              dataKey={p.vendor_name ?? p.filename}
              stroke={VENDOR_COLORS[i % VENDOR_COLORS.length]}
              fill={VENDOR_COLORS[i % VENDOR_COLORS.length]}
              fillOpacity={0.12}
              strokeWidth={2.5}
            />
          ))}
          <Legend wrapperStyle={{ fontSize: 13, paddingTop: 16 }} />
          <Tooltip
            formatter={(value) => [Number(value).toFixed(1), ""]}
            contentStyle={{ borderRadius: 8, fontSize: 12, border: "1px solid #dee2e6" }}
          />
        </RadarChart>
      </ResponsiveContainer>
    </Paper>
  );
}
