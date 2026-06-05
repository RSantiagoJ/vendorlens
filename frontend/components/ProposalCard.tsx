"use client";

import { useEffect, useState } from "react";

function useCountUp(target: number, duration = 900): number {
  const [value, setValue] = useState(0);
  useEffect(() => {
    let rafId: number;
    const start = performance.now();
    const tick = (now: number) => {
      const t = Math.min((now - start) / duration, 1);
      setValue(Math.round((1 - Math.pow(1 - t, 3)) * target));
      if (t < 1) rafId = requestAnimationFrame(tick);
    };
    rafId = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafId);
  }, [target, duration]);
  return value;
}

import {
  Paper, Text, Group, Stack, Badge, Collapse,
  Button, Divider, Box, ThemeIcon, Tooltip, Popover, Progress,
} from "@mantine/core";
import {
  IconBuilding, IconChevronDown, IconChevronUp, IconAlertTriangle,
  IconAward, IconInfoCircle, IconArrowUp,
} from "@tabler/icons-react";
import type { ProposalResult, RiskFlag, ScoreCard } from "@/lib/types";

const RING_R = 40;
const RING_C = 2 * Math.PI * RING_R;

function ScoreRing({ overall, animated, tier }: {
  overall: number;
  animated: number;
  tier: typeof SCORE_TIERS[number];
}) {
  const offset = RING_C - (animated / 100) * RING_C;
  return (
    <Stack align="center" gap={4} style={{ flexShrink: 0 }}>
      <Box style={{ position: "relative", width: 96, height: 96 }}>
        <svg width="96" height="96" viewBox="0 0 96 96" style={{ transform: "rotate(-90deg)" }}>
          <circle cx="48" cy="48" r={RING_R} fill="none" stroke="var(--mantine-color-gray-2)" strokeWidth="8" />
          <circle
            cx="48" cy="48" r={RING_R} fill="none"
            stroke={`var(--mantine-color-${tier.color}-5)`}
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={RING_C}
            strokeDashoffset={offset}
            style={{ transition: "stroke-dashoffset 0.05s linear" }}
          />
        </svg>
        <Box style={{
          position: "absolute", inset: 0,
          display: "flex", flexDirection: "column",
          alignItems: "center", justifyContent: "center", gap: 1,
        }}>
          <Text fw={900} style={{ color: tier.textColor, fontSize: "1.5rem", lineHeight: 1 }}>
            {animated}
          </Text>
          <Text size="xs" c="dimmed" fw={500} style={{ lineHeight: 1 }}>/100</Text>
        </Box>
      </Box>
      <Badge size="xs" radius="sm" variant="light" color={tier.color}>
        {overall >= 70 ? "Meets" : overall >= 40 ? "Review" : "Fails"}
      </Badge>
    </Stack>
  );
}

const DIMENSIONS: { key: keyof Omit<ScoreCard, "overall">; label: string }[] = [
  { key: "platform_functionality",  label: "Platform Functionality" },
  { key: "accessibility_compliance", label: "Accessibility & Compliance" },
  { key: "integration_capability",  label: "Integration Capability" },
  { key: "pricing_transparency",    label: "Pricing Transparency" },
  { key: "security_and_compliance", label: "Security & Compliance" },
  { key: "support_and_training",    label: "Support & Training" },
  { key: "enterprise_readiness",    label: "Enterprise Readiness" },
  { key: "innovation_roadmap",      label: "Innovation Roadmap" },
  { key: "risk_level",              label: "Risk Level" },
];

const CONTRACT_FIELDS: { key: keyof import("@/lib/types").ProposalData; label: string }[] = [
  { key: "total_cost",              label: "Total Cost" },
  { key: "pricing_model",          label: "Pricing Model" },
  { key: "price_escalation",       label: "Price Escalation" },
  { key: "contract_length",        label: "Contract Length" },
  { key: "renewal_terms",          label: "Renewal Terms" },
  { key: "termination_clause",     label: "Termination Clause" },
  { key: "liability_cap",          label: "Liability Cap" },
  { key: "sla_uptime",             label: "SLA Uptime" },
  { key: "security_certifications", label: "Security Certifications" },
  { key: "data_processing_agreement", label: "Data Processing Agreement" },
  { key: "governing_law",          label: "Governing Law" },
  { key: "support_model",          label: "Support Model" },
];

