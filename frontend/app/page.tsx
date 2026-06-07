"use client";

export const dynamic = "force-dynamic";

import { AgentProgressBar } from "@/components/AgentProgressBar";
import { BoredPanel } from "@/components/BoredPanel";
import { MemoPanel } from "@/components/MemoPanel";
import { ProposalCard } from "@/components/ProposalCard";
import { ThinkingLog } from "@/components/ThinkingLog";
import { UploadZone } from "@/components/UploadZone";
import { VendorComparisonTable } from "@/components/VendorComparisonTable";
import { VendorRadarChart } from "@/components/VendorRadarChart";
import { WinnerHero } from "@/components/WinnerHero";
import { DEMO_RESULT } from "@/lib/fixtures";
import { countFailedProposals } from "@/lib/scoring";
import type { AnalysisResult, Bundle, Stage } from "@/lib/types";
import { Logo } from "@/logo";
import {
  Alert,
  AppShell,
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
  IconAlertCircle,
  IconAlertTriangle,
  IconAward,
  IconBuilding,
  IconChartBar,
  IconCircleCheck,
  IconFileText,
  IconRefresh,
  IconSearch,
  IconShieldCheck,
} from "@tabler/icons-react";
import confetti from "canvas-confetti";
import { useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useRef, useState } from "react";

const LANDING_QUOTES = [
  "A great contract awaits you — but read the auto-renewal clause first.",
  "The vendor with the highest score is not always the lowest risk.",
  "The winning vendor is not the cheapest — it is the least surprising.",
  "A DPA is worth a thousand apologies.",
  "Five AI agents cannot replace due diligence. They can, however, speed it up considerably.",
  "The auto-renewal clause is always watching.",
  "A SOC 2 Type II audit report is a love language.",
  "The best negotiation starts before you sign.",
  "Read every exhibit. Especially Exhibit C.",
  "An SLA without teeth is just a suggestion.",
  "The vendor that rushes you to sign has something to hide.",
  "Good things come to those who benchmark.",
  "A $50,000 liability cap is a red flag dressed as a number.",
  "Governing law matters more than the vendor admits.",
  "The RFP rubric you set today shapes the vendor you're stuck with tomorrow.",
];

