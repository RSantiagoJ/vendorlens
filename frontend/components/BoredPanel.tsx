"use client";

import { useState } from "react";
import { Box, Button, Group, Paper, Stack, Text } from "@mantine/core";
import {
  IconCookie,
  IconDeviceGamepad2,
  IconSparkles,
  IconX,
} from "@tabler/icons-react";
import confetti from "canvas-confetti";
import { TetrisGame } from "./TetrisGame";

const FORTUNES = [
  "A great contract awaits you — but read the auto-renewal clause first.",
  "The vendor with the highest score is not always the lowest risk.",
  "A $50,000 liability cap is a red flag dressed as a number.",
  "Clarity will come. So will the invoice.",
  "The RFP rubric you set today shapes the vendor you're stuck with tomorrow.",
  "Beware the 30-day opt-out window disguised as flexibility.",
  "Your next best decision will be backed by data, not intuition.",
  "A DPA is worth a thousand apologies.",
  "The winning vendor is not the cheapest — it is the least surprising.",
  "Governing law matters more than the vendor admits.",
  "Five AI agents cannot replace due diligence. They can, however, speed it up considerably.",
  "The auto-renewal clause is always watching.",
  "A SOC 2 Type II audit report is a love language.",
  "Not all escalation caps are created equal.",
  "The best negotiation starts before you sign.",
  "Your procurement director will thank you. Eventually.",
  "Read every exhibit. Especially Exhibit C.",
  "An SLA without teeth is just a suggestion.",
  "The vendor that rushes you to sign has something to hide.",
  "Good things come to those who benchmark.",
];

function fireBurst() {
  confetti({ particleCount: 180, spread: 80, origin: { y: 0.7 } });
}

function fireFireworks() {
  const shoot = (angle: number, x: number) =>
    confetti({ particleCount: 80, angle, spread: 55, startVelocity: 60, origin: { x, y: 0.8 } });
  shoot(60, 0);
  setTimeout(() => shoot(120, 1), 150);
  setTimeout(() => shoot(90, 0.5), 300);
}

function fireSchoolPride() {
  // UMass maroon + white + blue — 5-cannon wave
  const colors = ["#881c1c", "#ffffff", "#003087"];
  const shoot = (angle: number, x: number) =>
    confetti({ particleCount: 90, angle, spread: 55, startVelocity: 60, origin: { x, y: 0.8 }, colors });
  shoot(60, 0);
  setTimeout(() => shoot(120, 1),    150);
  setTimeout(() => shoot(75, 0.25),  300);
  setTimeout(() => shoot(105, 0.75), 450);
  setTimeout(() => shoot(90, 0.5),   600);
}

type Tab = "game" | "confetti" | "fortune";

const TABS = [
  { id: "game" as Tab,     Icon: IconDeviceGamepad2, label: "Game"     },
  { id: "confetti" as Tab, Icon: IconSparkles,        label: "Confetti" },
  { id: "fortune" as Tab,  Icon: IconCookie,          label: "Fortune"  },
];

const PANEL_WIDTH = 260;

export function BoredPanel() {
  const [open, setOpen] = useState(false);
  const [tab, setTab] = useState<Tab>("game");
  const [fortune, setFortune] = useState<string>(
    () => FORTUNES[Math.floor(Math.random() * FORTUNES.length)]
  );

  function handleTab(t: Tab) {
    setTab(t);
  }

  function pickFortune() {
    setFortune(FORTUNES[Math.floor(Math.random() * FORTUNES.length)]);
  }

  return (
    <Box style={{ position: "fixed", bottom: 24, right: 24, zIndex: 200 }}>
      {open && (
        <Paper
          radius="lg"
          shadow="xl"
          style={{
            position: "absolute",
            bottom: 52,
            right: 0,
            width: PANEL_WIDTH,
            background: "#0f0f1a",
            border: "1px solid rgba(255,255,255,0.09)",
            overflow: "hidden",
          }}
        >
          {/* Header */}
          <Group
            px="md"
            py={10}
            justify="space-between"
            style={{ borderBottom: "1px solid rgba(255,255,255,0.07)" }}
          >
            <Text size="xs" fw={600} tt="uppercase" style={{ letterSpacing: "0.05em", color: "rgba(255,255,255,0.7)" }}>
              While you wait
            </Text>
            <Box
              onClick={() => setOpen(false)}
              style={{ cursor: "pointer", color: "rgba(255,255,255,0.6)", lineHeight: 1 }}
            >
              <IconX size={14} />
            </Box>
          </Group>

          {/* Tabs */}
          <Group gap={0} style={{ borderBottom: "1px solid rgba(255,255,255,0.07)" }}>
            {TABS.map(({ id, Icon, label }) => (
              <Box
                key={id}
                onClick={() => handleTab(id)}
                style={{
                  flex: 1,
                  padding: "8px 4px",
                  textAlign: "center",
                  cursor: "pointer",
                  background: tab === id ? "rgba(255,255,255,0.06)" : "transparent",
                  borderBottom: tab === id
                    ? "2px solid var(--mantine-color-blue-4)"
                    : "2px solid transparent",
                  transition: "background 0.15s",
                }}
              >
                <Stack gap={3} align="center">
                  <Icon
                    size={16}
                    color={tab === id ? "var(--mantine-color-blue-4)" : "rgba(255,255,255,0.65)"}
                  />
                  <Text
                    size="xs"
                    fw={tab === id ? 600 : 400}
                    style={{ color: tab === id ? "var(--mantine-color-blue-4)" : "rgba(255,255,255,0.65)" }}
                  >
                    {label}
                  </Text>
                </Stack>
              </Box>
            ))}
          </Group>

          {/* Content */}
          {tab === "game" && <TetrisGame />}

          {tab === "confetti" && (
            <Stack gap="sm" p="md" align="center">
              <Text size="xs" ta="center" style={{ color: "rgba(255,255,255,0.65)" }}>
                No one will know.
              </Text>
              <Button
                fullWidth
                size="sm"
                variant="light"
                color="blue"
                onClick={fireBurst}
              >
                🎉 Burst
              </Button>
              <Button
                fullWidth
                size="sm"
                variant="light"
                color="orange"
                onClick={fireFireworks}
              >
                🎆 Fireworks
              </Button>
              <Button
                fullWidth
                size="sm"
                variant="light"
                color="red"
                onClick={fireSchoolPride}
              >
                🎓 School Pride
              </Button>
            </Stack>
          )}

          {tab === "fortune" && (
            <Stack gap="md" p="md" align="center">
              <Paper
                p="sm"
                radius="md"
                style={{
                  background: "rgba(255,255,255,0.06)",
                  border: "1px solid rgba(255,255,255,0.1)",
                  width: "100%",
                }}
              >
                <Text
                  size="sm"
                  c="white"
                  ta="center"
                  style={{ lineHeight: 1.55, fontStyle: "italic" }}
                >
                  &ldquo;{fortune}&rdquo;
                </Text>
              </Paper>
              <Button
                fullWidth
                size="xs"
                variant="light"
                color="blue"
                onClick={pickFortune}
              >
                Another one
              </Button>
            </Stack>
          )}
        </Paper>
      )}

      {/* Trigger */}
      <Button
        size="sm"
        radius="xl"
        variant={open ? "subtle" : "filled"}
        color={open ? "gray" : "blue"}
        onClick={() => setOpen((o) => !o)}
        style={{
          boxShadow: open ? "none" : "0 4px 16px rgba(0,0,0,0.3)",
          transition: "box-shadow 0.2s",
        }}
      >
        {open ? "✕ Close" : "🎮 Bored?"}
      </Button>
    </Box>
  );
}
