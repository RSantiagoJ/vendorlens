import type { ProposalResult } from "./types";

export interface TelemetrySummary {
  vendorCount: number;
  riskCount: number;
  elapsed: string | null;
}

export function formatElapsed(ms: number): string {
  if (ms < 60_000) return `${(ms / 1000).toFixed(1)}s`;
  const m = Math.floor(ms / 60_000);
  const s = Math.round((ms % 60_000) / 1000);
  return `${m}m ${s}s`;
}

export function buildTelemetrySummary(
  proposals: ProposalResult[],
  elapsedMs?: number,
): TelemetrySummary {
  return {
    vendorCount: proposals.length,
    riskCount: proposals.reduce((sum, p) => sum + (p.risks?.length ?? 0), 0),
    elapsed: elapsedMs != null ? formatElapsed(elapsedMs) : null,
  };
}
