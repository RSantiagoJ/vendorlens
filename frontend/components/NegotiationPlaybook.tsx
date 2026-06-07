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
  IconScale,
  IconTarget,
} from "@tabler/icons-react";

interface Props {
  plans: NegotiationBrief[];
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
              {/* Overall approach */}
              <Box
                style={{
                  background: "linear-gradient(90deg, #0d1a2e 0%, #1c0810 100%)",
                  borderRadius: 8,
                  padding: "12px 16px",
                  borderLeft: "3px solid var(--mantine-color-umblue-5)",
                }}
              >
                <Text size="xs" tt="uppercase" fw={700} c="umblue.3" style={{ letterSpacing: "0.07em" }}>
                  Opening Posture
                </Text>
                <Text mt={4} style={{ color: "rgba(255,255,255,0.88)", fontSize: "0.95rem", lineHeight: 1.55 }}>
                  {brief.overall_approach}
                </Text>
              </Box>

              {/* Priority tactics table */}
              {brief.priority_tactics.length > 0 && (
                <Box>
                  <Group gap={6} mb={10}>
                    <IconTarget size={14} color="var(--mantine-color-umblue-6)" />
                    <Text size="xs" tt="uppercase" fw={700} c="dimmed" style={{ letterSpacing: "0.07em" }}>
                      Priority Tactics
                    </Text>
                  </Group>
                  <Box style={{ borderRadius: 8, overflow: "hidden", border: "1px solid var(--mantine-color-gray-3)" }}>
                    <Table striped highlightOnHover withColumnBorders={false}>
                      <Table.Thead style={{ background: "#f8f9fa" }}>
                        <Table.Tr>
                          <Table.Th style={{ width: "18%", fontSize: "0.75rem", color: "#666", fontWeight: 700 }}>AREA</Table.Th>
                          <Table.Th style={{ width: "27%", fontSize: "0.75rem", color: "#666", fontWeight: 700 }}>THEIR POSITION</Table.Th>
                          <Table.Th style={{ width: "27%", fontSize: "0.75rem", color: "#666", fontWeight: 700 }}>OUR ASK</Table.Th>
                          <Table.Th style={{ width: "28%", fontSize: "0.75rem", color: "#666", fontWeight: 700 }}>LEVERAGE</Table.Th>
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

              {/* Red lines + concessions side by side */}
              <Group gap="md" align="flex-start" grow>
                {brief.red_lines.length > 0 && (
                  <Box>
                    <Group gap={6} mb={8}>
                      <IconAlertTriangle size={14} color="var(--mantine-color-red-6)" />
                      <Text size="xs" tt="uppercase" fw={700} c="dimmed" style={{ letterSpacing: "0.07em" }}>
                        Red Lines
                      </Text>
                    </Group>
                    <Stack gap={6}>
                      {brief.red_lines.map((line, i) => (
                        <Tooltip key={i} label="Walk away if unmet" position="top-start" withArrow>
                          <Badge
                            variant="light"
                            color="red"
                            radius="sm"
                            size="md"
                            style={{ cursor: "default", whiteSpace: "normal", height: "auto", padding: "6px 10px", textTransform: "none", fontWeight: 500, fontSize: "0.8rem", display: "block", textAlign: "left" }}
                          >
                            {line}
                          </Badge>
                        </Tooltip>
                      ))}
                    </Stack>
                  </Box>
                )}

                {brief.concessions_to_offer.length > 0 && (
                  <Box>
                    <Group gap={6} mb={8}>
                      <IconGift size={14} color="var(--mantine-color-teal-6)" />
                      <Text size="xs" tt="uppercase" fw={700} c="dimmed" style={{ letterSpacing: "0.07em" }}>
                        Concessions to Offer
                      </Text>
                    </Group>
                    <Stack gap={6}>
                      {brief.concessions_to_offer.map((c, i) => (
                        <Badge
                          key={i}
                          variant="light"
                          color="teal"
                          radius="sm"
                          size="md"
                          style={{ cursor: "default", whiteSpace: "normal", height: "auto", padding: "6px 10px", textTransform: "none", fontWeight: 500, fontSize: "0.8rem", display: "block", textAlign: "left" }}
                        >
                          {c}
                        </Badge>
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
                  <Group gap={6} mb={4}>
                    <IconScale size={14} color="#b8860b" />
                    <Text size="xs" tt="uppercase" fw={700} style={{ color: "#b8860b", letterSpacing: "0.07em" }}>
                      BATNA
                    </Text>
                  </Group>
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
