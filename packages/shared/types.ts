import { VerdictLevel } from './risk-levels';
import { ScamCategory } from './scam-categories';

export interface AnalysisRequest {
  text: string;
}

export interface AnalysisResponse {
  id?: string;
  verdict: VerdictLevel;
  risk_score: number;
  category: ScamCategory;
  reason: string;
  red_flags: string[];
  recommended_action: string;
}