"use client";

import { useState } from "react";
import { Box, Button, Group, Paper, Stack, Text, Transition, Tooltip } from "@mantine/core";
import { useReducedMotion } from "@mantine/hooks";
import {
  IconBulb,
  IconCheck,
  IconClipboard,
  IconDeviceGamepad2,
  IconFlame,
  IconX,
} from "@tabler/icons-react";
import { TetrisGame } from "./TetrisGame";
import { pickRandom } from "@/lib/bored";

const ROASTS = [
  "Their FERPA compliance documentation is a one-page attestation signed by someone in marketing.",
  "The implementation timeline says 12–16 weeks. The go-live date in their proposal is 8 weeks from now.",
  "Their LTI integration is 'fully supported.' LTI 1.1. They're working on 1.3.",
  "'Unlimited storage' appears in the contract. Fair use policy on page 47 limits it to 2TB per institution.",
  "Their SOC 2 Type II report covers their data centers. Their subprocessors are a separate conversation.",
  "The ERP vendor's 'dedicated higher education team' is one account manager shared across 40 institutions.",
  "Their SIS migration tool 'supports Banner data.' What it does with Banner data is another matter.",
  "99.9% uptime SLA measured annually. That's 8.7 hours of downtime — all during finals week.",
  "The vendor's API is 'RESTful in spirit.'",
  "Their accessibility VPAT is WCAG 2.0 AA. Your RFP requires 2.1. They're 'working on it.'",
  "The ERP has been in continuous development since 2002. The 2002 code is still there.",
  "'No hidden fees' is in the executive summary. Exhibit C lists $85K in professional services.",
  "Their SOC 2 Type II is pending renewal. It has been pending renewal for 11 months.",
  "The ERP implementation is '6 months.' Month 9 update: 'entering final configuration phase.'",
  "Their data ownership clause says 'institution retains rights to content.' Derived analytics: not mentioned.",
  "The disaster recovery SLA promises a 4-hour RTO. The backup policy runs quarterly.",
];

const FACTS = [
  "Universities spend an average of 6–9 months on major ERP or SIS procurement cycles.",
  "FERPA violations can result in the loss of federal funding — directly impacting Title IV aid for enrolled students.",
  "A failed ERP implementation at a mid-size university typically costs $15–50M in remediation.",
  "Less than 25% of university vendor contracts include an explicit FERPA data processing addendum.",
  "The average university runs 900+ distinct software applications across campus.",
  "60% of higher ed ERP migrations exceed their initial timeline by more than 6 months.",
  "Auto-renewal clauses without adequate notice periods appear in 38% of higher ed SaaS contracts.",
  "Only 31% of higher ed procurement teams conduct structured post-contract vendor performance reviews.",
  "87% of higher ed IT leaders cite vendor lock-in as a top 3 infrastructure concern.",
  "The average university pays 22% more for software licenses than peer institutions due to decentralized purchasing.",
  "ERP contracts without clear data portability clauses cost 2–3× more in migration when the vendor is replaced.",
  "A liability cap below the annual contract value appears in 44% of mid-market software contracts.",
  "Consortium purchasing through organizations like Internet2 reduces software costs by an average of 31%.",
  "Only 12% of university vendor contracts are actively monitored for SLA compliance after signature.",
  "The average time from ERP contract signature to first major support escalation: 63 days.",
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
  roast: 230,
  facts: 210,
};

export function BoredPanel() {
  const [open, setOpen] = useState(false);
  const [tab, setTab] = useState<Tab>("game");
  const [visibleTab, setVisibleTab] = useState<Tab>("game");
  const [mounted, setMounted] = useState(true);
  const [roastIdx, setRoastIdx] = useState(() => Math.floor(Math.random() * ROASTS.length));
  const [factIdx, setFactIdx] = useState(() => Math.floor(Math.random() * FACTS.length));
  const [copied, setCopied] = useState(false);

  const reduceMotion = useReducedMotion();
  const duration = reduceMotion ? 0 : 150;

  function handleTab(t: Tab) {
    if (t === tab) return;
    setTab(t);
    setMounted(false);
  }

  function pickRoast() {
    setRoastIdx((i) => pickRandom(ROASTS.length, i));
  }

  function pickFact() {
    setFactIdx((i) => pickRandom(FACTS.length, i));
  }

  function copyText(text: string) {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    });
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
                      <Text size="xs" style={{ color: "rgba(255,255,255,0.35)" }}>
                        {roastIdx + 1} / {ROASTS.length}
                      </Text>
                      <Group gap="xs" w="100%">
                        <Button
                          style={{ flex: 1 }}
                          size="xs"
                          variant="light"
                          color="orange"
                          onClick={pickRoast}
                        >
                          🔥 Another
                        </Button>
                        <Tooltip label={copied ? "Copied!" : "Copy to clipboard"} withArrow>
                          <Button
                            size="xs"
                            variant="subtle"
                            color="gray"
                            px="xs"
                            onClick={() => copyText(ROASTS[roastIdx])}
                          >
                            {copied ? <IconCheck size={14} color="var(--mantine-color-green-5)" /> : <IconClipboard size={14} />}
                          </Button>
                        </Tooltip>
                      </Group>
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
                      <Text size="xs" style={{ color: "rgba(255,255,255,0.35)" }}>
                        {factIdx + 1} / {FACTS.length}
                      </Text>
                      <Group gap="xs" w="100%">
                        <Button
                          style={{ flex: 1 }}
                          size="xs"
                          variant="light"
                          color="blue"
                          onClick={pickFact}
                        >
                          💡 Next stat
                        </Button>
                        <Tooltip label={copied ? "Copied!" : "Copy to clipboard"} withArrow>
                          <Button
                            size="xs"
                            variant="subtle"
                            color="gray"
                            px="xs"
                            onClick={() => copyText(FACTS[factIdx])}
                          >
                            {copied ? <IconCheck size={14} color="var(--mantine-color-green-5)" /> : <IconClipboard size={14} />}
                          </Button>
                        </Tooltip>
                      </Group>
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
