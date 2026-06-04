export interface DimensionScore {
  score: number;
  rationale: string;
}

export interface ScoreCard {
  platform_functionality: DimensionScore;
  accessibility_compliance: DimensionScore;
  integration_capability: DimensionScore;
  pricing_transparency: DimensionScore;
  security_and_compliance: DimensionScore;
  support_and_training: DimensionScore;
  enterprise_readiness: DimensionScore;
  risk_level: DimensionScore;
  overall: number;
}

export interface RiskFlag {
  clause: string;
  severity: "HIGH" | "MEDIUM" | "LOW";
  explanation: string;
  recommendation: string;
  policy_reference: string;
  policy_excerpt: string | null;
}

export interface ProposalData {
  vendor_name: string | null;
  total_cost: string | null;
  pricing_model: string | null;
  price_escalation: string | null;
  overage_fees: string | null;
  contract_length: string | null;
  renewal_terms: string | null;
  termination_clause: string | null;
  liability_cap: string | null;
  data_ownership: string | null;
  data_processing_agreement: string | null;
  security_certifications: string | null;
  incident_response_docs: string | null;
  sla_uptime: string | null;
  sla_response_times: string | null;
  sla_penalties: string | null;
  support_model: string | null;
  training_offered: string | null;
  multi_campus_support: string | null;
  user_roles: string | null;
  mobile_app: string | null;
  accessibility_vpat: string | null;
  social_listening: string | null;
  analytics_reporting: string | null;
  integrations: string | null;
  sandbox_available: string | null;
  customer_references: string | null;
  supplier_diversity: string | null;
  deliverables: string[] | null;
  ip_ownership: string | null;
  governing_law: string | null;
}

export interface ProposalResult {
  filename: string;
  vendor_name: string | null;
  extracted: ProposalData | null;
  risks: RiskFlag[] | null;
  scores: ScoreCard | null;
}

export interface AnalysisResult {
  job_id: string;
  bundle_id: string;
  proposals: ProposalResult[];
  memo: string | null;
  status: string;
  error: string | null;
}

export interface Bundle {
  id: string;
  label: string;
  description: string;
}

export type Stage = "extracting" | "risk" | "scoring" | "memo" | "done" | null;
