"use client";

import { Box, Group, Text } from "@mantine/core";
import { IconCircleCheck } from "@tabler/icons-react";
import type { TelemetrySummary } from "@/lib/telemetry";

interface Props {
  summary: TelemetrySummary;
}

export function TelemetryFooter({ summary }: Props) {
  const parts: string[] = [
    `${summary.vendorCount} vendor${summary.vendorCount !== 1 ? "s" : ""} analyzed`,
    `${summary.riskCount} risk flag${summary.riskCount !== 1 ? "s" : ""} surfaced`,
    ...(summary.elapsed ? [`completed in ${summary.elapsed}`] : []),
    ...(summary.llmCostUsd != null ? [`$${summary.llmCostUsd.toFixed(2)} api cost`] : []),
  ];

  return (
    <Box
      py="sm"
      style={{
        borderTop: "1px solid rgba(0,0,0,0.08)",
        textAlign: "center",
      }}
    >
      <Group gap="xs" justify="center" align="center">
        <IconCircleCheck size={13} color="var(--mantine-color-umgreen-6)" />
        <Text
          size="xs"
          c="dimmed"
          style={{ fontFamily: "monospace", letterSpacing: "0.03em" }}
        >
          {parts.join(" · ")}
        </Text>
      </Group>
    </Box>
  );
}
