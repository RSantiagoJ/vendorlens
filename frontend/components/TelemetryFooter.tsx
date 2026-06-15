"use client";

import { Box, Group, Text, Tooltip } from "@mantine/core";
import { IconCircleCheck } from "@tabler/icons-react";
import type { TelemetrySummary } from "@/lib/telemetry";

interface Props {
  summary: TelemetrySummary;
}

const DOT = <Text span size="xs" c="dimmed" style={{ fontFamily: "monospace" }}> · </Text>;

export function TelemetryFooter({ summary }: Props) {
  const textStyle = { fontFamily: "monospace", letterSpacing: "0.03em" } as const;

  return (
    <Box
      py="sm"
      style={{
        borderTop: "1px solid rgba(0,0,0,0.08)",
        textAlign: "center",
      }}
    >
      <Group gap={0} justify="center" align="center" wrap="wrap">
        <IconCircleCheck size={13} color="var(--mantine-color-umgreen-6)" style={{ marginRight: 6 }} />
        <Text size="xs" c="dimmed" style={textStyle}>
          {summary.vendorCount} vendor{summary.vendorCount !== 1 ? "s" : ""} analyzed
        </Text>
        {DOT}
        <Tooltip label="Total contract risk flags surfaced across all vendor proposals — HIGH, MEDIUM, and LOW combined." multiline w={220} withArrow>
          <Text size="xs" c="dimmed" style={{ ...textStyle, cursor: "help", textDecoration: "underline dotted" }}>
            {summary.riskCount} risk flag{summary.riskCount !== 1 ? "s" : ""} surfaced
          </Text>
        </Tooltip>
        {summary.elapsed && <>{DOT}<Text size="xs" c="dimmed" style={textStyle}>completed in {summary.elapsed}</Text></>}
        {summary.llmCostUsd != null && (
          <>
            {DOT}
            <Tooltip label="Total Claude API cost for this analysis run — extraction, risk analysis, scoring, memo, and negotiation briefs combined." multiline w={240} withArrow>
              <Text size="xs" c="dimmed" style={{ ...textStyle, cursor: "help", textDecoration: "underline dotted" }}>
                ${summary.llmCostUsd.toFixed(2)} api cost
              </Text>
            </Tooltip>
          </>
        )}
      </Group>
    </Box>
  );
}
