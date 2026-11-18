"""
ProteinLens-OS Pydantic v2 Request / Response Schemas
Single source of truth for FastAPI OpenAPI and Next.js TypeScript contracts.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AnalyzeProteinRequest(BaseModel):
    sequence: Optional[str] = None
    uniprot_id: Optional[str] = None
    protein_name: Optional[str] = None
    min_confidence: float = Field(default=0.20, ge=0.05, le=0.95)
    include_bio_evidence: bool = True


class AnalyzeVariantRequest(BaseModel):
    sequence: Optional[str] = None
    uniprot_id: Optional[str] = None
    gene_symbol: Optional[str] = None
    protein_name: Optional[str] = None
    position: int = Field(..., ge=1, le=512)
    mut_aa: str = Field(..., min_length=1, max_length=1)
    run_pocket_dms: bool = True
    max_pocket_residues: int = Field(default=8, ge=1, le=14)
    include_bio_evidence: bool = True


class BatchVariantItem(BaseModel):
    label: Optional[str] = None
    uniprot_id: Optional[str] = None
    gene_symbol: Optional[str] = None
    sequence: Optional[str] = None
    position: int = Field(..., ge=1, le=512)
    mut_aa: str = Field(..., min_length=1, max_length=1)


class BatchTriageRequest(BaseModel):
    title: str = "Patient Variant Cohort Triage"
    items: List[BatchVariantItem] = Field(..., min_length=1, max_length=30)


class SaveCaseRequest(BaseModel):
    title: str
    protein_name: str
    uniprot_id: Optional[str] = None
    gene_symbol: Optional[str] = None
    mutation: Optional[str] = None
    composite_risk_score: Optional[float] = None
    evolutionary_llr: Optional[float] = None
    risk_tier: Optional[str] = None
    sequence_sha256: str
    clinician_notes: str = ""
    mode: str = "research"
    payload: Dict[str, Any]


class UpdateCaseNotesRequest(BaseModel):
    clinician_notes: str


class AIConfigRequest(BaseModel):
    provider: str = "auto"  # auto | gemini | grok | groq | ollama | deterministic
    api_key: Optional[str] = None
    model_name: Optional[str] = None
    ollama_url: Optional[str] = None


class InstitutionUpdateRequest(BaseModel):
    institution_name: str
    department: str
    location: str
    report_disclaimer: str
    default_audience_mode: str = "clinical"


class CopilotSynthesizeRequest(BaseModel):
    evidence_packet: Dict[str, Any]
    audience_mode: str = "clinical"  # clinical | research | student
