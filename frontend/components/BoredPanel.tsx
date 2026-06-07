"use client";

import { useEffect, useState } from "react";
import { Box, Button, Group, Paper, Stack, Text, Transition } from "@mantine/core";
import { useReducedMotion } from "@mantine/hooks";
import {
  IconBulb,
  IconDeviceGamepad2,
  IconFlame,
  IconX,
} from "@tabler/icons-react";
import { TetrisGame } from "./TetrisGame";

const ROASTS = [
  "SynergyCloud promised 99.9% uptime. Their SLA defines 'uptime' as 'the server is physically plugged in.'",
  "DocuPrime's support SLA is 48 hours. The clock starts when they feel like responding.",
  "InnovateTech's 'AI-powered analytics' is a pivot table in a trench coat.",
  "QuadrantPlus has not passed a SOC 2 audit. It has, however, attended a SOC 2 webinar.",
  "VendorSoft 9.0 ships with 300 pages of documentation last updated for VendorSoft 4.2.",
  "HelixEDU's pricing model has six tiers. None include the features you actually need.",
  "MegaCorp Solutions buried the auto-renewal clause in Exhibit F, subsection 7, paragraph 3(b)(ii).",
  "EduCloud Pro stores your data in 'the cloud.' They cannot tell you which one.",
  "NexGen Platform's API is 'RESTful in spirit.'",
  "OmniLearn's 'unlimited users' plan has a fair use policy that limits users.",
  "ProcureMax calls their liability cap 'industry standard.' The industry would like a word.",
  "FlexiVend's 'enterprise-grade security' is a login page with HTTPS. That's it.",
  "TotalSoft's implementation timeline is '6–8 weeks.' Week 16 update: 'almost there.'",
  "EduPrime's FERPA compliance documentation is a PDF from 2018 that says 'FERPA compliant.'",
  "CoreSystems offers a 30-day money-back guarantee. Step 1: find the opt-out form.",
];

const FACTS = [
  "The average enterprise RFP process takes 3–6 months from release to contract signature.",
  "42% of data breaches in 2023 originated from a third-party vendor or supplier.",
  "Only 12% of enterprise vendor contracts are actively monitored after signature.",
  "Auto-renewal clauses account for an estimated 23% of unplanned SaaS spend.",
  "The average cost of a third-party data breach reached $4.29M in 2023.",
  "68% of organizations experienced a third-party security incident in the past three years.",
  "Fortune 500 companies manage an average of 10,000+ active vendor relationships.",
  "Procurement teams using structured scoring rubrics close vendor selections 40% faster.",
  "Only 34% of procurement teams have full visibility into their supplier risk exposure.",
  "The average enterprise wastes $135K/year on unused or duplicate SaaS licenses.",
  "Contracts with explicit data portability clauses reduce migration costs by up to 60%.",
  "Liability caps below $1M appear in 44% of mid-market software contracts.",
  "A poorly scoped SLA can cost 2–5× more in remediation than the original contract value.",
  "The average time from contract signature to first support escalation: 47 days.",
  "Vendor lock-in affects an estimated 80% of enterprise cloud contracts after year two.",
];

type Tab = "game" | "roast" | "facts";

const TABS = [
  { id: "game" as Tab,  Icon: IconDeviceGamepad2, label: "Game"  },
  { id: "roast" as Tab, Icon: IconFlame,           label: "Roast" },
  { id: "facts" as Tab, Icon: IconBulb,            label: "Stats" },
];

const PANEL_WIDTH = 260;

const tabHeights = {
  game: 511,
  roast: 200,
  facts: 180,
};

export function BoredPanel() {
  const [open, setOpen] = useState(false);
  const [tab, setTab] = useState<Tab>("game");
  const [visibleTab, setVisibleTab] = useState<Tab>("game");
  const [mounted, setMounted] = useState(true);
  const [roastIdx, setRoastIdx] = useState(0);
  const [factIdx, setFactIdx] = useState(0);

  // Randomize client-side only to avoid SSR hydration mismatch
  useEffect(() => {
    setRoastIdx(Math.floor(Math.random() * ROASTS.length));
    setFactIdx(Math.floor(Math.random() * FACTS.length));
  }, []);

  const reduceMotion = useReducedMotion();
  const duration = reduceMotion ? 0 : 150;

  function handleTab(t: Tab) {
    if (t === tab) return;
    setTab(t);
    setMounted(false);
  }

  function pickRoast() {
    setRoastIdx((i) => (i + 1) % ROASTS.length);
  }

  function pickFact() {
    setFactIdx((i) => (i + 1) % FACTS.length);
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
              style={{ cursor: "pointer", color: "rgba(255,255,255,0.5)", lineHeight: 1 }}
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
                  borderBottom: "2px solid",
                  borderColor: tab === id ? "var(--mantine-color-blue-4)" : "transparent",
                  transition: reduceMotion ? "none" : "background 0.15s, border-color 0.15s",
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
          <Box
            style={{
              minHeight: tabHeights[visibleTab],
              transition: reduceMotion ? "none" : "min-height 0.2s ease-in-out",
              overflow: "hidden",
            }}
          >
            <Transition
              mounted={mounted}
              transition="fade"
              duration={duration}
              onExited={() => {
                setVisibleTab(tab);
                setMounted(true);
              }}
            >
              {(styles) => (
                <Box style={styles}>
                  {visibleTab === "game" && <TetrisGame />}

                  {visibleTab === "roast" && (
                    <Stack gap="md" p="md" align="center">
                      <Paper
                        p="sm"
                        radius="md"
                        style={{
                          background: "rgba(255,80,30,0.08)",
                          border: "1px solid rgba(255,80,30,0.22)",
                          width: "100%",
                        }}
                      >
                        <Text
                          size="sm"
                          c="white"
                          ta="center"
                          style={{ lineHeight: 1.55 }}
                        >
                          {ROASTS[roastIdx]}
                        </Text>
                      </Paper>
                      <Button
                        fullWidth
                        size="xs"
                        variant="light"
                        color="orange"
                        onClick={pickRoast}
                      >
                        🔥 Roast another
                      </Button>
                    </Stack>
                  )}

                  {visibleTab === "facts" && (
                    <Stack gap="md" p="md" align="center">
                      <Paper
                        p="sm"
                        radius="md"
                        style={{
                          background: "rgba(100,180,255,0.07)",
                          border: "1px solid rgba(100,180,255,0.18)",
                          width: "100%",
                        }}
                      >
                        <Text
                          size="sm"
                          c="white"
                          ta="center"
                          style={{ lineHeight: 1.55 }}
                        >
                          {FACTS[factIdx]}
                        </Text>
                      </Paper>
                      <Button
                        fullWidth
                        size="xs"
                        variant="light"
                        color="blue"
                        onClick={pickFact}
                      >
                        💡 Next stat
                      </Button>
                    </Stack>
                  )}
                </Box>
              )}
            </Transition>
          </Box>
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
          🎮 Bored?
      </Button>
    </Box>
  );
}
