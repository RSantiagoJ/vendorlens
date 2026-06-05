"use client";

import { AgentProgressBar } from "@/components/AgentProgressBar";
import { MemoPanel } from "@/components/MemoPanel";
import { ProposalCard } from "@/components/ProposalCard";
import { BoredPanel } from "@/components/BoredPanel";
import { ThinkingLog } from "@/components/ThinkingLog";
import { UploadZone } from "@/components/UploadZone";
import { VendorComparisonTable } from "@/components/VendorComparisonTable";
import { VendorRadarChart } from "@/components/VendorRadarChart";
import { WinnerHero } from "@/components/WinnerHero";
import { DEMO_RESULT } from "@/lib/fixtures";
import type { AnalysisResult, Bundle, Stage } from "@/lib/types";
import { Logo } from "@/logo";
import {
  Alert,
  AppShell,
  Badge,
  Box,
  Button,
  Container,
  Group,
  Paper,
  SimpleGrid,
  Stack,
  Text,
  ThemeIcon,
  Transition,
} from "@mantine/core";
import {
  IconAlertCircle, IconCircleCheck, IconRefresh,
  IconSearch, IconShieldCheck, IconChartBar, IconFileText, IconArrowRight,
  IconAward, IconAlertTriangle, IconBuilding,
} from "@tabler/icons-react";
import confetti from "canvas-confetti";
import { useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const PIPELINE_STEPS = [
  { label: "Extract",      Icon: IconSearch      },
  { label: "Risk Analysis",Icon: IconShieldCheck  },
  { label: "Scoring",      Icon: IconChartBar     },
  { label: "Recommendation",Icon: IconFileText    },
];

type AppState = "idle" | "uploading" | "processing" | "ready" | "done" | "error";

export default function Home() {
  const searchParams = useSearchParams();
  const isDemo = searchParams.has("demo");
  const isProcessingDemo = searchParams.has("processing");
  const [appState, setAppState] = useState<AppState>(isDemo ? "done" : isProcessingDemo ? "processing" : "idle");
  const [stage, setStage] = useState<Stage>(isDemo ? "done" : isProcessingDemo ? "extracting" : null);
  const [result, setResult] = useState<AnalysisResult | null>(isDemo ? DEMO_RESULT : null);
  const [selectedBundleId, setSelectedBundleId] = useState<string | null>((isDemo || isProcessingDemo) ? DEMO_RESULT.bundle_id : null);
  const [error, setError] = useState<string | null>(null);
  const [bundles, setBundles] = useState<Bundle[]>([]);
  const [vendorNames, setVendorNames] = useState<string[]>(
    isProcessingDemo ? DEMO_RESULT.proposals.map((p) => p.extracted?.vendor_name ?? p.filename) : []
  );
  const [totalRisks, setTotalRisks] = useState<number | undefined>(undefined);

  useEffect(() => {
    fetch(`${API_BASE}/bundles`)
      .then((r) => r.json())
      .then(setBundles)
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!isProcessingDemo) return;
    const stages: Stage[] = ["extracting", "risk", "scoring", "memo"];
    let i = 0;
    const id = setInterval(() => {
      i = (i + 1) % stages.length;
      setStage(stages[i]);
    }, 2500);
    return () => clearInterval(id);
  }, [isProcessingDemo]);

  function revealResults() {
    setAppState("done");
    const shoot = (angle: number, x: number) =>
      confetti({ particleCount: 80, angle, spread: 55, startVelocity: 60, origin: { x, y: 0.8 } });
    shoot(60, 0);
    setTimeout(() => shoot(120, 1), 150);
    setTimeout(() => shoot(90, 0.5), 300);
  }

  function reset() {
    setAppState("idle");
    setStage(null);
    setResult(null);
    setError(null);
    setVendorNames([]);
    setTotalRisks(undefined);
  }

  const handleSubmit = useCallback(async (files: File[], bundle: string) => {
    setAppState("uploading");
    setSelectedBundleId(bundle);
    setError(null);

    try {
      const form = new FormData();
      files.forEach((f) => form.append("files", f));
      form.append("bundle", bundle);

      const res = await fetch(`${API_BASE}/analyze`, {
        method: "POST",
        body: form,
      });
      if (!res.ok) throw new Error(`Upload failed: ${res.status}`);

      const { job_id } = await res.json();
      setAppState("processing");

      const es = new EventSource(`${API_BASE}/stream/${job_id}`);

      es.addEventListener("extracting", (e) => {
        setStage("extracting");
        try {
          const data = JSON.parse((e as MessageEvent).data);
          if (Array.isArray(data.vendors)) setVendorNames(data.vendors);
        } catch {}
      });

      (["risk", "memo"] as const).forEach(
        (s) => es.addEventListener(s, () => setStage(s))
      );

      es.addEventListener("scoring", (e) => {
        setStage("scoring");
        try {
          const data = JSON.parse((e as MessageEvent).data);
          if (typeof data.total_risks === "number") setTotalRisks(data.total_risks);
        } catch {}
      });

      es.addEventListener("done", (e) => {
        es.close();
        setStage("done");
        const data: AnalysisResult = JSON.parse((e as MessageEvent).data);
        setResult(data);
        setAppState("ready");
      });

      es.addEventListener("error", (e) => {
        es.close();
        const raw = (e as MessageEvent).data;
        const msg = raw ? JSON.parse(raw).error : null;
        setError(msg ?? "An error occurred during analysis.");
        setAppState("error");
      });

      es.onerror = () => {
        es.close();
        setError("Lost connection to the server.");
        setAppState("error");
      };
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setAppState("error");
    }
  }, []);

  const bundleId = result?.bundle_id ?? selectedBundleId;
  const currentBundle = bundleId ? bundles.find((b) => b.id === bundleId) : null;
  const scored = (result?.proposals ?? [])
    .filter((p) => p.scores?.overall != null)
    .sort((a, b) => b.scores!.overall - a.scores!.overall);
  const winner = scored[0] ?? null;
  const sortedProposals = [
    ...scored,
    ...(result?.proposals ?? []).filter((p) => p.scores?.overall == null),
  ];
  const allRisksCount = (result?.proposals ?? []).reduce(
    (sum, p) => sum + (p.risks?.length ?? 0), 0
  );

  return (
    <AppShell header={{ height: 68 }}>
      <AppShell.Header
        style={{
          boxShadow: "0 2px 16px rgba(0,0,0,0.3)",
          background: "#0f1117",
          borderBottom: "2px solid var(--mantine-color-umgreen-5)",
        }}
      >
        <Group h="100%" px="lg" justify="space-between">
          <Group gap="sm">
            <Box style={{ filter: "brightness(0) invert(1)" }}>
              <Logo width={44} />
            </Box>
            <Box>
              <Text fw={800} size="xl" style={{ color: "white", lineHeight: 1.2 }}>
                VendorLens
              </Text>
              <Text size="sm" style={{ color: "rgba(255,255,255,0.45)", lineHeight: 1.3 }}>
                Proposal Intelligence · UMass Procurement
              </Text>
            </Box>
          </Group>
          {appState !== "idle" && (
            <Button
              variant="subtle"
              size="xs"
              leftSection={<IconRefresh size={14} />}
              onClick={reset}
              style={{ color: "rgba(255,255,255,0.6)" }}
            >
              Start over
            </Button>
          )}
        </Group>
      </AppShell.Header>

      <AppShell.Main
        style={{
          background: "#f5f5f5",
          overflowY: "auto",
          height: "calc(100vh - 68px)",
        }}
      >
        <Container size="xl" py="xl">
          {appState === "idle" && (
            <Stack gap="xl" align="center">
              <Box
                py="xl"
                style={{
                  width: "100%",
                  background: "radial-gradient(ellipse 90% 60% at 50% 0%, var(--mantine-color-umblue-0) 0%, transparent 100%)",
                  borderRadius: "var(--mantine-radius-lg)",
                }}
              >
              <Stack gap="md" align="center" maw={560} mx="auto" ta="center">
                <Text size="2rem" fw={800} c="dark" style={{ lineHeight: 1.2 }}>
                  AI-Powered Vendor Analysis
                </Text>
                <Text c="dimmed" size="md">
                  Upload vendor proposals and get structured extraction, risk
                  flags, scoring, and a recommendation memo in under a minute.
                </Text>
                {bundles.length > 0 && (
                  <Group gap="xs" justify="center">
                    {bundles.map((b) => (
                      <Badge key={b.id} variant="light" color="umblue" size="md" radius="sm">
                        {b.label}
                      </Badge>
                    ))}
                  </Group>
                )}
              </Stack>
              </Box>

              {/* Pipeline steps visual */}
              <Group justify="center" gap={0} wrap="nowrap">
                {PIPELINE_STEPS.map(({ label, Icon }, i) => (
                  <Group key={label} gap={0} align="flex-start" wrap="nowrap">
                    <Stack align="center" gap={8} style={{ width: 104 }}>
                      <ThemeIcon size={48} radius="xl" variant="light" color="umblue">
                        <Icon size={22} />
                      </ThemeIcon>
                      <Text size="xs" fw={600} ta="center" c="dimmed" style={{ lineHeight: 1.3 }}>
                        {label}
                      </Text>
                    </Stack>
                    {i < PIPELINE_STEPS.length - 1 && (
                      <Box style={{ paddingTop: 16, color: "var(--mantine-color-gray-4)", flexShrink: 0 }}>
                        <IconArrowRight size={16} />
                      </Box>
                    )}
                  </Group>
                ))}
              </Group>

              <UploadZone
                onSubmit={handleSubmit}
                loading={false}
                bundles={bundles}
              />
            </Stack>
          )}

          {appState === "uploading" && (
            <Stack align="center" gap="xl">
              <UploadZone
                onSubmit={handleSubmit}
                loading={true}
                bundles={bundles}
              />
            </Stack>
          )}

          {(appState === "processing" || appState === "ready" || appState === "done") && (
            <Stack gap="xl" pt="xl">
              {currentBundle && (
                <Box>
                  <Text size="xs" tt="uppercase" fw={600} c="dimmed" style={{ letterSpacing: "0.06em" }}>
                    {appState === "done" || appState === "ready" ? "RFP Evaluation" : "Evaluating"}
                  </Text>
                  <Text fw={700} size="xl" c="dark">{currentBundle.label}</Text>
                  <Text size="sm" c="dimmed">
                    {currentBundle.description}
                    {appState === "done" && ` · ${sortedProposals.length} vendor${sortedProposals.length !== 1 ? "s" : ""} evaluated`}
                  </Text>
                </Box>
              )}

              {appState !== "done" && (
                <SimpleGrid cols={{ base: 1, md: 2 }} spacing="md" style={{ alignItems: "flex-start" }}>
                  <AgentProgressBar stage={appState === "ready" ? "done" : stage} />
                  <ThinkingLog
                    stage={appState === "ready" ? "done" : stage}
                    vendorNames={vendorNames}
                    totalRisks={totalRisks}
                  />
                </SimpleGrid>
              )}

              {(appState === "processing" || appState === "ready") && <BoredPanel />}

              {appState === "done" && result && (
                <Stack gap="xl" className="fadeIn" id="print-report">
                  {winner && (
                    <WinnerHero
                      winner={winner}
                      totalVendors={sortedProposals.length}
                      totalRisks={allRisksCount}
                    />
                  )}

                  {/* KPI summary bar */}
                  <SimpleGrid cols={{ base: 1, sm: 3 }} spacing="md" data-print-hide>
                    {[
                      {
                        value: sortedProposals.length,
                        label: "Vendors Analyzed",
                        icon: <IconBuilding size={22} />,
                        color: "umblue",
                      },
                      {
                        value: allRisksCount,
                        label: "Risks Flagged",
                        icon: <IconAlertTriangle size={22} />,
                        color: "ummaroon",
                      },
                      {
                        value: winner ? Math.round(winner.scores!.overall) : "—",
                        suffix: winner ? "/100" : "",
                        label: "Winner Score",
                        icon: <IconAward size={22} />,
                        color: "umgreen",
                      },
                    ].map(({ value, label, icon, color, suffix = "" }) => (
                      <Paper
                        key={label}
                        p="lg"
                        radius="md"
                        withBorder
                        bg="white"
                        style={{
                          borderLeft: `4px solid var(--mantine-color-${color}-5)`,
                          boxShadow: "0 1px 4px rgba(0,0,0,0.05)",
                        }}
                      >
                        <Group justify="space-between" align="flex-start">
                          <Stack gap={2}>
                            <Text size="xs" tt="uppercase" fw={600} c="dimmed" style={{ letterSpacing: "0.06em" }}>
                              {label}
                            </Text>
                            <Group gap={4} align="baseline">
                              <Text fw={900} style={{ fontSize: "2rem", lineHeight: 1, color: `var(--mantine-color-${color}-7)` }}>
                                {value}
                              </Text>
                              {suffix && <Text size="sm" c="dimmed" fw={500}>{suffix}</Text>}
                            </Group>
                          </Stack>
                          <ThemeIcon size={44} radius="xl" variant="light" color={color}>
                            {icon}
                          </ThemeIcon>
                        </Group>
                      </Paper>
                    ))}
                  </SimpleGrid>

                  <SimpleGrid
                    cols={{ base: 1, md: Math.min(sortedProposals.length, 3) }}
                    spacing="md"
                    style={{ overflow: "visible" }}
                  >
                    {sortedProposals.map((p, i) => (
                      <ProposalCard
                        key={p.filename}
                        proposal={p}
                        recommended={winner !== null && p.filename === winner.filename}
                        winnerScores={winner?.scores ?? undefined}
                        staggerIndex={i}
                      />
                    ))}
                  </SimpleGrid>
                  <VendorRadarChart proposals={sortedProposals} />
                  <VendorComparisonTable proposals={sortedProposals} winner={winner} />
                  {result.memo && <MemoPanel memo={result.memo} />}
                </Stack>
              )}
            </Stack>
          )}

          {appState === "error" && (
            <Stack align="center" gap="md" pt="xl">
              <Alert
                icon={<IconAlertCircle size={18} />}
                color="ummaroon"
                title="Analysis failed"
                maw={560}
                w="100%"
              >
                {error}
              </Alert>
              <Button
                variant="outline"
                color="umblue"
                onClick={reset}
                leftSection={<IconRefresh size={16} />}
              >
                Try again
              </Button>
            </Stack>
          )}
        </Container>

        <Transition mounted={appState === "ready"} transition="slide-up" duration={350}>
          {(styles) => (
            <Box style={{ ...styles, position: "fixed", bottom: 72, right: 24, zIndex: 201 }}>
              <Paper
                radius="lg"
                shadow="xl"
                p="md"
                style={{
                  background: "#0f0f1a",
                  border: "1px solid rgba(255,255,255,0.15)",
                  width: 228,
                }}
              >
                <Stack gap="xs">
                  <Group gap="xs">
                    <IconCircleCheck size={16} color="var(--mantine-color-green-5)" />
                    <Text size="sm" fw={600} style={{ color: "rgba(255,255,255,0.9)" }}>
                      Analysis complete!
                    </Text>
                  </Group>
                  <Text size="xs" style={{ color: "rgba(255,255,255,0.55)" }}>
                    Finish your game or jump straight to results.
                  </Text>
                  <Button size="sm" color="green" fullWidth onClick={revealResults}>
                    View Results →
                  </Button>
                </Stack>
              </Paper>
            </Box>
          )}
        </Transition>
      </AppShell.Main>
    </AppShell>
  );
}