const SCORE_TIERS = [
  { min: 7, color: "umgreen",  textColor: "var(--mantine-color-umgreen-6)" },
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

const SEVERITY_ORDER: Record<RiskFlag["severity"], number> = { HIGH: 0, MEDIUM: 1, LOW: 2 };

interface Props {
  proposal: ProposalResult;
  recommended?: boolean;
  showBadge?: boolean;
  winnerScores?: ScoreCard;
}

export function ProposalCard({ proposal, recommended = false, showBadge = true, winnerScores }: Props) {
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [openRationale, setOpenRationale] = useState<string | null>(null);
  const { vendor_name, scores, risks, extracted, filename } = proposal;

  const displayName = vendor_name ?? filename;
  const overall = scores?.overall ?? null;
  const animatedScore = useCountUp(overall ?? 0);

  const sortedRisks = [...(risks ?? [])].sort(
    (a, b) => SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity]
  );

  // Top 2 dimensions where this vendor trails the winner most
  const gapToWin = !recommended && winnerScores && scores
    ? DIMENSIONS
        .map(({ key, label }) => ({
          key,
          label,
          gap: parseFloat((winnerScores[key].score - scores[key].score).toFixed(1)),
        }))
        .filter((g) => g.gap >= 0.5)
        .sort((a, b) => b.gap - a.gap)
        .slice(0, 2)
    : [];

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
        boxShadow: recommended
          ? "0 0 0 4px var(--mantine-color-umgreen-1), 0 8px 32px rgba(0,0,0,0.10)"
          : "0 1px 4px rgba(0,0,0,0.04)",
        transform: recommended ? "scale(1.018)" : undefined,
        position: "relative",
        zIndex: recommended ? 1 : undefined,
        transition: "box-shadow 200ms ease, transform 200ms ease",
      }}
    >
      <Stack gap="md">
        {/* Best Choice banner */}
        {recommended && showBadge && (
          <Group gap="xs" align="center">
            <IconAward size={16} color="var(--mantine-color-umgreen-6)" />
            <Text size="xs" fw={700} tt="uppercase" c="umgreen.6" style={{ letterSpacing: "0.06em" }}>
              Best Choice
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
              <Text fw={700} size="lg" c="dark" lineClamp={1}>{displayName}</Text>
              <Text size="xs" c="dimmed">{filename}</Text>
            </Box>
          </Group>
          {overall !== null && (
            <ScoreRing overall={overall} animated={animatedScore} tier={scoreTier(overall / 10)} />
          )}
        </Group>


        {/* Gap to win — only shown on non-recommended vendors */}
        {gapToWin.length > 0 && (
          <Box
            p="xs"
            style={{
              background: "var(--mantine-color-gray-0)",
              borderRadius: "var(--mantine-radius-sm)",
              borderLeft: "3px solid var(--mantine-color-umyellow-4)",
            }}
          >
            <Group gap={6} align="center" mb={6}>
              <IconArrowUp size={12} color="var(--mantine-color-umyellow-6)" />
              <Text size="xs" fw={600} c="dimmed" tt="uppercase" style={{ letterSpacing: "0.04em" }}>
                Gap to win
              </Text>
            </Group>
            <Group gap="xs" wrap="wrap">
              {gapToWin.map(({ key, label, gap }) => (
                <Badge key={key} size="xs" variant="outline" color="umyellow">
                  +{gap} {label}
                </Badge>
              ))}
            </Group>
          </Box>
        )}

        {/* Dimension scores — click any row to see AI rationale */}
        {scores && (
          <Stack gap={6}>
            {DIMENSIONS.map(({ key, label }) => {
              const dim = scores[key];
              const isOpen = openRationale === key;
              return (
                <Popover
                  key={key}
                  opened={isOpen}
                  onClose={() => setOpenRationale(null)}
                  position="bottom"
                  withArrow
                  shadow="md"
                  width={280}
                >
                  <Popover.Target>
                    <Box
                      onClick={() => setOpenRationale(isOpen ? null : key)}
                      style={{ cursor: "pointer" }}
                    >
                      <Group justify="space-between" mb={2}>
                        <Text size="xs" c="dimmed">{label}</Text>
                        <Group gap={4} align="center">
                          <Text size="xs" fw={600} style={{ color: scoreTier(dim.score).textColor }}>
                            {dim.score.toFixed(1)}
                          </Text>
                          <IconInfoCircle size={11} color="var(--mantine-color-gray-4)" />
                        </Group>
                      </Group>
                      <Progress
                        value={(dim.score / 10) * 100}
                        color={scoreTier(dim.score).color}
                        size="sm"
                        radius="xl"
                      />
                    </Box>
                  </Popover.Target>
                  <Popover.Dropdown>
                    <Stack gap={8}>
                      <Group justify="space-between" align="center">
                        <Text size="xs" fw={700} c="dark">{label}</Text>
                        <Badge size="xs" variant="light" color={scoreTier(dim.score).color}>
                          {dim.score.toFixed(1)} / 10
                        </Badge>
                      </Group>
                      <Text size="xs" c="dimmed" style={{ lineHeight: 1.55, fontStyle: "italic" }}>
                        {dim.rationale}
                      </Text>
                    </Stack>
                  </Popover.Dropdown>
                </Popover>
              );
            })}
          </Stack>
        )}

        {/* Risk flags */}
        {sortedRisks.length > 0 && (
          <>
            <Divider />
            <Stack gap="xs">
              <Group gap="xs" align="center" justify="space-between">
                <Group gap="xs" align="center">
                  <IconAlertTriangle size={14} color="var(--mantine-color-gray-6)" />
                  <Text size="xs" fw={600} c="dimmed" tt="uppercase" style={{ letterSpacing: "0.05em" }}>
                    Risk Flags
                  </Text>
                </Group>
                <Group gap="xs">
                  {(["HIGH", "MEDIUM", "LOW"] as const)
                    .filter((s) => sortedRisks.some((r) => r.severity === s))
                    .map((s) => (
                      <Badge key={s} color={RISK_COLORS[s]} variant={s === "HIGH" ? "filled" : "light"} size="xs" radius="sm">
                        {s}
                      </Badge>
                    ))}
                </Group>
              </Group>
              <Group gap="xs" wrap="wrap">
                {sortedRisks.map((risk, i) => (
                  <Tooltip
                    key={i}
                    label={
                      <Stack gap={4} p={4}>
                        <Text size="xs" fw={600}>{risk.clause}</Text>
                        <Text size="xs">{risk.explanation}</Text>
                        {risk.recommendation && (
                          <Text size="xs" style={{ fontStyle: "italic", opacity: 0.75 }}>
                            → {risk.recommendation}
                          </Text>
                        )}
                        {risk.policy_excerpt && (
                          <Box
                            mt={4}
                            p={6}
                            style={{
                              background: "rgba(255,255,255,0.08)",
                              borderRadius: 4,
                              borderLeft: "2px solid rgba(255,255,255,0.25)",
                            }}
                          >
                            <Text size="xs" c="dimmed" mb={2} tt="uppercase" style={{ letterSpacing: "0.04em", fontSize: 9 }}>
                              Policy
                            </Text>
                            <Text size="xs" style={{ fontStyle: "italic", opacity: 0.85, lineHeight: 1.45 }}>
                              "{risk.policy_excerpt}"
                            </Text>
                          </Box>
                        )}
                      </Stack>
                    }
                    multiline
                    w={300}
                    withArrow
                    position="top"
                  >
                    <Badge
                      color={RISK_COLORS[risk.severity]}
                      variant={risk.severity === "HIGH" ? "filled" : "light"}
                      size="sm"
                      radius="sm"
                      style={{ cursor: "help" }}
                    >
                      {risk.clause.length > 40 ? risk.clause.slice(0, 38) + "…" : risk.clause}
                    </Badge>
                  </Tooltip>
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
