"use client";

import { useState, useCallback, useEffect } from "react";
import {
  AppShell, Box, Group, Text, Container, Stack, Alert, Button,
  SimpleGrid, Badge,
} from "@mantine/core";
import { IconRefresh, IconAlertCircle } from "@tabler/icons-react";
import { Logo } from "@/logo";
import { UploadZone } from "@/components/UploadZone";
import { AgentProgressBar } from "@/components/AgentProgressBar";
import { ThinkingLog } from "@/components/ThinkingLog";
import { ProposalCard } from "@/components/ProposalCard";
import { MemoPanel } from "@/components/MemoPanel";
import type { AnalysisResult, Bundle, Stage } from "@/lib/types";

const API_BASE = "http://localhost:8000";

type AppState = "idle" | "uploading" | "processing" | "done" | "error";

export default function Home() {
  const [appState, setAppState] = useState<AppState>("idle");
  const [stage, setStage] = useState<Stage>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [bundles, setBundles] = useState<Bundle[]>([
    { id: "lms", label: "LMS Platform RFP", description: "Learning Management System evaluation for multi-campus university" },
    { id: "cyber", label: "Cybersecurity Services RFP", description: "Managed security services evaluation against NIST/FedRAMP standards" },
  ]);

  useEffect(() => {
    fetch(`${API_BASE}/bundles`)
      .then((r) => r.json())
      .then(setBundles)
      .catch(() => {}); // fall back to defaults above if backend unreachable
  }, []);

  function reset() {
    setAppState("idle");
    setStage(null);
    setResult(null);
    setError(null);
  }

  const handleSubmit = useCallback(async (files: File[], bundle: string) => {
    setAppState("uploading");
    setError(null);

    try {
      const form = new FormData();
      files.forEach((f) => form.append("files", f));
      form.append("bundle", bundle);

      const res = await fetch(`${API_BASE}/analyze`, { method: "POST", body: form });
      if (!res.ok) throw new Error(`Upload failed: ${res.status}`);

      const { job_id } = await res.json();
      setAppState("processing");

      const es = new EventSource(`${API_BASE}/stream/${job_id}`);

      es.addEventListener("extracting", () => setStage("extracting"));
      es.addEventListener("risk", () => setStage("risk"));
      es.addEventListener("scoring", () => setStage("scoring"));
      es.addEventListener("memo", () => setStage("memo"));

      es.addEventListener("done", (e) => {
        es.close();
        setStage("done");
        const data: AnalysisResult = JSON.parse((e as MessageEvent).data);
        setResult(data);
        setAppState("done");
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

  const activeBundle = result ? bundles.find((b) => b.id === result.bundle_id) : null;

  return (
    <AppShell header={{ height: 68 }}>
      <AppShell.Header
        style={{
          boxShadow: "0 1px 8px rgba(0,0,0,0.08)",
          background: "white",
          borderBottom: "none",
        }}
      >
        <Group h="100%" px="lg" justify="space-between">
          <Group gap="sm">
            <Logo width={44} />
            <Box>
              <Text fw={800} size="xl" c="dark" style={{ lineHeight: 1.2 }}>
                VendorLens
              </Text>
              <Text size="sm" c="dimmed" style={{ lineHeight: 1.3 }}>
                Proposal Intelligence · UMass Procurement
              </Text>
            </Box>
          </Group>
          {appState !== "idle" && (
            <Button
              variant="subtle"
              color="gray"
              size="xs"
              leftSection={<IconRefresh size={14} />}
              onClick={reset}
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
              <Stack gap="xs" align="center" maw={560} mx="auto" ta="center">
                <Text size="2rem" fw={800} c="dark" style={{ lineHeight: 1.2 }}>
                  AI-Powered Vendor Analysis
                </Text>
                <Text c="dimmed" size="md">
                  Upload vendor proposals and get structured extraction, risk flags,
                  scoring, and a recommendation memo — in under a minute.
                </Text>
              </Stack>
              <UploadZone onSubmit={handleSubmit} loading={false} bundles={bundles} />
            </Stack>
          )}

          {appState === "uploading" && (
            <Stack align="center" gap="xl">
              <UploadZone onSubmit={handleSubmit} loading={true} bundles={bundles} />
            </Stack>
          )}

          {appState === "processing" && (
            <Stack align="center" gap="md" pt="xl">
              <AgentProgressBar stage={stage} />
              <ThinkingLog stage={stage} />
            </Stack>
          )}

          {appState === "done" && result && (() => {
            const bestScore = Math.max(...result.proposals.map((p) => p.scores?.overall ?? -1));
            return (
              <Stack gap="xl" className="fadeIn">
                <Group justify="space-between" align="center">
                  <AgentProgressBar stage="done" />
                  {activeBundle && (
                    <Badge variant="light" color="umblue" size="md" radius="sm">
                      {activeBundle.label}
                    </Badge>
                  )}
                </Group>
                <SimpleGrid cols={{ base: 1, md: Math.min(result.proposals.length, 3) }} spacing="md">
                  {result.proposals.map((p) => (
                    <ProposalCard
                      key={p.filename}
                      proposal={p}
                      recommended={bestScore > 0 && p.scores?.overall === bestScore}
                    />
                  ))}
                </SimpleGrid>
                {result.memo && <MemoPanel memo={result.memo} />}
              </Stack>
            );
          })()}

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
      </AppShell.Main>
    </AppShell>
  );
}
