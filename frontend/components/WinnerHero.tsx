"use client";

import { useEffect, useState } from "react";

function useCountUp(target: number, duration = 1100): number {
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

import { Box, Group, Stack, Text, Badge, ThemeIcon, Divider, Tooltip } from "@mantine/core";
import { IconAward, IconShieldCheck, IconTrendingUp } from "@tabler/icons-react";
import type { ProposalResult, ScoreCard } from "@/lib/types";
import { scoreTier, scoreLabel } from "@/lib/scoring";

const DIMENSIONS: { key: keyof Omit<ScoreCard, "overall">; label: string; description: string }[] = [
  { key: "platform_functionality",   label: "Platform Functionality",    description: "Core ERP modules — financial management (GL, AP/AR, grants, procurement), HR, payroll, and faculty-specific workflows. Highest-weighted criterion (25%)." },
  { key: "security_and_compliance",  label: "Security & Compliance",     description: "SOC 2 Type II / ISO 27001 certification, data processing agreement covering FERPA and GLBA, encryption standards, disaster recovery documentation, and data ownership terms." },
  { key: "integration_capability",   label: "Integration Capability",    description: "Native connectors for Banner/PeopleSoft SIS, banking and ACH, benefits carrier EDI, SSO/SAML 2.0 with Azure AD and Okta, and open REST API quality." },
  { key: "accessibility_compliance", label: "Accessibility",             description: "GASB accounting standards, 2 CFR 200 grant compliance, IRS reporting (W-2, 1099, ACA), NACUBO reporting, and WCAG 2.1 AA accessibility for employee-facing portals." },
  { key: "support_and_training",     label: "Support & Training",        description: "Implementation methodology, named staffing model, hypercare period, post-go-live SLAs with financial penalties, 24/7 payroll window coverage, and higher education references." },
  { key: "pricing_transparency",     label: "Pricing Transparency",      description: "Clarity of implementation costs, subscription pricing, annual escalation rate, data migration fees, and total cost of ownership over the contract term." },
  { key: "enterprise_readiness",     label: "Enterprise Readiness",      description: "Multi-campus and multi-entity accounting, granular role-based access control, published uptime history, and disaster recovery RTO/RPO documentation." },
  { key: "innovation_roadmap",       label: "Innovation Roadmap",        description: "18–24 month product roadmap, AI/automation plans (anomaly detection, spend analytics), continuous delivery model, and higher education advisory board influence." },
];

interface Props {
  winner: ProposalResult;
  totalVendors: number;
  totalRisks: number;
}

export function WinnerHero({ winner, totalVendors, totalRisks }: Props) {
  const overall = winner.scores?.overall ?? 0;
  const animatedScore = useCountUp(overall);

  const topStrengths = winner.scores
    ? DIMENSIONS
        .map(({ key, label, description }) => ({ label, description, score: winner.scores![key]?.score ?? 0 }))
        .sort((a, b) => b.score - a.score)
        .slice(0, 3)
    : [];

  const allRisks = winner.risks ?? [];
  const riskBreakdown = {
    HIGH: allRisks.filter((r) => r.severity === "HIGH").length,
    MEDIUM: allRisks.filter((r) => r.severity === "MEDIUM").length,
    LOW: allRisks.filter((r) => r.severity === "LOW").length,
  };
  const totalWinnerRisks = riskBreakdown.HIGH + riskBreakdown.MEDIUM + riskBreakdown.LOW;
  const highRisks = riskBreakdown.HIGH;
  const tier = scoreTier(overall).color;

  return (
    <Box
      className="fadeIn"
      style={{
        background: "linear-gradient(135deg, var(--mantine-color-umgreen-0) 0%, #ffffff 60%)",
        border: "1.5px solid var(--mantine-color-umgreen-3)",
        borderRadius: "var(--mantine-radius-md)",
        padding: "var(--mantine-spacing-xl)",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Background accent */}
      <Box
        style={{
          position: "absolute",
          top: -40,
          right: -40,
          width: 220,
          height: 220,
          borderRadius: "50%",
          background: "var(--mantine-color-umgreen-1)",
          opacity: 0.5,
          pointerEvents: "none",
        }}
      />

      <div style={{ display: "flex", flexWrap: "wrap", gap: "var(--mantine-spacing-xl)", alignItems: "flex-start", position: "relative" }}>
        {/* Left — identity + score */}
        <Stack gap="md" style={{ flex: "1 1 280px" }}>
          <Group gap="xs">
            <ThemeIcon size={22} variant="filled" color="umgreen" radius="xl">
              <IconAward size={13} />
            </ThemeIcon>
            <Text size="xs" fw={800} tt="uppercase" c="umgreen.7" style={{ letterSpacing: "0.1em" }}>
              Recommended Vendor
            </Text>
          </Group>

          <Box>
            <Text
              fw={900}
              c="dark"
              style={{ fontSize: "clamp(1.6rem, 3vw, 2.4rem)", lineHeight: 1.1, letterSpacing: "-0.02em" }}
            >
              {winner.vendor_name ?? winner.filename}
            </Text>
          </Box>

          {/* Score bar */}
          <Group gap="lg" align="flex-end">
            <Stack gap={2} style={{ minWidth: 80 }}>
              <Text
                fw={900}
                style={{
                  fontSize: "clamp(2.8rem, 5vw, 4rem)",
                  lineHeight: 1,
                  color: `var(--mantine-color-${tier}-6)`,
                  fontVariantNumeric: "tabular-nums",
                }}
              >
                {animatedScore}
              </Text>
              <Text size="sm" c="dimmed" fw={500}>/ 10</Text>
            </Stack>

            <Stack gap={6} style={{ flex: 1, maxWidth: 320 }}>
              {/* Animated fill bar */}
              <Box
                style={{
                  height: 10,
                  borderRadius: 999,
                  background: "var(--mantine-color-gray-2)",
                  overflow: "hidden",
                }}
              >
                <Box
                  style={{
                    width: `${(animatedScore / 10) * 100}%`,
                    height: "100%",
                    borderRadius: 999,
                    background: `var(--mantine-color-${tier}-5)`,
                    transition: "width 0.05s linear",
                  }}
                />
              </Box>
              <Group gap="md">
                <Badge size="sm" color={tier} variant={tier === "umgreen" ? "filled" : "light"} radius="sm">
                  {scoreLabel(overall)}
                </Badge>
                {highRisks === 0 && (
                  <Group gap={4}>
                    <IconShieldCheck size={13} color="var(--mantine-color-umgreen-6)" />
                    <Text size="xs" c="umgreen.6" fw={600}>No high risks</Text>
                  </Group>
                )}
              </Group>
            </Stack>
          </Group>

          {/* Stats line */}
          <Group gap="xs">
            <Text size="xs" c="dimmed">
              {totalVendors} vendor{totalVendors !== 1 ? "s" : ""} evaluated
            </Text>
            <Text size="xs" c="dimmed">·</Text>
            <Text size="xs" c="dimmed">
              {totalRisks} risk flag{totalRisks !== 1 ? "s" : ""} across all proposals
            </Text>
            {highRisks > 0 && (
              <>
                <Text size="xs" c="dimmed">·</Text>
                <Text size="xs" c="ummaroon.6" fw={600}>{highRisks} HIGH on this vendor</Text>
              </>
            )}
          </Group>

          {/* Risk breakdown bar for this vendor */}
          {totalWinnerRisks > 0 && (
            <Box>
              <Text size="xs" fw={600} c="dimmed" tt="uppercase" mb={6} style={{ letterSpacing: "0.05em" }}>
                This vendor's risk profile
              </Text>
              <Box
                style={{
                  height: 7,
                  borderRadius: 999,
                  display: "flex",
                  overflow: "hidden",
                  background: "var(--mantine-color-gray-2)",
                  marginBottom: 8,
                }}
              >
                {riskBreakdown.HIGH > 0 && (
                  <Box style={{ width: `${(riskBreakdown.HIGH / totalWinnerRisks) * 100}%`, background: "var(--mantine-color-ummaroon-5)" }} />
                )}
                {riskBreakdown.MEDIUM > 0 && (
                  <Box style={{ width: `${(riskBreakdown.MEDIUM / totalWinnerRisks) * 100}%`, background: "var(--mantine-color-umyellow-5)" }} />
                )}
                {riskBreakdown.LOW > 0 && (
                  <Box style={{ width: `${(riskBreakdown.LOW / totalWinnerRisks) * 100}%`, background: "var(--mantine-color-gray-4)" }} />
                )}
              </Box>
              <Group gap="md">
                {(["HIGH", "MEDIUM", "LOW"] as const)
                  .filter((s) => riskBreakdown[s] > 0)
                  .map((s) => (
                    <Tooltip
                      key={s}
                      label={
                        s === "HIGH"
                          ? "Requires immediate negotiation or legal review before signing. Contract terms that could expose the institution to significant financial or legal risk."
                          : s === "MEDIUM"
                          ? "Worth negotiating, but not a blocker. Terms that deviate from best practice or institutional policy but carry manageable risk."
                          : "Minor deviations from preferred terms. Note for the record but unlikely to affect the decision."
                      }
                      multiline
                      w={220}
                      withArrow
                      position="bottom"
                    >
                    <Group gap={5} align="center" style={{ cursor: "help" }}>
                      <Box
                        style={{
                          width: 8, height: 8, borderRadius: "50%", flexShrink: 0,
                          background: s === "HIGH"
                            ? "var(--mantine-color-ummaroon-5)"
                            : s === "MEDIUM"
                            ? "var(--mantine-color-umyellow-5)"
                            : "var(--mantine-color-gray-4)",
                        }}
                      />
                      <Text size="xs" c="dimmed">{riskBreakdown[s]} {s}</Text>
                    </Group>
                    </Tooltip>
                  ))}
              </Group>
            </Box>
          )}
        </Stack>

        {/* Right — top strengths */}
        {topStrengths.length > 0 && (
          <Box
            style={{
              background: "var(--mantine-color-gray-0)",
              border: "1px solid var(--mantine-color-gray-3)",
              borderRadius: "var(--mantine-radius-md)",
              padding: "var(--mantine-spacing-lg)",
              minWidth: 260,
              flex: "0 0 auto",
              boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
            }}
          >
            <Group gap={8} mb="md">
              <IconTrendingUp size={16} color="var(--mantine-color-umgreen-6)" />
              <Text size="sm" fw={700} tt="uppercase" c="dimmed" style={{ letterSpacing: "0.06em" }}>
                Top Strengths
              </Text>
            </Group>
            <Stack gap={12}>
              {topStrengths.map(({ label, description, score }, i) => (
                <Box key={label}>
                  <Group justify="space-between" mb={5}>
                    <Tooltip label={description} multiline w={240} withArrow position="left" openDelay={300}>
                      <Text size="sm" c="dark" fw={i === 0 ? 700 : 500} style={{ cursor: "help", textDecoration: "underline dotted" }}>{label}</Text>
                    </Tooltip>
                    <Text
                      size="sm"
                      fw={800}
                      style={{ color: score >= 7 ? "var(--mantine-color-umgreen-6)" : "var(--mantine-color-umyellow-7)" }}
                    >
                      {score.toFixed(1)}
                    </Text>
                  </Group>
                  <Box style={{ height: 6, borderRadius: 999, background: "var(--mantine-color-gray-1)", overflow: "hidden" }}>
                    <Box
                      style={{
                        width: `${(score / 10) * 100}%`,
                        height: "100%",
                        borderRadius: 999,
                        background: score >= 7
                          ? "var(--mantine-color-umgreen-5)"
                          : "var(--mantine-color-umyellow-5)",
                      }}
                    />
                  </Box>
                  {i < topStrengths.length - 1 && <Divider mt={12} color="gray.1" />}
                </Box>
              ))}
            </Stack>
          </Box>
        )}
      </div>
    </Box>
  );
}
