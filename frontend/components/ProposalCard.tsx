"use client";

import { useState } from "react";
import {
  Paper, Text, Group, Stack, Badge, Progress, Collapse,
  Button, Divider, Box, ThemeIcon,
} from "@mantine/core";
import {
  IconBuilding, IconChevronDown, IconChevronUp, IconAlertTriangle, IconAward,
} from "@tabler/icons-react";
import type { ProposalResult, RiskFlag, ScoreCard } from "@/lib/types";

const DIMENSIONS: { key: keyof Omit<ScoreCard, "overall">; label: string }[] = [
  { key: "platform_functionality", label: "Platform Functionality" },
  { key: "accessibility_compliance", label: "Accessibility & Compliance" },
  { key: "integration_capability", label: "Integration Capability" },
  { key: "pricing_transparency", label: "Pricing Transparency" },
  { key: "security_and_compliance", label: "Security & Compliance" },
  { key: "support_and_training", label: "Support & Training" },
  { key: "enterprise_readiness", label: "Enterprise Readiness" },
  { key: "risk_level", label: "Risk Level" },
];

const CONTRACT_FIELDS: { key: keyof import("@/lib/types").ProposalData; label: string }[] = [
  { key: "total_cost", label: "Total Cost" },
  { key: "pricing_model", label: "Pricing Model" },
  { key: "price_escalation", label: "Price Escalation" },
  { key: "contract_length", label: "Contract Length" },
  { key: "renewal_terms", label: "Renewal Terms" },
  { key: "termination_clause", label: "Termination Clause" },
  { key: "liability_cap", label: "Liability Cap" },
  { key: "sla_uptime", label: "SLA Uptime" },
  { key: "security_certifications", label: "Security Certifications" },
  { key: "data_processing_agreement", label: "Data Processing Agreement" },
  { key: "governing_law", label: "Governing Law" },
  { key: "support_model", label: "Support Model" },
];

function scoreColor(score: number): string {
  if (score >= 7) return "umgreen";
  if (score >= 4) return "umyellow";
  return "ummaroon";
}

function scoreTextColor(score: number): string {
  if (score >= 7) return "var(--mantine-color-umgreen-6)";
  if (score >= 4) return "var(--mantine-color-umyellow-7)";
  return "var(--mantine-color-ummaroon-6)";
}

function riskColor(severity: RiskFlag["severity"]): string {
  if (severity === "HIGH") return "ummaroon";
  if (severity === "MEDIUM") return "umyellow";
  return "gray";
}

interface Props {
  proposal: ProposalResult;
  recommended?: boolean;
}

