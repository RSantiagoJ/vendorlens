from pydantic import BaseModel

from graph.state import ProposalData, RiskFlag, ScoreCard


class AnalyzeResponse(BaseModel):
    job_id: str


class ProposalResult(BaseModel):
    filename: str
    vendor_name: str | None = None
    extracted: ProposalData | None = None
    risks: list[RiskFlag] | None = None
    scores: ScoreCard | None = None
    error: str | None = None


class AnalysisResult(BaseModel):
    job_id: str
    bundle_id: str = "lms"
    proposals: list[ProposalResult]
    memo: str | None = None
    status: str
    error: str | None = None
