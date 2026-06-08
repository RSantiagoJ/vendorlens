"use client";

import type { NegotiationBrief } from "@/lib/types";
import {
  Accordion,
  Badge,
  Box,
  Group,
  Stack,
  Table,
  Text,
  ThemeIcon,
  Tooltip,
} from "@mantine/core";
import {
  IconAlertTriangle,
  IconBriefcase,
  IconGift,
  IconInfoCircle,
  IconScale,
  IconTarget,
} from "@tabler/icons-react";

interface Props {
  plans: NegotiationBrief[];
}

function SectionLabel({ icon, label, tooltip }: { icon: React.ReactNode; label: string; tooltip: string }) {
  return (
    <Group gap={6} mb={8}>
      {icon}
      <Text size="xs" tt="uppercase" fw={700} c="dimmed" style={{ letterSpacing: "0.07em" }}>
        {label}
      </Text>
      <Tooltip label={tooltip} multiline w={260} withArrow position="top">
        <IconInfoCircle size={13} color="var(--mantine-color-gray-5)" style={{ cursor: "help" }} />
      </Tooltip>
    </Group>
  );
}

export function NegotiationPlaybook({ plans }: Props) {
  if (!plans || plans.length === 0) return null;

  return (
    <Accordion variant="separated" radius="md" defaultValue={plans[0]?.vendor_name}>
      {plans.map((brief) => (
        <Accordion.Item key={brief.vendor_name} value={brief.vendor_name}>
          <Accordion.Control>
            <Group gap="sm">
              <ThemeIcon size="sm" variant="light" color="umblue">
                <IconBriefcase size={14} />
              </ThemeIcon>
              <Text fw={700}>{brief.vendor_name}</Text>
            </Group>
          </Accordion.Control>
          <Accordion.Panel>
            <Stack gap="lg" py="xs">
              {/* Opening Posture */}
              <Box
                style={{
                  background: "linear-gradient(90deg, #0d1a2e 0%, #1c0810 100%)",
                  borderRadius: 8,
                  padding: "12px 16px",
                  borderLeft: "3px solid var(--mantine-color-umblue-5)",
                }}
              >
                <Tooltip
                  label="The overall tone and posture to open with — sets the dynamic before any specific asks."
                  multiline
                  w={280}
                  withArrow
                  position="top-start"
                >
                  <Group gap={6} mb={4} style={{ cursor: "help", display: "inline-flex" }}>
                    <Text size="xs" tt="uppercase" fw={700} c="umblue.3" style={{ letterSpacing: "0.07em" }}>
                      Opening Posture
                    </Text>
                    <IconInfoCircle size={12} color="rgba(100,160,255,0.6)" />
                  </Group>
                </Tooltip>
                <Text style={{ color: "rgba(255,255,255,0.88)", fontSize: "0.95rem", lineHeight: 1.55 }}>
                  {brief.overall_approach}
                </Text>
              </Box>

              {/* Priority Tactics table */}
              {brief.priority_tactics.length > 0 && (
                <Box>
                  <SectionLabel
                    icon={<IconTarget size={14} color="var(--mantine-color-umblue-6)" />}
                    label="Priority Tactics"
                    tooltip="The 3–5 highest-leverage negotiation moves, grounded in actual contract terms and scores. Ranked by impact."
                  />
                  <Box style={{ borderRadius: 8, overflow: "hidden", border: "1px solid var(--mantine-color-gray-3)" }}>
                    <Table striped highlightOnHover withColumnBorders={false}>
                      <Table.Thead style={{ background: "#f8f9fa" }}>
                        <Table.Tr>
                          <Table.Th style={{ width: "18%", fontSize: "0.75rem", color: "#666", fontWeight: 700 }}>
                            AREA
                          </Table.Th>
                          <Table.Th style={{ width: "27%", fontSize: "0.75rem", color: "#666", fontWeight: 700 }}>
                            <Tooltip label="What the vendor's current contract draft says." withArrow>
                              <span style={{ cursor: "help", borderBottom: "1px dashed #aaa" }}>THEIR POSITION</span>
                            </Tooltip>
                          </Table.Th>
                          <Table.Th style={{ width: "27%", fontSize: "0.75rem", color: "#666", fontWeight: 700 }}>
                            <Tooltip label="What you're asking for in this negotiation." withArrow>
                              <span style={{ cursor: "help", borderBottom: "1px dashed #aaa" }}>OUR ASK</span>
                            </Tooltip>
                          </Table.Th>
                          <Table.Th style={{ width: "28%", fontSize: "0.75rem", color: "#666", fontWeight: 700 }}>
                            <Tooltip label="Why you have negotiating power here — competitor scores, risk flags, or policy requirements." withArrow multiline w={220}>
                              <span style={{ cursor: "help", borderBottom: "1px dashed #aaa" }}>LEVERAGE</span>
                            </Tooltip>
                          </Table.Th>
                        </Table.Tr>
                      </Table.Thead>
                      <Table.Tbody>
                        {brief.priority_tactics.map((tactic, i) => (
                          <Table.Tr key={i}>
                            <Table.Td>
                              <Text fw={600} size="sm">{tactic.area}</Text>
                            </Table.Td>
                            <Table.Td>
                              <Text size="sm" c="dimmed">{tactic.their_position}</Text>
                            </Table.Td>
                            <Table.Td>
                              <Text size="sm" fw={500} c="umblue.7">{tactic.our_ask}</Text>
                            </Table.Td>
                            <Table.Td>
                              <Text size="sm" c="dark">{tactic.leverage}</Text>
                            </Table.Td>
                          </Table.Tr>
                        ))}
                      </Table.Tbody>
                    </Table>
                  </Box>
                </Box>
              )}

              {/* Red Lines + Concessions */}
              <Group gap="md" align="flex-start" grow>
                {brief.red_lines.length > 0 && (
                  <Box style={{ minWidth: 0 }}>
                    <SectionLabel
                      icon={<IconAlertTriangle size={14} color="var(--mantine-color-red-6)" />}
                      label="Red Lines"
                      tooltip="Non-negotiables. If the vendor won't meet these, walk away — the risk or policy exposure is too high to proceed."
                    />
                    <Stack gap={6}>
                      {brief.red_lines.map((line, i) => (
                        <Tooltip key={i} label="Walk away if the vendor won't agree to this." position="top-start" withArrow>
                          <Badge
                            variant="light"
                            color="red"
                            radius="sm"
                            size="md"
                            style={{ cursor: "help", whiteSpace: "normal", height: "auto", padding: "6px 10px", textTransform: "none", fontWeight: 500, fontSize: "0.8rem", display: "block", textAlign: "left" }}
                          >
                            {line}
                          </Badge>
                        </Tooltip>
                      ))}
                    </Stack>
                  </Box>
                )}

                {brief.concessions_to_offer.length > 0 && (
                  <Box style={{ minWidth: 0 }}>
                    <SectionLabel
                      icon={<IconGift size={14} color="var(--mantine-color-teal-6)" />}
                      label="Concessions to Offer"
                      tooltip="Things you can give the vendor in exchange for movement on red lines or key asks — multi-year commitment, faster payment, reference participation."
                    />
                    <Stack gap={6}>
                      {brief.concessions_to_offer.map((c, i) => (
                        <Tooltip key={i} label="Offer this in exchange for movement on a red line or key ask." position="top-start" withArrow>
                          <Badge
                            variant="light"
                            color="teal"
                            radius="sm"
                            size="md"
                            style={{ cursor: "help", whiteSpace: "normal", height: "auto", padding: "6px 10px", textTransform: "none", fontWeight: 500, fontSize: "0.8rem", display: "block", textAlign: "left" }}
                          >
                            {c}
                          </Badge>
                        </Tooltip>
                      ))}
                    </Stack>
                  </Box>
                )}
              </Group>

              {/* BATNA */}
              {brief.batna && (
                <Box
                  style={{
                    background: "#fffbe6",
                    border: "1px solid #f0c040",
                    borderRadius: 8,
                    padding: "10px 14px",
                  }}
                >
                  <Tooltip
                    label="Best Alternative To a Negotiated Agreement — your walk-away option. Knowing your BATNA tells you how firm to be. The stronger the alternative, the more leverage you have."
                    multiline
                    w={300}
                    withArrow
                    position="top-start"
                  >
                    <Group gap={6} mb={4} style={{ cursor: "help", display: "inline-flex" }}>
                      <IconScale size={14} color="#b8860b" />
                      <Text size="xs" tt="uppercase" fw={700} style={{ color: "#b8860b", letterSpacing: "0.07em" }}>
                        BATNA
                      </Text>
                      <IconInfoCircle size={12} color="#c8a020" />
                    </Group>
                  </Tooltip>
                  <Text size="sm" style={{ color: "#5a4a00" }}>{brief.batna}</Text>
                </Box>
              )}
            </Stack>
          </Accordion.Panel>
        </Accordion.Item>
      ))}
    </Accordion>
  );
}
