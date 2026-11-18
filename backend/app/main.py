"""
ProteinLens-OS FastAPI Application
Full-Stack REST + SSE Backend powering:
- Independent Scientific ML Core (ESM2 LLR, 3D Pocket DMS, Real 3-mer, MLP/kNN, Exact True Path DAG)
- Federated Open-Bio APIs (UniProt, AlphaFold DB, NCBI ClinVar, Open Targets)
- Auto-Configuring Multi-Provider XAI Router (Gemini / xAI Grok / Groq / Ollama / Local Fallback)
- Institutional White-Label Configuration, Academic Teaching Labs & SQLite Persistence
"""

from __future__ import annotations

import asyncio
import csv
import hashlib
import io
import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlmodel import select
from sse_starlette.sse import EventSourceResponse

from ml.engine import ProteinLensScientificEngine
from services.ai_router import AutoConfigAIRouter
from services.bio_apis import BioEvidenceService
from .database import BatchJob, ClinicalCase, DatabaseManager, InstitutionConfig, utc_now_iso
from .labs_catalog import ACADEMIC_TEACHING_LABS, CLINICAL_VARIANT_PRESETS
from .schemas import (
    AIConfigRequest,
    AnalyzeProteinRequest,
    AnalyzeVariantRequest,
    BatchTriageRequest,
    CopilotSynthesizeRequest,
    InstitutionUpdateRequest,
    SaveCaseRequest,
    UpdateCaseNotesRequest,
)


BACKEND_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = BACKEND_ROOT / "assets"
DB_PATH = BACKEND_ROOT / "data" / "proteinlens.db"
ENV_FILE = BACKEND_ROOT / ".env"

