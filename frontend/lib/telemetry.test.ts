import { describe, it, expect } from "vitest";
import { formatElapsed, buildTelemetrySummary } from "./telemetry";
import type { ProposalResult } from "./types";

describe("formatElapsed", () => {
  it("formats sub-minute durations as seconds", () => {
    expect(formatElapsed(5_000)).toBe("5.0s");
    expect(formatElapsed(38_200)).toBe("38.2s");
    expect(formatElapsed(59_900)).toBe("59.9s");
  });

  it("formats minute+ durations as m s", () => {
    expect(formatElapsed(60_000)).toBe("1m 0s");
    expect(formatElapsed(72_000)).toBe("1m 12s");
    expect(formatElapsed(125_000)).toBe("2m 5s");
  });

  it("formats zero correctly", () => {
    expect(formatElapsed(0)).toBe("0.0s");
  });
});

describe("buildTelemetrySummary", () => {
  const p = (riskCount: number) =>
    ({
      filename: "test.pdf",
      vendor_name: "Test",
      extracted: null,
      risks: Array.from({ length: riskCount }, (_, i) => ({
        clause: `Clause ${i}`,
        severity: "LOW" as const,
        explanation: "",
        recommendation: "",
        policy_reference: "",
        policy_excerpt: null,
      })),
      scores: null,
    }) as ProposalResult;

  it("counts vendors and risk flags", () => {
    const summary = buildTelemetrySummary([p(3), p(2)]);
    expect(summary.vendorCount).toBe(2);
    expect(summary.riskCount).toBe(5);
  });

  it("includes formatted elapsed time when provided", () => {
    const summary = buildTelemetrySummary([p(1)], 38_200);
    expect(summary.elapsed).toBe("38.2s");
  });

  it("sets elapsed to null when not provided", () => {
    const summary = buildTelemetrySummary([p(1)]);
    expect(summary.elapsed).toBeNull();
  });

  it("handles proposals with null risks", () => {
    const noRisks = { ...p(0), risks: null } as ProposalResult;
    const summary = buildTelemetrySummary([noRisks, p(2)]);
    expect(summary.riskCount).toBe(2);
  });

  it("includes llmCostUsd when provided", () => {
    const summary = buildTelemetrySummary([p(1)], 5000, 0.07);
    expect(summary.llmCostUsd).toBe(0.07);
  });

  it("sets llmCostUsd to null when not provided", () => {
    const summary = buildTelemetrySummary([p(1)]);
    expect(summary.llmCostUsd).toBeNull();
  });
});
