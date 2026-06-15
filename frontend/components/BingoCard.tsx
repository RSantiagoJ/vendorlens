"use client";

import { useEffect, useState } from "react";
import { Box, Button, Stack, Text } from "@mantine/core";

const RED_FLAGS = [
  "Auto-renewal clause",
  "Unlimited storage*",
  "SOC 2 pending",
  '"Working on it"',
  "Best-effort SLA",
  "Fair use p.47",
  "Timeline TBD",
  "Unlisted subprocessors",
  "No data portability",
  "LTI 1.1 only",
  '"6-month" go-live',
  "Shared acct team",
  "99.9% uptime*",
  '"No hidden fees"',
  "No FERPA DPA",
  "REST-ish API",
  "WCAG 2.0 VPAT",
  "15% price cap",
  "1-mo liability cap",
  "120-day exit clause",
  '"Supports Banner"',
  "Q3 roadmap item",
  "Mktg attestation",
  "Training = YouTube",
];

const SIZE = 5;
const TOTAL = SIZE * SIZE;
const CENTER = Math.floor(TOTAL / 2);

const LINES: number[][] = [
  [0,1,2,3,4], [5,6,7,8,9], [10,11,12,13,14], [15,16,17,18,19], [20,21,22,23,24],
  [0,5,10,15,20], [1,6,11,16,21], [2,7,12,17,22], [3,8,13,18,23], [4,9,14,19,24],
  [0,6,12,18,24], [4,8,12,16,20],
];

function shuffle<T>(arr: T[]): T[] {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

function makeCard(): string[] {
  const s = shuffle(RED_FLAGS);
  return [...s.slice(0, CENTER), "FREE", ...s.slice(CENTER)];
}

function checkBingo(marked: Set<number>): boolean {
  return LINES.some(line => line.every(i => marked.has(i)));
}

const CELL = 42;

export function BingoCard() {
  const [card, setCard] = useState<string[]>([]);
  const [marked, setMarked] = useState<Set<number>>(new Set([CENTER]));
  const [bingo, setBingo] = useState(false);

  function newCard() {
    setCard(makeCard());
    setMarked(new Set([CENTER]));
    setBingo(false);
  }

  useEffect(() => { newCard(); }, []);

  function toggle(i: number) {
    if (i === CENTER || bingo) return;
    const next = new Set(marked);
    if (next.has(i)) next.delete(i); else next.add(i);
    setMarked(next);
    if (checkBingo(next)) setBingo(true);
  }

  return (
    <Stack gap="sm" p="md" align="center">
      <Box style={{ display: "grid", gridTemplateColumns: `repeat(5, ${CELL}px)`, gap: 3 }}>
        {card.map((label, i) => {
          const isCenter = i === CENTER;
          const isMarked = marked.has(i);
          return (
            <Box
              key={i}
              onClick={() => toggle(i)}
              style={{
                width: CELL,
                height: CELL,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                textAlign: "center",
                borderRadius: 4,
                cursor: isCenter ? "default" : "pointer",
                background: isMarked
                  ? isCenter
                    ? "rgba(45,198,83,0.25)"
                    : "rgba(100,180,255,0.22)"
                  : "rgba(255,255,255,0.05)",
                border: "1px solid",
                borderColor: isMarked
                  ? isCenter
                    ? "rgba(45,198,83,0.5)"
                    : "rgba(100,180,255,0.4)"
                  : "rgba(255,255,255,0.1)",
                transition: "background 0.12s, border-color 0.12s",
                padding: 3,
              }}
            >
              <Text
                size="9px"
                fw={isMarked ? 700 : 400}
                c={isMarked ? "white" : "gray.4"}
                style={{ lineHeight: 1.2 }}
              >
                {label}
              </Text>
            </Box>
          );
        })}
      </Box>

      <Text size="xs" c="dimmed" ta="center">
        {bingo
          ? "🎉 BINGO! They got us again."
          : "Mark every red flag you spot in the proposal"}
      </Text>

      <Button size="xs" variant={bingo ? "filled" : "subtle"} color={bingo ? "yellow" : "gray"} onClick={newCard}>
        {bingo ? "🎉 New Card" : "New card"}
      </Button>
    </Stack>
  );
}
