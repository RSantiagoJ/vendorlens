"use client";

import type { CSSProperties } from "react";
import { Paper, Text, Group, Badge, Box, ScrollArea, Tooltip, Stack } from "@mantine/core";
import { IconAward } from "@tabler/icons-react";
import type { ProposalData, ProposalResult, RiskFlag, ScoreCard } from "@/lib/types";

const SCORE_DIMENSIONS: {
  key: keyof Omit<ScoreCard, "overall">;
  label: string;
  weight: string;
}[] = [
  { key: "platform_functionality",  label: "Platform Functionality",   weight: "25%" },
  { key: "accessibility_compliance",label: "Accessibility & Compliance",weight: "15%" },
  { key: "integration_capability",  label: "Integration Capability",   weight: "15%" },
  { key: "security_and_compliance", label: "Security & Compliance",    weight: "15%" },
  { key: "pricing_transparency",    label: "Pricing Transparency",     weight: "10%" },
  { key: "support_and_training",    label: "Support & Training",       weight: "10%" },
  { key: "enterprise_readiness",    label: "Enterprise Readiness",     weight: "5%"  },
  { key: "innovation_roadmap",      label: "Innovation Roadmap",       weight: "5%"  },
];

const CONTRACT_FIELDS: { key: keyof ProposalData; label: string }[] = [
  { key: "total_cost",             label: "Total Cost"             },
  { key: "pricing_model",          label: "Pricing Model"          },
  { key: "contract_length",        label: "Contract Length"        },
  { key: "sla_uptime",             label: "SLA Uptime"             },
  { key: "security_certifications",label: "Security Certifications"},
  { key: "liability_cap",          label: "Liability Cap"          },
  { key: "governing_law",          label: "Governing Law"          },
];

const SCORE_TIERS = [
  { min: 7, color: "umgreen",  textColor: "var(--mantine-color-umgreen-6)"  },
  { min: 4, color: "umyellow", textColor: "var(--mantine-color-umyellow-7)" },
  { min: 0, color: "ummaroon", textColor: "var(--mantine-color-ummaroon-6)" },
] as const;

function scoreTier(score: number) {
  return SCORE_TIERS.find((t) => score >= t.min)!;
}

const RISK_COLORS: Record<RiskFlag["severity"], string> = {
  HIGH: "ummaroon",
  MEDIUM: "umyellow",
  LOW: "gray",
};

const LABEL_W = 200;
const DATA_W = 200;

const labelCell: CSSProperties = {
  padding: "7px 14px",
  textAlign: "left",
  verticalAlign: "middle",
  borderBottom: "1px solid var(--mantine-color-gray-2)",
  width: LABEL_W,
  whiteSpace: "nowrap",
};

const sectionHeader: CSSProperties = {
  padding: "9px 14px",
  background: "var(--mantine-color-gray-0)",
  borderTop: "1px solid var(--mantine-color-gray-2)",
  borderBottom: "1px solid var(--mantine-color-gray-2)",
};

function dataCell(isWinner: boolean): CSSProperties {
  return {
    padding: "7px 14px",
    textAlign: "center",
    verticalAlign: "middle",
    borderBottom: "1px solid var(--mantine-color-gray-2)",
    background: isWinner ? "var(--mantine-color-umgreen-0)" : undefined,
    width: DATA_W,
  };
}

interface Props {
  proposals: ProposalResult[];
  winner: ProposalResult | null;
}

