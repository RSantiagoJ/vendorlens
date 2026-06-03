from typing import Optional, List
from pydantic import BaseModel

from graph.state import ProposalData, RiskFlag, ScoreCard


class AnalyzeResponse(BaseModel):
    job_id: str


class ProposalResult(BaseModel):
    filename: str
    vendor_name: Optional[str] = None
    extracted: Optional[ProposalData] = None
    risks: Optional[List[RiskFlag]] = None
    scores: Optional[ScoreCard] = None


class AnalysisResult(BaseModel):
    job_id: str
    proposals: List[ProposalResult]
    memo: Optional[str] = None
    status: str
    error: Optional[str] = None