export function ProposalCard({ proposal, recommended = false }: Props) {
  const [detailsOpen, setDetailsOpen] = useState(false);
  const { vendor_name, scores, risks, extracted, filename } = proposal;

  const displayName = vendor_name ?? filename;
  const overall = scores?.overall ?? null;

  const highRisks = risks?.filter((r) => r.severity === "HIGH") ?? [];
  const medRisks = risks?.filter((r) => r.severity === "MEDIUM") ?? [];
  const lowRisks = risks?.filter((r) => r.severity === "LOW") ?? [];
  const sortedRisks = [...highRisks, ...medRisks, ...lowRisks];

  return (
    <Paper
      p="lg"
      radius="md"
      withBorder
      bg="white"
      className="fadeIn"
      style={{
        height: "100%",
        borderColor: recommended ? "var(--mantine-color-umgreen-5)" : undefined,
        borderWidth: recommended ? 2 : 1,
        boxShadow: recommended ? "0 0 0 4px var(--mantine-color-umgreen-1)" : undefined,
      }}
    >
      <Stack gap="md">
        {/* Recommended banner */}
        {recommended && (
          <Group gap="xs" align="center">
            <IconAward size={16} color="var(--mantine-color-umgreen-6)" />
            <Text size="xs" fw={700} tt="uppercase" c="umgreen.6" style={{ letterSpacing: "0.06em" }}>
              Recommended
            </Text>
          </Group>
        )}

        {/* Header */}
        <Group justify="space-between" align="flex-start" gap="sm">
          <Group gap="sm" style={{ flex: 1 }}>
            <ThemeIcon size={40} radius="xl" variant="light" color="umblue">
              <IconBuilding size={20} />
            </ThemeIcon>
            <Box style={{ flex: 1 }}>
              <Text fw={700} size="lg" c="dark" lineClamp={1}>
                {displayName}
              </Text>
              <Text size="xs" c="dimmed">{filename}</Text>
            </Box>
          </Group>
          {overall !== null && (
            <Box ta="center" style={{ minWidth: 64 }}>
              <Text
                size="2rem"
                fw={800}
                style={{ color: scoreTextColor(overall), lineHeight: 1 }}
              >
                {overall.toFixed(1)}
              </Text>
              <Text size="xs" c="dimmed" fw={500}>/ 10</Text>
            </Box>
          )}
        </Group>

        {/* Overall score bar */}
        {overall !== null && (
          <Progress
            value={(overall / 10) * 100}
            color={scoreColor(overall)}
            size="lg"
            radius="xl"
          />
        )}

        {/* Dimension scores */}
        {scores && (
          <Stack gap={6}>
            {DIMENSIONS.map(({ key, label }) => {
              const dim = scores[key];
              return (
                <Box key={key}>
                  <Group justify="space-between" mb={2}>
                    <Text size="xs" c="dimmed">{label}</Text>
                    <Text size="xs" fw={600} style={{ color: scoreTextColor(dim.score) }}>
                      {dim.score.toFixed(1)}
                    </Text>
                  </Group>
                  <Progress
                    value={(dim.score / 10) * 100}
                    color={scoreColor(dim.score)}
                    size="sm"
                    radius="xl"
                  />
                </Box>
              );
            })}
          </Stack>
        )}

        {/* Risk tags */}
        {sortedRisks.length > 0 && (
          <>
            <Divider />
            <Stack gap="xs">
              <Group gap="xs" align="center">
                <IconAlertTriangle size={14} color="var(--mantine-color-gray-6)" />
                <Text size="xs" fw={600} c="dimmed" tt="uppercase" style={{ letterSpacing: "0.05em" }}>
                  Risk Flags
                </Text>
              </Group>
              <Group gap="xs" wrap="wrap">
                {sortedRisks.map((risk, i) => (
                  <Badge
                    key={i}
                    color={riskColor(risk.severity)}
                    variant={risk.severity === "HIGH" ? "filled" : "light"}
                    size="sm"
                    radius="sm"
                    title={risk.explanation}
                  >
                    {risk.clause.length > 40 ? risk.clause.slice(0, 38) + "…" : risk.clause}
                  </Badge>
                ))}
              </Group>
            </Stack>
          </>
        )}

        {/* Contract details toggle */}
        {extracted && (
          <>
            <Divider />
            <Button
              variant="subtle"
              color="umblue"
              size="xs"
              rightSection={detailsOpen ? <IconChevronUp size={14} /> : <IconChevronDown size={14} />}
              onClick={() => setDetailsOpen((o) => !o)}
              px={0}
              style={{ alignSelf: "flex-start" }}
            >
              {detailsOpen ? "Hide" : "Show"} contract details
            </Button>
            <Collapse expanded={detailsOpen}>
              <Stack gap="xs">
                {CONTRACT_FIELDS.map(({ key, label }) => {
                  const value = extracted[key];
                  if (!value || (Array.isArray(value) && value.length === 0)) return null;
                  return (
                    <Box key={key}>
                      <Text size="xs" fw={600} c="dimmed" tt="uppercase" style={{ letterSpacing: "0.04em" }}>
                        {label}
                      </Text>
                      <Text size="sm" c="dark">
                        {Array.isArray(value) ? value.join(", ") : value}
                      </Text>
                    </Box>
                  );
                })}
              </Stack>
            </Collapse>
          </>
        )}
      </Stack>
    </Paper>
  );
}
