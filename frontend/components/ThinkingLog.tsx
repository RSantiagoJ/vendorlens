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
    "Calling Gemini Flash to extract structured fields...",
    "Parsing JSON response into ProposalData model",
  ],
  risk: [
    "Loading institutional procurement policy...",
    "Checking security certification requirements (SOC 2 Type II, ISO 27001)",
    "Checking renewal and auto-renewal clauses",
    "Checking data ownership and AI training provisions",
    "Checking governing law and jurisdiction",
    "Checking liability cap against policy minimums",
    "Calling Gemini Flash to classify risk severity (HIGH / MEDIUM / LOW)...",
  ],
  scoring: [
    "Loading RFP criteria and scoring rubric...",
    "Evaluating platform functionality (weight: 25%)",
    "Evaluating accessibility and WCAG compliance (15%)",
    "Evaluating integration capability (15%)",
    "Evaluating security and compliance (15%)",
    "Evaluating pricing transparency and support (10% each)",
    "Evaluating innovation and AI product roadmap (5%)",
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

const STAGE_SUMMARY: Record<ActiveStage, string> = {
  extracting: `${STAGE_LINES.extracting.length} operations`,
  risk: `${STAGE_LINES.risk.length} checks`,
  scoring: `${STAGE_LINES.scoring.length} criteria`,
  memo: `${STAGE_LINES.memo.length} sections`,
};

const COMPLETION_LABELS: Record<ActiveStage, string> = {
  extracting: "Extraction complete",
  risk: "Risk analysis complete",
  scoring: "Scoring complete",
  memo: "Memo complete",
};

const TYPEWRITER_INTERVAL_MS = 25;
const TYPEWRITER_CHARS_PER_TICK = 4;

const ACTIVE_STAGE_SET = new Set<Stage>(["extracting", "risk", "scoring", "memo"]);

function isActiveStage(s: Stage): s is ActiveStage {
  return ACTIVE_STAGE_SET.has(s);
}

interface Entry {
  text: string;
  stage: ActiveStage | "done";
  completion?: boolean;
  typed?: number; // chars revealed so far; undefined = fully shown
}

interface Props {
  stage: Stage;
}

export function ThinkingLog({ stage }: Props) {
  const [entries, setEntries] = useState<Entry[]>([]);
  const viewportRef = useRef<HTMLDivElement>(null);
  const lineTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const typewriterRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const indexRef = useRef(0);
  const prevStageRef = useRef<ActiveStage | null>(null);
  const stageStartRef = useRef<Partial<Record<ActiveStage, number>>>({});

  useEffect(() => {
    if (lineTimerRef.current) clearTimeout(lineTimerRef.current);
    if (typewriterRef.current) clearInterval(typewriterRef.current);

    // When a stage completes, add a rich completion marker with timing
    if (prevStageRef.current && prevStageRef.current !== stage) {
      const completedStage = prevStageRef.current;
      const startTime = stageStartRef.current[completedStage];
      const elapsed = startTime ? Math.round((Date.now() - startTime) / 1000) : null;
      const timePart = elapsed != null ? ` · ${elapsed}s` : "";
      setEntries((prev) => [
        ...prev,
        {
          text: `${COMPLETION_LABELS[completedStage]} — ${STAGE_SUMMARY[completedStage]}${timePart}`,
          stage: completedStage,
          completion: true,
        },
      ]);
    }

    if (!isActiveStage(stage)) {
      prevStageRef.current = null;
      return;
    }

    prevStageRef.current = stage;
    stageStartRef.current[stage] = Date.now();
    indexRef.current = 0;
    const lines = STAGE_LINES[stage];
    const capturedStage = stage;

    function revealLastEntry(text: string, onDone: () => void) {
      let typed = 0;
      if (typewriterRef.current) clearInterval(typewriterRef.current);
      typewriterRef.current = setInterval(() => {
        typed = Math.min(typed + TYPEWRITER_CHARS_PER_TICK, text.length);
        setEntries((prev) => {
          const next = [...prev];
          const last = next[next.length - 1];
          if (last) next[next.length - 1] = { ...last, typed };
          return next;
        });
        if (typed >= text.length) {
          clearInterval(typewriterRef.current!);
          // Mark as fully revealed
          setEntries((prev) => {
            const next = [...prev];
            const last = next[next.length - 1];
            if (last) next[next.length - 1] = { ...last, typed: undefined };
            return next;
          });
          onDone();
        }
      }, TYPEWRITER_INTERVAL_MS);
    }

    function addNextLine() {
      if (indexRef.current >= lines.length) return;
      const delay = Math.floor(Math.random() * 900) + 600; // 600–1500ms
      lineTimerRef.current = setTimeout(() => {
        const text = lines[indexRef.current++];
        setEntries((prev) => [...prev, { text, stage: capturedStage, typed: 0 }]);
        revealLastEntry(text, addNextLine);
      }, delay);
    }

    // First line immediately
    const firstText = lines[indexRef.current++];
    setEntries((prev) => [...prev, { text: firstText, stage: capturedStage, typed: 0 }]);
    revealLastEntry(firstText, addNextLine);

    return () => {
      if (lineTimerRef.current) clearTimeout(lineTimerRef.current);
      if (typewriterRef.current) clearInterval(typewriterRef.current);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stage]);

  // Auto-scroll to bottom on new entries
  useEffect(() => {
    viewportRef.current?.scrollTo({
      top: viewportRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [entries]);

  const allCompletionLines: Entry[] =
    stage === "done" && entries.length === 0
      ? (["extracting", "risk", "scoring", "memo"] as ActiveStage[]).map((s) => ({
          text: `${COMPLETION_LABELS[s]} — ${STAGE_SUMMARY[s]}`,
          stage: s,
          completion: true,
        }))
      : [];

  const displayEntries = entries.length > 0 ? entries : allCompletionLines;
  if (displayEntries.length === 0) return null;

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

      <ScrollArea h={240} viewportRef={viewportRef} scrollbarSize={4}>
        <Stack gap={3} pr="xs">
          {displayEntries.map((entry, i) => {
            const isLast = i === displayEntries.length - 1;
            const isDimmed = !isLast && !entry.completion;
            const isTyping = entry.typed !== undefined;
            const displayText = isTyping ? entry.text.slice(0, entry.typed) : entry.text;

            return (
              <Text
                key={i}
                size="xs"
                className={entry.completion ? "fadeIn" : undefined}
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
                <span
                  style={{
                    flexShrink: 0,
                    color: entry.completion
                      ? "var(--mantine-color-umgreen-5)"
                      : "var(--mantine-color-umblue-4)",
                  }}
                >
                  {entry.completion ? "✓" : "›"}
                </span>
                <span>
                  {displayText}
                  {(isTyping || (isLast && isActiveStage(stage))) && (
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
