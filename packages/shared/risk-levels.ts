export type VerdictLevel = 'GREEN' | 'YELLOW' | 'RED';

export const RISK_THRESHOLDS = {
  GREEN_MAX: 29,
  YELLOW_MAX: 59,
  MAX_SCORE: 100,
  MIN_SCORE: 0,
} as const;