function BackgroundQuotes() {
  const [idx, setIdx] = useState(0);
  const [visible, setVisible] = useState(true);
  const [hovered, setHovered] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const SHOW_MS = 4800;
  const FADE_MS = 900;

  function advance() {
    setVisible(false);
    setTimeout(() => {
      setIdx((i) => (i + 1) % LANDING_QUOTES.length);
      setVisible(true);
    }, FADE_MS);
  }

  function restartTimer() {
    if (intervalRef.current) clearInterval(intervalRef.current);
    intervalRef.current = setInterval(advance, SHOW_MS + FADE_MS);
  }

  useEffect(() => {
    // Randomize starting quote client-side only (avoids SSR hydration mismatch)
    setIdx(Math.floor(Math.random() * LANDING_QUOTES.length));
    restartTimer();
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <Box
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      onClick={() => { advance(); restartTimer(); }}
      style={{ cursor: "pointer" }}
    >
      <Text
        style={{
          fontStyle: "italic",
          fontWeight: 300,
          lineHeight: 1.7,
          fontSize: "clamp(1.15rem, 1.7vw, 1.55rem)",
          color: "white",
          opacity: visible ? (hovered ? 1 : 0.82) : 0,
          transition: "opacity 0.9s ease-in-out",
          userSelect: "none",
        }}
      >
        &ldquo;{LANDING_QUOTES[idx]}&rdquo;
      </Text>
      <Text
        style={{
          marginTop: 16,
          fontSize: "0.7rem",
          letterSpacing: "0.1em",
          textTransform: "uppercase",
          color: "rgba(255,255,255,0.35)",
          userSelect: "none",
          opacity: hovered ? 1 : 0,
          transition: "opacity 0.25s ease",
        }}
      >
        ↻ click to change
      </Text>
    </Box>
  );
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const PIPELINE_STEPS = [
  { label: "Extract",        Icon: IconSearch     },
  { label: "Risk Analysis",  Icon: IconShieldCheck },
  { label: "Scoring",        Icon: IconChartBar   },
  { label: "Recommendation", Icon: IconFileText   },
];

type AppState =
  | "idle"
  | "uploading"
  | "processing"
  | "ready"
  | "done"
  | "error";

function HomeContent() {
  const searchParams = useSearchParams();
  const isDemo = searchParams.has("demo");
  const isProcessingDemo = searchParams.has("processing");
  const [appState, setAppState] = useState<AppState>(
    isDemo ? "done" : isProcessingDemo ? "processing" : "idle",
  );
  const [stage, setStage] = useState<Stage>(
    isDemo ? "done" : isProcessingDemo ? "extracting" : null,
  );
  const [result, setResult] = useState<AnalysisResult | null>(
    isDemo ? DEMO_RESULT : null,
  );
  const [selectedBundleId, setSelectedBundleId] = useState<string | null>(
    isDemo || isProcessingDemo ? DEMO_RESULT.bundle_id : null,
  );
  const [error, setError] = useState<string | null>(null);
  const [bundles, setBundles] = useState<Bundle[]>([]);
  const [vendorNames, setVendorNames] = useState<string[]>(
    isProcessingDemo
      ? DEMO_RESULT.proposals.map((p) => p.extracted?.vendor_name ?? p.filename)
      : [],
  );
  const [totalRisks, setTotalRisks] = useState<number | undefined>(undefined);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

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

    const umColors = ["#881c1c", "#ffffff", "#00a550", "#003087", "#FFD700"];
    const shoot = (angle: number, x: number, count = 130) =>
      confetti({ particleCount: count, angle, spread: 65, startVelocity: 72, origin: { x, y: 0.88 }, ticks: 220, colors: umColors });

    // Wave 1 — both side cannons at once
    shoot(60, 0, 160);
    shoot(120, 1, 160);

    // Wave 2 — inner flanks
    setTimeout(() => { shoot(72, 0.12, 140); shoot(108, 0.88, 140); }, 180);

    // Wave 3 — mid-court + center up
    setTimeout(() => { shoot(80, 0.3, 120); shoot(100, 0.7, 120); shoot(90, 0.5, 200); }, 380);

    // Wave 4 — 360° sphere burst from center
    setTimeout(() => confetti({ particleCount: 500, spread: 360, startVelocity: 28, decay: 0.94, gravity: 0.75, origin: { x: 0.5, y: 0.45 }, ticks: 350, colors: umColors }), 650);

    // Wave 5 — gold star shower
    setTimeout(() => confetti({ particleCount: 120, spread: 360, startVelocity: 18, decay: 0.96, gravity: 0.35, origin: { x: 0.5, y: 0.5 }, ticks: 500, shapes: ["star"], colors: ["#FFD700", "#FFA500", "#FF6347"], scalar: 1.5 }), 850);

    // Wave 6 — second side salvo
    setTimeout(() => { shoot(60, 0.05, 120); shoot(120, 0.95, 120); }, 1200);

    // Wave 7 — ceiling rain finale
    setTimeout(() => confetti({ particleCount: 200, spread: 260, startVelocity: 8, decay: 0.95, gravity: 1.1, origin: { x: 0.5, y: 0 }, ticks: 300, colors: umColors }), 1550);
  }

  function reset() {
    if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
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

      // Poll /progress every 2s instead of SSE — avoids App Runner 120s hard cut
      pollRef.current = setInterval(async () => {
        try {
          const poll = await fetch(`${API_BASE}/jobs/${job_id}/progress`);
          if (!poll.ok) return;
          const data = await poll.json();

          if (Array.isArray(data.vendors) && data.vendors.length)
            setVendorNames(data.vendors);
          if (typeof data.total_risks === "number")
            setTotalRisks(data.total_risks);
          if (data.stage && data.stage !== "pending")
            setStage(data.stage as Stage);

          if (data.status === "done" || data.status === "partial") {
            clearInterval(pollRef.current!); pollRef.current = null;
            setResult(data.result as AnalysisResult);
            setStage("memo");
            setTimeout(() => { setStage("done"); setAppState("ready"); }, 800);
          } else if (data.status === "error") {
            clearInterval(pollRef.current!); pollRef.current = null;
            setError(data.result?.error ?? "Analysis failed.");
            setAppState("error");
          }
        } catch {}
      }, 2000);

      // Hard timeout — pipeline should never take more than 5 min
      setTimeout(() => {
        if (pollRef.current) {
          clearInterval(pollRef.current); pollRef.current = null;
          setError("Analysis timed out. Please try again.");
          setAppState("error");
        }
      }, 300_000);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setAppState("error");
    }
  }, []);

  const bundleId = result?.bundle_id ?? selectedBundleId;
  const currentBundle = bundleId
    ? bundles.find((b) => b.id === bundleId)
    : null;
  const scored = (result?.proposals ?? [])
    .filter((p) => p.scores?.overall != null)
    .sort((a, b) => b.scores!.overall - a.scores!.overall);
  const winner = scored[0] ?? null;
  const sortedProposals = [
    ...scored,
    ...(result?.proposals ?? []).filter((p) => p.scores?.overall == null),
  ];
  const allRisksCount = (result?.proposals ?? []).reduce(
    (sum, p) => sum + (p.risks?.length ?? 0),
    0,
  );

  return (
    <AppShell header={{ height: 68 }}>
      <AppShell.Header
        style={{
          boxShadow: "0 2px 20px rgba(0,0,0,0.4)",
          background: "linear-gradient(90deg, #1c0810 0%, #0f1117 55%)",
          borderBottom: "2px solid var(--mantine-color-umgreen-5)",
        }}
      >
        <Group h="100%" px="lg" justify="space-between">
          <Group gap="sm">
            <Box style={{ filter: "brightness(0) invert(1)" }}>
              <Logo width={44} />
            </Box>
            <Box>
              <Text
                fw={800}
                size="xl"
                style={{ color: "white", lineHeight: 1.2 }}
              >
                VendorLens
              </Text>
              <Text
                size="sm"
                c="umblue.3"
                style={{
                  lineHeight: 1.3,
                }}
              >
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
              style={{ color: "rgba(255,255,255,0.8)" }}
            >
              Start over
            </Button>
          )}
        </Group>
      </AppShell.Header>

      <AppShell.Main
        style={{
          background: "#f5f5f5",
          overflowY: appState === "idle" ? "hidden" : "auto",
          height: "calc(100vh - 68px)",
        }}
      >
        <Container size="xl" py={appState === "idle" ? 0 : "xl"}>
          {appState === "idle" && (
            <Box style={{ display: "flex", height: "calc(100vh - 68px)" }}>
              {/* Left — quote panel */}
              <Box
                style={{
                  flex: "0 0 42%",
                  background: "linear-gradient(160deg, #1c0810 0%, #0f1117 55%, #0d1a2e 100%)",
                  borderRight: "1px solid rgba(255,255,255,0.06)",
                  display: "flex",
                  flexDirection: "column",
                  padding: "40px",
                }}
              >
                <Box style={{ flex: 1, display: "flex", alignItems: "center" }}>
                  <BackgroundQuotes />
                </Box>
                <Stack gap={12}>
                  {PIPELINE_STEPS.map(({ label, Icon }, i) => (
                    <Group key={label} gap={12} align="center">
                      <Text fw={600} style={{ color: "rgba(255,255,255,0.35)", minWidth: 18, textAlign: "right", fontSize: "0.85rem" }}>{i + 1}</Text>
                      <Icon size={16} color="rgba(255,255,255,0.55)" />
                      <Text style={{ color: "rgba(255,255,255,0.75)", fontSize: "0.95rem" }}>{label}</Text>
                    </Group>
                  ))}
                </Stack>
              </Box>

              {/* Right — upload panel */}
              <Box
                style={{
                  flex: 1,
                  background: "white",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  padding: "40px 48px",
                  overflowY: "auto",
                }}
              >
                <Stack gap="lg" w="100%" maw={500}>
                  <Box ta="center">
                    <Text fw={800} c="dark" style={{ fontSize: "2rem", lineHeight: 1.15, letterSpacing: "-0.02em" }}>
                      AI-Powered Vendor Analysis
                    </Text>
                    <Text c="dimmed" size="md" mt={10} style={{ lineHeight: 1.6 }}>
                      Upload vendor proposals and get structured extraction, risk flags, scoring, and a recommendation memo in under a minute.
                    </Text>
                  </Box>

                  <UploadZone onSubmit={handleSubmit} loading={false} bundles={bundles} />
                </Stack>
              </Box>
            </Box>
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

          {(appState === "processing" ||
            appState === "ready" ||
            appState === "done") && (
            <Stack gap="xl" pt="xl">
              {currentBundle && (
                <Box>
                  <Text
                    size="xs"
                    tt="uppercase"
                    fw={600}
                    c="dimmed"
                    style={{ letterSpacing: "0.06em" }}
                  >
                    {appState === "done" || appState === "ready"
                      ? "RFP Evaluation"
                      : "Evaluating"}
                  </Text>
                  <Text fw={700} size="xl" c="dark">
                    {currentBundle.label}
                  </Text>
                  <Text size="sm" c="dimmed">
                    {currentBundle.description}
                    {appState === "done" &&
                      ` · ${sortedProposals.length} vendor${sortedProposals.length !== 1 ? "s" : ""} evaluated`}
                  </Text>
                </Box>
              )}

              {appState !== "done" && (
                <SimpleGrid
                  cols={{ base: 1, md: 2 }}
                  spacing="md"
                  style={{ alignItems: "stretch" }}
                >
                  <AgentProgressBar
                    stage={appState === "ready" ? "done" : stage}
                  />
                  <ThinkingLog
                    stage={appState === "ready" ? "done" : stage}
                    vendorNames={vendorNames}
                    totalRisks={totalRisks}
                  />
                </SimpleGrid>
              )}

              {(appState === "processing" || appState === "ready") && (
                <BoredPanel />
              )}

              {appState === "done" && result && (
                <Stack gap="xl" className="fadeIn" id="print-report">
                  {result.status === "partial" && (
                    <Alert
                      icon={<IconAlertTriangle size={16} />}
                      color="umyellow"
                      variant="light"
                      title="Partial results"
                      radius="md"
                    >
                      {countFailedProposals(result.proposals)} of{" "}
                      {result.proposals.length} vendor
                      {result.proposals.length !== 1 ? "s" : ""} could not be
                      scored. Results below reflect only the vendors that
                      completed analysis.
                    </Alert>
                  )}

                  {winner && (
                    <WinnerHero
                      winner={winner}
                      totalVendors={sortedProposals.length}
                      totalRisks={allRisksCount}
                    />
                  )}

                  {/* KPI summary bar */}
                  <SimpleGrid
                    cols={{ base: 1, sm: 3 }}
                    spacing="md"
                    data-print-hide
                  >
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
                        value: winner
                          ? Math.round(winner.scores!.overall)
                          : "—",
                        suffix: winner ? "/10" : "",
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
                            <Text
                              size="xs"
                              tt="uppercase"
                              fw={600}
                              c="dimmed"
                              style={{ letterSpacing: "0.06em" }}
                            >
                              {label}
                            </Text>
                            <Group gap={4} align="baseline">
                              <Text
                                fw={900}
                                style={{
                                  fontSize: "2rem",
                                  lineHeight: 1,
                                  color: `var(--mantine-color-${color}-7)`,
                                }}
                              >
                                {value}
                              </Text>
                              {suffix && (
                                <Text size="sm" c="dimmed" fw={500}>
                                  {suffix}
                                </Text>
                              )}
                            </Group>
                          </Stack>
                          <ThemeIcon
                            size={44}
                            radius="xl"
                            variant="light"
                            color={color}
                          >
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
                        recommended={
                          winner !== null && p.filename === winner.filename
                        }
                        winnerScores={winner?.scores ?? undefined}
                        staggerIndex={i}
                      />
                    ))}
                  </SimpleGrid>
                  <VendorRadarChart proposals={sortedProposals} />
                  <VendorComparisonTable
                    proposals={sortedProposals}
                    winner={winner}
                  />
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

        <Transition
          mounted={appState === "ready"}
          transition="slide-up"
          duration={350}
        >
          {(styles) => (
            <Box
              style={{
                ...styles,
                position: "fixed",
                bottom: 72,
                right: 24,
                zIndex: 201,
              }}
            >
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
                    <IconCircleCheck
                      size={16}
                      color="var(--mantine-color-green-5)"
                    />
                    <Text
                      size="sm"
                      fw={600}
                      style={{ color: "rgba(255,255,255,0.9)" }}
                    >
                      Analysis complete!
                    </Text>
                  </Group>
                  <Text size="xs" style={{ color: "rgba(255,255,255,0.55)" }}>
                    Finish your game or jump straight to results.
                  </Text>
                  <Button
                    size="sm"
                    color="green"
                    fullWidth
                    onClick={revealResults}
                  >
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

export default function Home() {
  return (
    <Suspense fallback={null}>
      <HomeContent />
    </Suspense>
  );
}