app = FastAPI(
    title="ProteinLens-OS API",
    description="Open-Source Clinical Variant Intelligence, 3D-Pocket Zero-Shot DMS & True-Path GO Platform",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize singletons
db = DatabaseManager(DB_PATH)
engine = ProteinLensScientificEngine(ASSETS_DIR)
bio_service = BioEvidenceService()
ai_router = AutoConfigAIRouter(ENV_FILE)
START_TIME = time.time()


def _lookup_preset_sequence(uniprot_id: Optional[str]) -> Optional[Dict[str, Any]]:
    if not uniprot_id:
        return None
    uid = uniprot_id.strip().upper()
    for p in engine.presets:
        if p.get("uniprot_id", "").upper() == uid:
            return p
    return None


def _get_institution_config() -> InstitutionConfig:
    with db.get_session() as session:
        cfg = session.exec(select(InstitutionConfig).where(InstitutionConfig.id == 1)).first()
        if not cfg:
            cfg = InstitutionConfig(id=1)
            session.add(cfg)
            session.commit()
            session.refresh(cfg)
        return cfg


@app.get("/api/health")
async def health_check() -> Dict[str, Any]:
    cfg = _get_institution_config()
    return {
        "status": "healthy",
        "service": "ProteinLens-OS Backend",
        "version": "2.0.0",
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "ml_engine": {
            "backbone": engine.esm.model_name,
            "go_terms": len(engine.dag.top_terms),
            "training_proteins": int(engine.X_train.shape[0]),
            "real_3mer_trained": engine.baseline_3mer.is_real_trained,
        },
        "ai_router": ai_router.get_status(),
        "institution": cfg.model_dump(),
    }


@app.get("/api/presets")
async def get_presets() -> Dict[str, Any]:
    return {
        "proteins": engine.presets,
        "clinical_variants": CLINICAL_VARIANT_PRESETS,
        "teaching_labs": ACADEMIC_TEACHING_LABS,
    }


@app.post("/api/analyze/protein")
async def analyze_protein(req: AnalyzeProteinRequest) -> Dict[str, Any]:
    sequence = (req.sequence or "").strip()
    uniprot_id = req.uniprot_id.strip().upper() if req.uniprot_id else None
    protein_name = req.protein_name
    uniprot_evidence: Dict[str, Any] = {"available": False}
    opentargets_evidence: Dict[str, Any] = {"available": False}

    # Resolve sequence from preset or live UniProt if only UniProt ID provided
    preset = _lookup_preset_sequence(uniprot_id)
    if not sequence and preset:
        sequence = preset["sequence"]
        protein_name = protein_name or preset["name"]

    if uniprot_id and req.include_bio_evidence:
        uniprot_evidence = await bio_service.fetch_uniprot_entry(uniprot_id)
        if not sequence and uniprot_evidence.get("sequence"):
            sequence = uniprot_evidence["sequence"]
        if not protein_name and uniprot_evidence.get("protein_name"):
            protein_name = uniprot_evidence["protein_name"]
        if uniprot_evidence.get("ensembl_gene_id"):
            opentargets_evidence = await bio_service.fetch_opentargets_drugs(
                uniprot_evidence["ensembl_gene_id"]
            )

    if not sequence:
        raise HTTPException(
            status_code=400,
            detail="Provide either a valid amino acid sequence (FASTA) or a resolvable UniProt ID.",
        )

    try:
        analysis = engine.analyze_protein(
            sequence=sequence,
            uniprot_id=uniprot_id,
            min_confidence=req.min_confidence,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    clean_out = engine.strip_internal(analysis)
    clean_out["protein_name"] = protein_name or (preset["name"] if preset else uniprot_id or "Custom Protein")
    clean_out["bio_evidence"] = {
        "uniprot": uniprot_evidence,
        "open_targets": opentargets_evidence,
    }
    return clean_out


@app.post("/api/analyze/variant")
async def analyze_variant(req: AnalyzeVariantRequest) -> Dict[str, Any]:
    sequence = (req.sequence or "").strip()
    uniprot_id = req.uniprot_id.strip().upper() if req.uniprot_id else None
    gene_symbol = req.gene_symbol.strip().upper() if req.gene_symbol else None
    protein_name = req.protein_name

    preset = _lookup_preset_sequence(uniprot_id)
    if not sequence and preset:
        sequence = preset["sequence"]
        protein_name = protein_name or preset["name"]

    uniprot_evidence: Dict[str, Any] = {"available": False}
    clinvar_evidence: Dict[str, Any] = {"available": False, "matched": False, "records": []}
    opentargets_evidence: Dict[str, Any] = {"available": False, "drugs": []}

    if uniprot_id and req.include_bio_evidence:
        uniprot_evidence = await bio_service.fetch_uniprot_entry(uniprot_id)
        if not sequence and uniprot_evidence.get("sequence"):
            sequence = uniprot_evidence["sequence"]
        if not gene_symbol and uniprot_evidence.get("gene_symbol"):
            gene_symbol = uniprot_evidence["gene_symbol"]
        if not protein_name and uniprot_evidence.get("protein_name"):
            protein_name = uniprot_evidence["protein_name"]

    if not sequence:
        raise HTTPException(
            status_code=400,
            detail="Could not resolve sequence. Provide sequence or valid UniProt ID.",
        )

    try:
        result = engine.analyze_variant_and_pocket_dms(
            sequence=sequence,
            pos_1based=req.position,
            mut_aa=req.mut_aa,
            uniprot_id=uniprot_id,
            run_pocket_dms=req.run_pocket_dms,
            max_pocket_residues=req.max_pocket_residues,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # Run ClinVar + Open Targets concurrently
    if req.include_bio_evidence:
        tasks = [bio_service.fetch_clinvar_variant(gene_symbol, result["mutation"])]
        ensg = uniprot_evidence.get("ensembl_gene_id")
        if ensg:
            tasks.append(bio_service.fetch_opentargets_drugs(ensg))
        fetched = await asyncio.gather(*tasks, return_exceptions=True)
        if len(fetched) >= 1 and isinstance(fetched[0], dict):
            clinvar_evidence = fetched[0]
        if len(fetched) >= 2 and isinstance(fetched[1], dict):
            opentargets_evidence = fetched[1]

    # Attach WT PDB content if available so the variant studio can render 3D pocket immediately
    wt_full = engine.analyze_protein(sequence, uniprot_id=uniprot_id)
    result["protein_name"] = protein_name or (preset["name"] if preset else uniprot_id or "Custom Protein")
    result["gene_symbol"] = gene_symbol
    result["sequence_sha256"] = wt_full["sequence_sha256"]
    result["pdb_content"] = wt_full["structure"].get("pdb_content")
    result["bio_evidence"] = {
        "uniprot": uniprot_evidence,
        "clinvar": clinvar_evidence,
        "open_targets": opentargets_evidence,
    }
    return result


# ---------------------------------------------------------------------------
# Batch Patient Variant Cohort Triage (Background Queue + SSE Stream)
# ---------------------------------------------------------------------------
def _run_batch_job_sync(job_uid: str, items: List[Dict[str, Any]]) -> None:
    with db.get_session() as session:
        job = session.exec(select(BatchJob).where(BatchJob.job_uid == job_uid)).first()
        if not job:
            return
        job.status = "running"
        job.updated_at = utc_now_iso()
        session.add(job)
        session.commit()

    results: List[Dict[str, Any]] = []
    try:
        for idx, item in enumerate(items):
            seq = (item.get("sequence") or "").strip()
            uid = item.get("uniprot_id")
            if not seq and uid:
                preset = _lookup_preset_sequence(uid)
                if preset:
                    seq = preset["sequence"]
            if not seq:
                results.append({
                    "index": idx + 1,
                    "label": item.get("label") or f"{uid or 'Seq'} pos {item['position']}{item['mut_aa']}",
                    "status": "error",
                    "error": "Missing sequence for UniProt ID",
                })
            else:
                try:
                    vr = engine.analyze_variant_and_pocket_dms(
                        sequence=seq,
                        pos_1based=int(item["position"]),
                        mut_aa=str(item["mut_aa"]),
                        uniprot_id=uid,
                        run_pocket_dms=False,  # Fast single-site LLR + Delta-GO + 5A pocket for cohort triage
                    )
                    da = vr["dual_axis_assessment"]
                    sp = vr["structural_pocket"]
                    results.append({
                        "index": idx + 1,
                        "label": item.get("label") or f"{item.get('gene_symbol') or uid or 'Custom'} {vr['mutation']}",
                        "uniprot_id": uid,
                        "gene_symbol": item.get("gene_symbol"),
                        "mutation": vr["mutation"],
                        "position": vr["position"],
                        "mut_aa": vr["mut_aa"],
                        "composite_risk_score": da["composite_risk_score"],
                        "evolutionary_llr": da["evolutionary_llr"],
                        "fdi_score": da["fdi_score"],
                        "plddt": sp.get("target_plddt"),
                        "contacts_5A": sp.get("all_5A_contact_count", 0),
                        "risk_tier": da["risk_tier"],
                        "severity": da["severity"],
                        "acmg_cue": da["acmg_computational_cue"],
                        "latency_ms": vr["latency_ms"],
                        "status": "ok",
                    })
                except Exception as exc:
                    results.append({
                        "index": idx + 1,
                        "label": item.get("label") or f"Row {idx + 1}",
                        "status": "error",
                        "error": str(exc),
                    })

            # Rank valid rows highest risk first
            ranked = sorted(
                results,
                key=lambda r: r.get("composite_risk_score", -1.0),
                reverse=True,
            )
            with db.get_session() as session:
                job = session.exec(select(BatchJob).where(BatchJob.job_uid == job_uid)).first()
                if job:
                    job.completed_items = idx + 1
                    job.results_json = json.dumps(ranked)
                    job.updated_at = utc_now_iso()
                    session.add(job)
                    session.commit()

        with db.get_session() as session:
            job = session.exec(select(BatchJob).where(BatchJob.job_uid == job_uid)).first()
            if job:
                job.status = "completed"
                job.updated_at = utc_now_iso()
                session.add(job)
                session.commit()
    except Exception as exc:
        with db.get_session() as session:
            job = session.exec(select(BatchJob).where(BatchJob.job_uid == job_uid)).first()
            if job:
                job.status = "failed"
                job.error_message = str(exc)
                job.updated_at = utc_now_iso()
                session.add(job)
                session.commit()


@app.post("/api/analyze/batch")
async def start_batch_triage(req: BatchTriageRequest, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    job_uid = f"batch-{uuid.uuid4().hex[:10]}"
    items_raw = [it.model_dump() for it in req.items]

    # Pre-resolve live UniProt sequences if needed so sync worker has sequences ready
    for it in items_raw:
        if not it.get("sequence") and it.get("uniprot_id"):
            preset = _lookup_preset_sequence(it["uniprot_id"])
            if preset:
                it["sequence"] = preset["sequence"]
            else:
                uni = await bio_service.fetch_uniprot_entry(it["uniprot_id"])
                if uni.get("sequence"):
                    it["sequence"] = uni["sequence"]

    with db.get_session() as session:
        job = BatchJob(
            job_uid=job_uid,
            title=req.title,
            status="queued",
            total_items=len(items_raw),
            completed_items=0,
            results_json="[]",
        )
        session.add(job)
        session.commit()

    background_tasks.add_task(_run_batch_job_sync, job_uid, items_raw)
    return {"job_uid": job_uid, "status": "queued", "total_items": len(items_raw)}


@app.get("/api/jobs/{job_uid}")
async def get_batch_job(job_uid: str) -> Dict[str, Any]:
    with db.get_session() as session:
        job = session.exec(select(BatchJob).where(BatchJob.job_uid == job_uid)).first()
        if not job:
            raise HTTPException(status_code=404, detail="Batch job not found.")
        return {
            "job_uid": job.job_uid,
            "title": job.title,
            "status": job.status,
            "total_items": job.total_items,
            "completed_items": job.completed_items,
            "results": json.loads(job.results_json),
            "error_message": job.error_message,
            "created_at": job.created_at,
            "updated_at": job.updated_at,
        }


@app.get("/api/jobs/{job_uid}/stream")
async def stream_batch_job(job_uid: str):
    async def event_generator():
        while True:
            with db.get_session() as session:
                job = session.exec(select(BatchJob).where(BatchJob.job_uid == job_uid)).first()
                if not job:
                    yield {"event": "error", "data": json.dumps({"error": "Job not found"})}
                    return
                payload = {
                    "job_uid": job.job_uid,
                    "status": job.status,
                    "total_items": job.total_items,
                    "completed_items": job.completed_items,
                    "results": json.loads(job.results_json),
                }
                yield {"event": "progress", "data": json.dumps(payload)}
                if job.status in ("completed", "failed"):
                    return
            await asyncio.sleep(0.4)

    return EventSourceResponse(event_generator())


# ---------------------------------------------------------------------------
# Auto-Configuring Multi-Provider XAI Co-Pilot & Settings
# ---------------------------------------------------------------------------
@app.get("/api/settings/ai")
async def get_ai_settings() -> Dict[str, Any]:
    return ai_router.get_status()


@app.post("/api/settings/ai/models")
async def discover_ai_models(req: AIConfigRequest) -> Dict[str, Any]:
    return await ai_router.discover_models(
        provider=req.provider,
        api_key=req.api_key,
        ollama_url=req.ollama_url,
    )


@app.post("/api/settings/ai")
async def configure_ai_provider(req: AIConfigRequest) -> Dict[str, Any]:
    return await ai_router.configure_and_verify(
        api_key=req.api_key,
        provider=req.provider,
        model_name=req.model_name,
        ollama_url=req.ollama_url,
    )


@app.get("/api/settings/institution")
async def get_institution_settings() -> Dict[str, Any]:
    return _get_institution_config().model_dump()


@app.post("/api/settings/institution")
async def update_institution_settings(req: InstitutionUpdateRequest) -> Dict[str, Any]:
    with db.get_session() as session:
        cfg = session.exec(select(InstitutionConfig).where(InstitutionConfig.id == 1)).first()
        if not cfg:
            cfg = InstitutionConfig(id=1)
        cfg.institution_name = req.institution_name.strip() or "IIIT Nagpur — Computational Biology & AI Lab"
        cfg.department = req.department.strip()
        cfg.location = req.location.strip()
        cfg.report_disclaimer = req.report_disclaimer.strip()
        cfg.default_audience_mode = req.default_audience_mode
        cfg.updated_at = utc_now_iso()
        session.add(cfg)
        session.commit()
        session.refresh(cfg)
        return cfg.model_dump()


@app.post("/api/copilot/synthesize")
async def synthesize_copilot(req: CopilotSynthesizeRequest) -> Dict[str, Any]:
    cfg = _get_institution_config()
    return await ai_router.synthesize_xai_explanation(
        evidence_packet=req.evidence_packet,
        audience_mode=req.audience_mode,
        institution_name=cfg.institution_name,
    )


# ---------------------------------------------------------------------------
# Persistent Clinical & Research Cases (SQLite) + Audit Export
# ---------------------------------------------------------------------------
@app.get("/api/cases")
async def list_cases() -> List[Dict[str, Any]]:
    with db.get_session() as session:
        rows = session.exec(select(ClinicalCase).order_by(ClinicalCase.id.desc())).all()
        return [
            {
                "id": r.id,
                "case_code": r.case_code,
                "title": r.title,
                "protein_name": r.protein_name,
                "uniprot_id": r.uniprot_id,
                "gene_symbol": r.gene_symbol,
                "mutation": r.mutation,
                "composite_risk_score": r.composite_risk_score,
                "evolutionary_llr": r.evolutionary_llr,
                "risk_tier": r.risk_tier,
                "sequence_sha256": r.sequence_sha256,
                "clinician_notes": r.clinician_notes,
                "mode": r.mode,
                "created_at": r.created_at,
            }
            for r in rows
        ]


@app.get("/api/cases/{case_id}")
async def get_case_detail(case_id: int) -> Dict[str, Any]:
    with db.get_session() as session:
        row = session.get(ClinicalCase, case_id)
        if not row:
            raise HTTPException(status_code=404, detail="Case not found.")
        return {
            "id": row.id,
            "case_code": row.case_code,
            "title": row.title,
            "protein_name": row.protein_name,
            "uniprot_id": row.uniprot_id,
            "gene_symbol": row.gene_symbol,
            "mutation": row.mutation,
            "composite_risk_score": row.composite_risk_score,
            "evolutionary_llr": row.evolutionary_llr,
            "risk_tier": row.risk_tier,
            "sequence_sha256": row.sequence_sha256,
            "clinician_notes": row.clinician_notes,
            "mode": row.mode,
            "created_at": row.created_at,
            "payload": json.loads(row.payload_json),
        }


@app.post("/api/cases")
async def create_case(req: SaveCaseRequest) -> Dict[str, Any]:
    case_code = f"PLOS-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:5].upper()}"
    # Strip bulky raw PDB text before storing in SQLite
    slim_payload = {k: v for k, v in req.payload.items() if k != "pdb_content"}
    if "structure" in slim_payload and isinstance(slim_payload["structure"], dict):
        slim_payload["structure"] = {
            k: v for k, v in slim_payload["structure"].items() if k != "pdb_content"
        }

    with db.get_session() as session:
        case = ClinicalCase(
            case_code=case_code,
            title=req.title,
            protein_name=req.protein_name,
            uniprot_id=req.uniprot_id,
            gene_symbol=req.gene_symbol,
            mutation=req.mutation,
            composite_risk_score=req.composite_risk_score,
            evolutionary_llr=req.evolutionary_llr,
            risk_tier=req.risk_tier,
            sequence_sha256=req.sequence_sha256,
            clinician_notes=req.clinician_notes,
            mode=req.mode,
            payload_json=json.dumps(slim_payload),
        )
        session.add(case)
        session.commit()
        session.refresh(case)
        return {"id": case.id, "case_code": case.case_code, "created_at": case.created_at}


@app.patch("/api/cases/{case_id}/notes")
async def update_case_notes(case_id: int, req: UpdateCaseNotesRequest) -> Dict[str, Any]:
    with db.get_session() as session:
        row = session.get(ClinicalCase, case_id)
        if not row:
            raise HTTPException(status_code=404, detail="Case not found.")
        row.clinician_notes = req.clinician_notes
        session.add(row)
        session.commit()
        return {"id": row.id, "clinician_notes": row.clinician_notes}


@app.delete("/api/cases/{case_id}")
async def delete_case(case_id: int) -> Dict[str, Any]:
    with db.get_session() as session:
        row = session.get(ClinicalCase, case_id)
        if not row:
            raise HTTPException(status_code=404, detail="Case not found.")
        session.delete(row)
        session.commit()
        return {"deleted": True, "id": case_id}


@app.get("/api/export/{case_id}")
async def export_case(case_id: int, fmt: str = Query(default="json", pattern="^(json|csv)$")):
    cfg = _get_institution_config()
    with db.get_session() as session:
        row = session.get(ClinicalCase, case_id)
        if not row:
            raise HTTPException(status_code=404, detail="Case not found.")
        payload = json.loads(row.payload_json)

    dossier = {
        "schema_version": "ProteinLens-OS-2.0",
        "exported_at_utc": utc_now_iso(),
        "institution": cfg.model_dump(),
        "case": {
            "case_code": row.case_code,
            "title": row.title,
            "protein_name": row.protein_name,
            "uniprot_id": row.uniprot_id,
            "gene_symbol": row.gene_symbol,
            "mutation": row.mutation,
            "composite_risk_score": row.composite_risk_score,
            "evolutionary_llr": row.evolutionary_llr,
            "risk_tier": row.risk_tier,
            "sequence_sha256": row.sequence_sha256,
            "clinician_notes": row.clinician_notes,
            "created_at": row.created_at,
        },
        "analysis": payload,
    }
    dossier_bytes = json.dumps(dossier, sort_keys=True).encode("utf-8")
    dossier["provenance_sha256"] = hashlib.sha256(dossier_bytes).hexdigest()

    if fmt == "json":
        return JSONResponse(
            content=dossier,
            headers={"Content-Disposition": f'attachment; filename="{row.case_code}_dossier.json"'},
        )

    # CSV export of GO terms or variant lost/gained matrix
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["CaseCode", "Institution", "Protein", "Mutation", "Category", "GO_Term", "Name", "Score_or_Delta", "IA_Weight"])
    categorized = payload.get("categorized")
    if isinstance(categorized, dict):
        for asp in ("MF", "BP", "CC"):
            for item in categorized.get(asp, []):
                writer.writerow([
                    row.case_code, cfg.institution_name, row.protein_name, row.mutation or "WT",
                    asp, item.get("term"), item.get("name"), item.get("score"), item.get("ia"),
                ])
    elif isinstance(payload.get("go_disruption"), dict):
        gd = payload["go_disruption"]
        for item in gd.get("lost_functions", []):
            writer.writerow([
                row.case_code, cfg.institution_name, row.protein_name, row.mutation,
                "LOST_" + item.get("aspect", ""), item.get("term"), item.get("name"), item.get("delta"), item.get("ia"),
            ])
        for item in gd.get("gained_functions", []):
            writer.writerow([
                row.case_code, cfg.institution_name, row.protein_name, row.mutation,
                "GAINED_" + item.get("aspect", ""), item.get("term"), item.get("name"), item.get("delta"), item.get("ia"),
            ])

    return PlainTextResponse(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{row.case_code}_matrix.csv"'},
    )


# ---------------------------------------------------------------------------
# Institutional Admin Telemetry & Reproducible Benchmarks Endpoint
# ---------------------------------------------------------------------------
@app.get("/api/admin/telemetry")
async def get_admin_telemetry() -> Dict[str, Any]:
    with db.get_session() as session:
        case_count = len(session.exec(select(ClinicalCase)).all())
        batch_count = len(session.exec(select(BatchJob)).all())
    cfg = _get_institution_config()
    runs = engine.telemetry["protein_runs"] + engine.telemetry["variant_runs"]
    avg_ms = round(engine.telemetry["total_latency_ms"] / max(runs, 1), 2)
    cache_rate = round(
        100.0 * engine.telemetry["cache_hits"] / max(runs + engine.telemetry["cache_hits"], 1), 1
    )

    # Check if research benchmark results exist on disk
    bench_summary = None
    bench_file = BACKEND_ROOT.parent / "benchmarks" / "output" / "benchmark_summary.json"
    if bench_file.exists():
        try:
            bench_summary = json.loads(bench_file.read_text(encoding="utf-8"))
        except Exception:
            pass

    return {
        "institution": cfg.model_dump(),
        "ai_router": ai_router.get_status(),
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "saved_cases": case_count,
        "batch_jobs": batch_count,
        "engine_metrics": {
            **engine.telemetry,
            "avg_latency_ms": avg_ms,
            "cache_hit_rate_pct": cache_rate,
            "real_3mer_trained": engine.baseline_3mer.is_real_trained,
        },
        "benchmark_summary": bench_summary,
    }
