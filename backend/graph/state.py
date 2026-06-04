"""
VendorLens shared state definitions.

All Pydantic models for the LangGraph pipeline live here.
Agents import these directly. The graph imports VendorLensState.
"""

from typing import Optional, List, Literal
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Extraction Agent output
# ---------------------------------------------------------------------------

class ProposalData(BaseModel):
    vendor_name: Optional[str] = None
    total_cost: Optional[str] = None
    pricing_model: Optional[str] = None
    price_escalation: Optional[str] = None
    overage_fees: Optional[str] = None
    contract_length: Optional[str] = None
    renewal_terms: Optional[str] = None
    termination_clause: Optional[str] = None
    liability_cap: Optional[str] = None
    data_ownership: Optional[str] = None
    data_processing_agreement: Optional[str] = None
    security_certifications: Optional[str] = None
    incident_response_docs: Optional[str] = None
    sla_uptime: Optional[str] = None
    sla_response_times: Optional[str] = None
    sla_penalties: Optional[str] = None
    support_model: Optional[str] = None
    training_offered: Optional[str] = None
    multi_campus_support: Optional[str] = None
    user_roles: Optional[str] = None
    mobile_app: Optional[str] = None
    accessibility_vpat: Optional[str] = None
    social_listening: Optional[str] = None
    analytics_reporting: Optional[str] = None
    integrations: Optional[str] = None
    sandbox_available: Optional[str] = None
    customer_references: Optional[str] = None
    supplier_diversity: Optional[str] = None
    deliverables: Optional[List[str]] = None
    ip_ownership: Optional[str] = None
    governing_law: Optional[str] = None


# ---------------------------------------------------------------------------
# Risk Agent output
# ---------------------------------------------------------------------------

class RiskFlag(BaseModel):
    clause: str
    severity: Literal["HIGH", "MEDIUM", "LOW"]
    explanation: str
    recommendation: str
    policy_reference: str
    policy_excerpt: Optional[str] = None


# ---------------------------------------------------------------------------
# Scoring Agent output
# ---------------------------------------------------------------------------

class DimensionScore(BaseModel):
    score: float
    rationale: str


class ScoreCard(BaseModel):
    platform_functionality: DimensionScore
    accessibility_compliance: DimensionScore
    integration_capability: DimensionScore
    pricing_transparency: DimensionScore
    security_and_compliance: DimensionScore
    support_and_training: DimensionScore
    enterprise_readiness: DimensionScore
    innovation_roadmap: DimensionScore
    risk_level: DimensionScore
    overall: float


# ---------------------------------------------------------------------------
# Per-proposal container (one element in VendorLensState.proposals)
# ---------------------------------------------------------------------------

class ProposalState(BaseModel):
    filename: str
    raw_text: str
    extracted: Optional[ProposalData] = None
    risks: Optional[List[RiskFlag]] = None
    scores: Optional[ScoreCard] = None


# ---------------------------------------------------------------------------
# Top-level graph state
# ---------------------------------------------------------------------------

class VendorLensState(BaseModel):
    proposals: List[ProposalState] = []
    memo: Optional[str] = None
    status: Literal[
        "pending", "extracting", "risk", "scoring", "memo", "done", "error"
    ] = "pending"
    error: Optional[str] = None
