"use client";

import { useEffect, useRef, useState } from "react";
import { Paper, Text, ScrollArea, Group, ThemeIcon, Stack } from "@mantine/core";
import { IconTerminal2 } from "@tabler/icons-react";
import type { Stage } from "@/lib/types";

type ActiveStage = "extracting" | "risk" | "scoring" | "memo";

const STAGE_LINES: Record<ActiveStage, string[]> = {
  extracting: [
    "Initializing ChromaDB vector index...",
    "Running semantic search → pricing, fees, contract length",
    "Running semantic search → security certifications, DPA",
    "Running semantic search → features, SLA, integrations",
    "Deduplicating retrieved context chunks",
    "Calling Claude Sonnet to extract structured fields...",
    "Parsing JSON response into ProposalData model",
  ],
  risk: [
    "Loading UMPO procurement policy (SVM-01)...",
    "Checking security certification requirements (SOC 2 Type II, ISO 27001)",
    "Checking renewal and auto-renewal clauses",
    "Checking data ownership and AI training provisions",
    "Checking governing law and jurisdiction",
    "Checking liability cap against policy minimums",
    "Calling Claude Sonnet to classify risk severity (HIGH / MEDIUM / LOW)...",
  ],
  scoring: [
    "Loading LMS RFP criteria and scoring rubric...",
    "Evaluating platform functionality (weight: 25%)",
    "Evaluating accessibility and WCAG compliance (15%)",
    "Evaluating integration capability (15%)",
    "Evaluating security and compliance (15%)",
    "Evaluating pricing transparency and support (10% each)",
    "Calling Gemini Flash to score each dimension (0–10)...",
    "Computing weighted overall scores",
  ],
  memo: [
    "Collecting all vendor scores and risk flags...",
    "Ranking vendors by overall score",
    "Drafting executive summary",
    "Building vendor comparison table",
    "Writing risk findings section",
    "Calling Claude Sonnet to write recommendation memo...",
    "Formatting final output in Markdown",
  ],
};

const COMPLETION_LINES: Record<ActiveStage, string> = {
  extracting: "Extraction complete — structured data ready for all vendors",
  risk: "Risk analysis complete — flags classified and prioritized",
  scoring: "Scoring complete — weighted scores computed",
  memo: "Memo complete — recommendation ready",
};

const INTERVAL_MS = 2000;

interface Entry {
  text: string;
  stage: ActiveStage | "done";
  completion?: boolean;
}

function isActiveStage(s: Stage): s is ActiveStage {
  return s === "extracting" || s === "risk" || s === "scoring" || s === "memo";
}

interface Props {
  stage: Stage;
}

export function ThinkingLog({ stage }: Props) {
  const [entries, setEntries] = useState<Entry[]>([]);
  const viewportRef = useRef<HTMLDivElement>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const indexRef = useRef(0);
  const prevStageRef = useRef<ActiveStage | null>(null);

  useEffect(() => {
    if (timerRef.current) clearInterval(timerRef.current);

    // When a stage completes, add a completion marker
    if (prevStageRef.current && prevStageRef.current !== stage) {
      const completedStage = prevStageRef.current;
      setEntries((prev) => [
        ...prev,
        { text: COMPLETION_LINES[completedStage], stage: completedStage, completion: true },
      ]);
    }

    if (!isActiveStage(stage)) {
      prevStageRef.current = null;
      return;
    }

    prevStageRef.current = stage;
    indexRef.current = 0;
    const lines = STAGE_LINES[stage];

    // First line immediately
    setEntries((prev) => [...prev, { text: lines[0], stage }]);
    indexRef.current = 1;

    timerRef.current = setInterval(() => {
      if (indexRef.current >= lines.length) {
        clearInterval(timerRef.current!);
        return;
      }
      const line = lines[indexRef.current];
      setEntries((prev) => [...prev, { text: line, stage }]);
      indexRef.current++;
    }, INTERVAL_MS);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [stage]);

  // Auto-scroll to bottom on new entries
  useEffect(() => {
    viewportRef.current?.scrollTo({
      top: viewportRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [entries]);

  if (entries.length === 0) return null;

  const lastIndex = entries.length - 1;

  return (
    <Paper p="md" radius="md" withBorder bg="white" w="100%" maw={640} mx="auto" className="fadeIn">
      <Group gap="sm" mb="sm">
        <ThemeIcon size={24} variant="light" color="umblue" radius="sm">
          <IconTerminal2 size={14} />
        </ThemeIcon>
        <Text size="xs" fw={600} c="dimmed" tt="uppercase" style={{ letterSpacing: "0.05em" }}>
          Live activity
        </Text>
      </Group>

      <ScrollArea h={180} viewportRef={viewportRef} scrollbarSize={4}>
        <Stack gap={3} pr="xs">
          {entries.map((entry, i) => {
            const isLast = i === lastIndex;
            const isDimmed = !isLast && !entry.completion;

            return (
              <Text
                key={i}
                size="xs"
                className="fadeIn"
                style={{
                  fontFamily: "'Courier New', 'Menlo', monospace",
                  lineHeight: 1.7,
                  color: entry.completion
                    ? "var(--mantine-color-umgreen-6)"
                    : isDimmed
                    ? "var(--mantine-color-gray-5)"
                    : "var(--mantine-color-dark-6)",
                  display: "flex",
                  alignItems: "baseline",
                  gap: 8,
                }}
              >
                <span style={{ flexShrink: 0, color: entry.completion ? "var(--mantine-color-umgreen-5)" : "var(--mantine-color-umblue-4)" }}>
                  {entry.completion ? "✓" : "›"}
                </span>
                <span>
                  {entry.text}
                  {isLast && isActiveStage(stage) && (
                    <span
                      style={{
                        display: "inline-block",
                        width: 7,
                        height: "0.85em",
                        background: "var(--mantine-color-umblue-5)",
                        marginLeft: 3,
                        verticalAlign: "middle",
                        animation: "blink 1s step-end infinite",
                      }}
                    />
                  )}
                </span>
              </Text>
            );
          })}
        </Stack>
      </ScrollArea>
    </Paper>
  );
}
