"""
End-to-End Verification Suite for ProteinLens-OS Backend & Scientific ML Core
"""

from __future__ import annotations

import sys
from pathlib import Path
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import app  # noqa: E402
from services.ai_router import detect_provider_from_key  # noqa: E402

client = TestClient(app)


def test_health_and_default_iiit_institution():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "IIIT Nagpur" in data["institution"]["institution_name"]
    assert data["ml_engine"]["go_terms"] == 500
    assert data["ml_engine"]["real_3mer_trained"] is True


def test_presets_and_teaching_labs():
    resp = client.get("/api/presets")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["proteins"]) >= 5
    assert len(data["clinical_variants"]) >= 5
    assert len(data["teaching_labs"]) == 4


def test_ai_key_prefix_auto_detection():
    assert detect_provider_from_key("AIzaSyFakeKey123456") == "gemini"
    assert detect_provider_from_key("xai-FakeGrokKey12345") == "grok"
    assert detect_provider_from_key("gsk_FakeGroqKey12345") == "groq"


def test_protein_analysis_zero_dag_violations_and_real_saliency():
    # Hemoglobin Subunit Beta (fast 147 aa)
    resp = client.post(
        "/api/analyze/protein",
        json={"uniprot_id": "P68871", "include_bio_evidence": False},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["sequence_length"] == 147
    assert data["dag_audit"]["violations_after"] == 0
    assert data["structure"]["available"] is True
    assert data["structure"]["mean_plddt"] > 80.0
    assert len(data["xai"]["residue_profile"]) == 147
    assert len(data["dags"]["MF"]["nodes"]) >= 3
    assert len(data["model_arena"]["rows"]) >= 10


def test_dual_axis_variant_and_3d_pocket_dms():
    # Sickle cell HBB E7V (mature E6V)
    resp = client.post(
        "/api/analyze/variant",
        json={
            "uniprot_id": "P68871",
            "gene_symbol": "HBB",
            "position": 7,
            "mut_aa": "V",
            "run_pocket_dms": True,
            "max_pocket_residues": 5,
            "include_bio_evidence": False,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["mutation"] == "E7V"
    assert data["go_disruption"]["mut_dag_violations_after"] == 0
    assert data["structural_pocket"]["available"] is True
    assert data["structural_pocket"]["target_plddt"] is not None
    assert len(data["pocket_dms"]["rows"]) >= 2
    assert len(data["pocket_dms"]["amino_acids"]) == 20
    # Verify all 20 amino acid LLR scores exist for target residue
    target_row = data["pocket_dms"]["rows"][0]
    assert target_row["is_target"] is True
    assert len(target_row["scores"]) == 20
    assert target_row["scores"]["E"] == 0.0  # WT LLR must be exactly 0.0


def test_grounded_copilot_deterministic_fallback_and_sqlite_cases():
    syn = client.post(
        "/api/copilot/synthesize",
        json={
            "audience_mode": "student",
            "evidence_packet": {
                "protein_name": "Hemoglobin Subunit Beta",
                "sequence_length": 147,
                "top_mf": [{"name": "heme binding", "score": 0.91}],
                "dag_audit": {"violations_before": 12, "violations_after": 0, "terms_repaired": 4},
            },
        },
    )
    assert syn.status_code == 200
    sdata = syn.json()
    assert "headline" in sdata
    assert len(sdata["key_citations"]) >= 2

    # Save -> List -> Export -> Delete case in SQLite
    save_resp = client.post(
        "/api/cases",
        json={
            "title": "Test Sickle Cell Case",
            "protein_name": "Hemoglobin Subunit Beta",
            "uniprot_id": "P68871",
            "gene_symbol": "HBB",
            "mutation": "E7V",
            "composite_risk_score": 68.4,
            "evolutionary_llr": -3.1,
            "risk_tier": "Likely Pathogenic",
            "sequence_sha256": "abc123def456",
            "clinician_notes": "Verified by pytest.",
            "mode": "clinical",
            "payload": {"test": True},
        },
    )
    assert save_resp.status_code == 200
    cid = save_resp.json()["id"]

    exp_resp = client.get(f"/api/export/{cid}?fmt=json")
    assert exp_resp.status_code == 200
    exp_data = exp_resp.json()
    assert "provenance_sha256" in exp_data
    assert "IIIT Nagpur" in exp_data["institution"]["institution_name"]

    del_resp = client.delete(f"/api/cases/{cid}")
    assert del_resp.status_code == 200
    assert del_resp.json()["deleted"] is True
