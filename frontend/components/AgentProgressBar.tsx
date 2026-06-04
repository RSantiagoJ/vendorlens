"use client";

import { Paper, Group, Stack, Text, ThemeIcon, Loader, Box } from "@mantine/core";
import {
  IconSearch, IconShieldCheck, IconChartBar, IconFileText, IconCheck,
} from "@tabler/icons-react";
import type { Stage } from "@/lib/types";

const STAGES: { key: Stage; label: string; description: string; icon: React.ReactNode }[] = [
  {
    key: "extracting",
    label: "Extracting",
    description: "Reading each proposal and pulling out structured data — pricing, contract terms, SLA, certifications, and more.",
    icon: <IconSearch size={18} />,
  },
  {
    key: "risk",
    label: "Risk Analysis",
    description: "Checking contract clauses against UMPO procurement policy for compliance violations and red flags.",
    icon: <IconShieldCheck size={18} />,
  },
  {
    key: "scoring",
    label: "Scoring",
    description: "Evaluating each vendor against the LMS RFP criteria — functionality, accessibility, integrations, support, and pricing.",
    icon: <IconChartBar size={18} />,
  },
  {
    key: "memo",
    label: "Writing Memo",
    description: "Synthesizing risk flags and scores into a recommendation memo for the procurement committee.",
    icon: <IconFileText size={18} />,
  },
];

const STAGE_ORDER: Stage[] = ["extracting", "risk", "scoring", "memo", "done"];

function stageIndex(stage: Stage): number {
  return STAGE_ORDER.indexOf(stage);
}

function getStageStatus(stageKey: Stage, currentStage: Stage): "done" | "active" | "pending" {
  if (currentStage === "done") return "done";
  const current = stageIndex(currentStage);
  const mine = stageIndex(stageKey);
  if (mine < current) return "done";
  if (mine === current) return "active";
  return "pending";
}

interface Props {
  stage: Stage;
}

export function AgentProgressBar({ stage }: Props) {
  return (
    <Paper p="lg" radius="md" withBorder bg="white" w="100%" maw={640} mx="auto">
      <Text fw={600} size="sm" c="dimmed" mb="md" tt="uppercase" style={{ letterSpacing: "0.05em" }}>
        Analysis in progress
      </Text>
      <Stack gap="xs">
        {STAGES.map(({ key, label, description, icon }) => {
          const status = getStageStatus(key, stage);
          const isActive = status === "active";
          const isDone = status === "done";
          return (
            <Paper
              key={key}
              px="md"
              py="sm"
              radius="md"
              style={{
                background: isActive ? "var(--mantine-color-umblue-0)" : "transparent",
                border: isActive ? "1px solid var(--mantine-color-umblue-2)" : "1px solid transparent",
                transition: "all 150ms ease",
              }}
            >
              <Group gap="md" align="flex-start">
                <ThemeIcon
                  size={38}
                  radius="xl"
                  variant={status === "pending" ? "light" : "filled"}
                  color={isDone ? "umgreen" : isActive ? "umblue" : "gray"}
                  style={{ flexShrink: 0, marginTop: 2 }}
                >
                  {isDone ? (
                    <IconCheck size={18} />
                  ) : isActive ? (
                    <Loader size={16} color="white" type="dots" />
                  ) : (
                    icon
                  )}
                </ThemeIcon>
                <Stack gap={2} style={{ flex: 1 }}>
                  <Text
                    size="sm"
                    fw={isActive ? 700 : isDone ? 600 : 400}
                    c={isDone ? "umgreen.6" : isActive ? "umblue.8" : "dimmed"}
                  >
                    {label}
                  </Text>
                  {(isActive || isDone) && (
                    <Text size="xs" c="dimmed">
                      {description}
                    </Text>
                  )}
                </Stack>
              </Group>
            </Paper>
          );
        })}
      </Stack>
    </Paper>
  );
}
