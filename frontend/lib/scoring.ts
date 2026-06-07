// Scoring scale: 0–10. Do not multiply by 10 or normalize to 0–100.
// See DECISIONS.md — "Scoring scale 0–10 (not 0–100)" for the full history.

export const SCORE_TIERS = [
  { min: 7, color: "umgreen",  textColor: "var(--mantine-color-umgreen-6)"  },
  { min: 4, color: "umyellow", textColor: "var(--mantine-color-umyellow-7)" },
  { min: 0, color: "ummaroon", textColor: "var(--mantine-color-ummaroon-6)" },
] as const;

export type ScoreTier = typeof SCORE_TIERS[number];

export function scoreTier(score: number): ScoreTier {
  return SCORE_TIERS.find((t) => score >= t.min)!;
}

export function scoreLabel(overall: number): "Meets Criteria" | "Needs Review" | "Below Threshold" {
  if (overall >= 7) return "Meets Criteria";
  if (overall >= 4) return "Needs Review";
  return "Below Threshold";
}

export function scoreLabelShort(overall: number): "Meets" | "Review" | "Fails" {
  if (overall >= 7) return "Meets";
  if (overall >= 4) return "Review";
  return "Fails";
}

export function ringFillPercent(score: number): number {
  return (score / 10) * 100;
}

export function barFillPercent(score: number): number {
  return (score / 10) * 100;
}