export function VendorComparisonTable({ proposals, winner }: Props) {
  if (proposals.length < 2) return null;

  const totalCols = proposals.length + 1;

  return (
    <Paper p="lg" radius="md" withBorder bg="white" className="fadeIn">
      <Group mb="md" gap="xs">
        <Text fw={700} size="lg" c="dark">Head-to-Head Comparison</Text>
        <Text size="sm" c="dimmed">— all vendors across every criterion</Text>
      </Group>

      <ScrollArea>
        <table
          style={{
            minWidth: LABEL_W + DATA_W * proposals.length,
            borderCollapse: "collapse",
            tableLayout: "fixed",
            width: "100%",
          }}
        >
          {/* ── Column headers ─────────────────────────────────────── */}
          <thead>
            <tr>
              <th style={{ ...labelCell, borderBottom: "2px solid var(--mantine-color-gray-3)" }} />
              {proposals.map((p) => {
                const isWin = winner?.filename === p.filename;
                const overall = p.scores?.overall;
                const tier = overall != null ? scoreTier(overall / 10) : null;
                return (
                  <th
                    key={p.filename}
                    style={{
                      padding: "12px 14px",
                      textAlign: "center",
                      width: DATA_W,
                      borderBottom: isWin
                        ? "2px solid var(--mantine-color-umgreen-5)"
                        : "2px solid var(--mantine-color-gray-3)",
                      background: isWin ? "var(--mantine-color-umgreen-0)" : undefined,
                    }}
                  >
                    <Stack gap={3} align="center">
                      {isWin && (
                        <Group gap={4} justify="center">
                          <IconAward size={12} color="var(--mantine-color-umgreen-6)" />
                          <Text size="xs" fw={700} tt="uppercase" c="umgreen.6" style={{ letterSpacing: "0.06em" }}>
                            Best Choice
                          </Text>
                        </Group>
                      )}
                      <Text fw={700} size="sm" c="dark" lineClamp={1}>
                        {p.vendor_name ?? p.filename}
                      </Text>
                      {overall != null && tier && (
                        <Text fw={800} size="xl" style={{ color: tier.textColor, lineHeight: 1 }}>
                          {Math.round(overall)}
                          <Text span size="xs" fw={400} c="dimmed"> /100</Text>
                        </Text>
                      )}
                    </Stack>
                  </th>
                );
              })}
            </tr>
          </thead>

          <tbody>
            {/* ── Scores ─────────────────────────────────────────────── */}
            <tr>
              <td colSpan={totalCols} style={sectionHeader}>
                <Text size="xs" fw={700} tt="uppercase" c="dimmed" style={{ letterSpacing: "0.06em" }}>
                  Evaluation Scores
                </Text>
              </td>
            </tr>

            {SCORE_DIMENSIONS.map(({ key, label, weight }) => (
              <tr key={key}>
                <td style={labelCell}>
                  <Group gap={4}>
                    <Text size="xs" c="dark">{label}</Text>
                    <Text size="xs" c="dimmed">· {weight}</Text>
                  </Group>
                </td>
                {proposals.map((p) => {
                  const isWin = winner?.filename === p.filename;
                  const dim = p.scores?.[key];
                  if (!dim) {
                    return (
                      <td key={p.filename} style={dataCell(isWin)}>
                        <Text size="xs" c="dimmed">—</Text>
                      </td>
                    );
                  }
                  const tier = scoreTier(dim.score);
                  return (
                    <td key={p.filename} style={dataCell(isWin)}>
                      <Tooltip label={dim.rationale} multiline w={240} withArrow position="top">
                        <Box style={{ cursor: "help", display: "inline-flex", alignItems: "center", gap: 8 }}>
                          <Box
                            style={{
                              width: 52,
                              height: 5,
                              borderRadius: 999,
                              background: "var(--mantine-color-gray-2)",
                              overflow: "hidden",
                              flexShrink: 0,
                            }}
                          >
                            <Box
                              style={{
                                width: `${(dim.score / 10) * 100}%`,
                                height: "100%",
                                background: `var(--mantine-color-${tier.color}-5)`,
                                borderRadius: 999,
                              }}
                            />
                          </Box>
                          <Text size="xs" fw={600} style={{ color: tier.textColor, minWidth: 24 }}>
                            {dim.score.toFixed(1)}
                          </Text>
                        </Box>
                      </Tooltip>
                    </td>
                  );
                })}
              </tr>
            ))}

            {/* ── Risk flags ─────────────────────────────────────────── */}
            <tr>
              <td colSpan={totalCols} style={sectionHeader}>
                <Text size="xs" fw={700} tt="uppercase" c="dimmed" style={{ letterSpacing: "0.06em" }}>
                  Risk Flags
                </Text>
              </td>
            </tr>

            {(["HIGH", "MEDIUM", "LOW"] as const).map((severity) => (
              <tr key={severity}>
                <td style={labelCell}>
                  <Badge
                    color={RISK_COLORS[severity]}
                    variant={severity === "HIGH" ? "filled" : "light"}
                    size="xs"
                    radius="sm"
                  >
                    {severity}
                  </Badge>
                </td>
                {proposals.map((p) => {
                  const isWin = winner?.filename === p.filename;
                  const count = (p.risks ?? []).filter((r) => r.severity === severity).length;
                  return (
                    <td key={p.filename} style={dataCell(isWin)}>
                      <Text
                        size="sm"
                        fw={count > 0 && severity === "HIGH" ? 700 : 500}
                        c={
                          count === 0
                            ? "dimmed"
                            : severity === "HIGH"
                            ? "ummaroon.6"
                            : severity === "MEDIUM"
                            ? "umyellow.7"
                            : "dark"
                        }
                      >
                        {count}
                      </Text>
                    </td>
                  );
                })}
              </tr>
            ))}

            {/* ── Contract terms ─────────────────────────────────────── */}
            <tr>
              <td colSpan={totalCols} style={sectionHeader}>
                <Text size="xs" fw={700} tt="uppercase" c="dimmed" style={{ letterSpacing: "0.06em" }}>
                  Contract Terms
                </Text>
              </td>
            </tr>

            {CONTRACT_FIELDS.map(({ key, label }) => {
              const hasValue = proposals.some((p) => {
                const v = p.extracted?.[key];
                return v && !(Array.isArray(v) && v.length === 0);
              });
              if (!hasValue) return null;
              return (
                <tr key={key}>
                  <td style={labelCell}>
                    <Text size="xs" c="dark">{label}</Text>
                  </td>
                  {proposals.map((p) => {
                    const isWin = winner?.filename === p.filename;
                    const raw = p.extracted?.[key];
                    const value = Array.isArray(raw) ? raw.join(", ") : raw ?? null;
                    return (
                      <td key={p.filename} style={dataCell(isWin)}>
                        {value ? (
                          <Tooltip
                            label={value}
                            multiline
                            w={240}
                            withArrow
                            position="top"
                            disabled={value.length <= 55}
                          >
                            <Text
                              size="xs"
                              c="dark"
                              lineClamp={2}
                              style={{ cursor: value.length > 55 ? "help" : undefined, textAlign: "left" }}
                            >
                              {value}
                            </Text>
                          </Tooltip>
                        ) : (
                          <Text size="xs" c="dimmed">—</Text>
                        )}
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </ScrollArea>
    </Paper>
  );
}
