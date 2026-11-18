"""
ProteinLens-OS Unified Scientific ML Engine
Orchestrates all 6 independent, non-hardcoded ML & structural modules:
1. Single-load EsmForMaskedLM (320-d embeddings, Attention Rollout, Masked-Marginal LLR, Pocket DMS)
2. Real 8,000-d Sparse 3-mer kNN Baseline
3. ESM2 Cosine kNN Homology Predictor
4. Trained PyTorch Multi-Label MLP (500 GO Terms)
5. Exact Fixed-Point True Path DAG Engine + IA-Weighted Delta-GO
6. 3D AlphaFold Structural Pocket Engine (pLDDT + 5 A contact shell + Dual-Axis Risk Fusion)
"""

from __future__ import annotations

import hashlib
import json
import math
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
import torch
import torch.nn as nn

from .baseline_3mer import Real3MerBaseline
from .dag_engine import DAGEngine
from .esm_service import CANONICAL_AAS, ESM2Service
from .structure_service import StructureService


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-max(-20.0, min(20.0, x))))


# Standard NCBI BLOSUM62 log-odds substitution matrix (Henikoff & Henikoff, PNAS 1992)
_BLOSUM62_ORDER = "ARNDCQEGHILKMFPSTWYV"
_BLOSUM62_ROWS = [
    [ 4,-1,-2,-2, 0,-1,-1, 0,-2,-1,-1,-1,-1,-2,-1, 1, 0,-3,-2, 0],
    [-1, 5, 0,-2,-3, 1, 0,-2, 0,-3,-2, 2,-1,-3,-2,-1,-1,-3,-2,-3],
    [-2, 0, 6, 1,-3, 0, 0, 0, 1,-3,-3, 0,-2,-3,-2, 1, 0,-4,-2,-3],
    [-2,-2, 1, 6,-3, 0, 2,-1,-1,-3,-4,-1,-3,-3,-1, 0,-1,-4,-3,-3],
    [ 0,-3,-3,-3, 9,-3,-4,-3,-3,-1,-1,-3,-1,-2,-3,-1,-1,-2,-2,-1],
    [-1, 1, 0, 0,-3, 5, 2,-2, 0,-3,-2, 1, 0,-3,-1, 0,-1,-2,-1,-2],
    [-1, 0, 0, 2,-4, 2, 5,-2, 0,-3,-3, 1,-2,-3,-1, 0,-1,-3,-2,-2],
    [ 0,-2, 0,-1,-3,-2,-2, 6,-2,-4,-4,-2,-3,-3,-2, 0,-2,-2,-3,-3],
    [-2, 0, 1,-1,-3, 0, 0,-2, 8,-3,-3,-1,-2,-1,-2,-1,-2,-2, 2,-3],
    [-1,-3,-3,-3,-1,-3,-3,-4,-3, 4, 2,-3, 1, 0,-3,-2,-1,-3,-1, 3],
    [-1,-2,-3,-4,-1,-2,-3,-4,-3, 2, 4,-2, 2, 0,-3,-2,-1,-2,-1, 1],
    [-1, 2, 0,-1,-3, 1, 1,-2,-1,-3,-2, 5,-1,-3,-1, 0,-1,-3,-2,-2],
    [-1,-1,-2,-3,-1, 0,-2,-3,-2, 1, 2,-1, 5, 0,-2,-1,-1,-1,-1, 1],
    [-2,-3,-3,-3,-2,-3,-3,-3,-1, 0, 0,-3, 0, 6,-4,-2,-2, 1, 3,-1],
    [-1,-2,-2,-1,-3,-1,-1,-2,-2,-3,-3,-1,-2,-4, 7,-1,-1,-4,-3,-2],
    [ 1,-1, 1, 0,-1, 0, 0, 0,-1,-2,-2, 0,-1,-2,-1, 4, 1,-3,-2,-2],
    [ 0,-1, 0,-1,-1,-1,-1,-2,-2,-1,-1,-1,-1,-2,-1, 1, 5,-2,-2, 0],
    [-3,-3,-4,-4,-2,-2,-3,-2,-2,-3,-2,-3,-1, 1,-4,-3,-2,11, 2,-3],
    [-2,-2,-2,-3,-2,-1,-2,-3, 2,-1,-1,-2,-1, 3,-3,-2,-2, 2, 7,-1],
    [ 0,-3,-3,-3,-1,-2,-2,-3,-3, 3, 1,-2, 1,-1,-2,-2, 0,-3,-1, 4],
]
_BLOSUM62_IDX = {aa: i for i, aa in enumerate(_BLOSUM62_ORDER)}


def blosum62_radicality(wt: str, mut: str) -> float:
    """Normalized physicochemical radicality in [0, 1] derived from BLOSUM62."""
    if wt == mut:
        return 0.0
    i, j = _BLOSUM62_IDX.get(wt), _BLOSUM62_IDX.get(mut)
    if i is None or j is None:
        return 0.5
    score = _BLOSUM62_ROWS[i][j]  # ranges from -4 (most radical) to +3 (conservative)
    return max(0.0, min(1.0, (2.0 - score) / 6.0))


class ProteinLensScientificEngine:
    def __init__(self, assets_dir: Path):
        self.assets_dir = assets_dir
        self.esm = ESM2Service("facebook/esm2_t6_8M_UR50D")
        self.structure = StructureService(assets_dir / "pdbs")

        # Load metadata & DAG engine
        meta_path = assets_dir / "model_metadata.json"
        with open(meta_path, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)
        self.dag = DAGEngine(self.metadata)

        # Load trained PyTorch MLP
        weights_path = assets_dir / "mlp_weights.pt"
        checkpoint = torch.load(weights_path, map_location="cpu", weights_only=False)
        self.mlp_mu = np.asarray(checkpoint["mu"], dtype=np.float32)
        self.mlp_sd = np.asarray(checkpoint["sd"], dtype=np.float32)
        in_dim = int(checkpoint["in_dim"])
        out_dim = int(checkpoint["out_dim"])

        self.mlp_model = nn.Sequential(
            nn.Linear(in_dim, 512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, out_dim),
        )
        self.mlp_model.load_state_dict(checkpoint["model_state_dict"])
        self.mlp_model.eval()

        # Load 2,000 training embeddings & ground-truth GO labels
        self.X_train = np.load(assets_dir / "train_embeddings.npy").astype(np.float32)
        self.Y_train = np.load(assets_dir / "train_labels.npy").astype(np.float32)
        self.X_train_norm = self.X_train / np.maximum(
            np.linalg.norm(self.X_train, axis=1, keepdims=True), 1e-9
        )
        self.freq_prior = self.Y_train.mean(axis=0).astype(np.float32)

        # Real 3-mer baseline
        self.baseline_3mer = Real3MerBaseline(assets_dir, self.Y_train)

        # Load curated presets
        presets_path = assets_dir / "presets.json"
        self.presets: List[Dict[str, Any]] = []
        if presets_path.exists():
            with open(presets_path, "r", encoding="utf-8") as f:
                self.presets = json.load(f)

        # Runtime caches & telemetry
        self._protein_cache: Dict[str, Dict[str, Any]] = {}
        self.telemetry = {
            "protein_runs": 0,
            "variant_runs": 0,
            "dms_runs": 0,
            "cache_hits": 0,
            "total_latency_ms": 0.0,
        }

    def predict_mlp(self, embedding: np.ndarray) -> np.ndarray:
        x_norm = (embedding - self.mlp_mu) / self.mlp_sd
        with torch.no_grad():
            t_in = torch.tensor(x_norm[None, :], dtype=torch.float32)
            probs = torch.sigmoid(self.mlp_model(t_in)).cpu().numpy()[0]
        return probs.astype(np.float32)

    def predict_knn(self, embedding: np.ndarray, k: int = 10) -> np.ndarray:
        q_norm = embedding / max(float(np.linalg.norm(embedding)), 1e-9)
        sims = self.X_train_norm @ q_norm
        k_eff = min(k, len(sims))
        top_idx = np.argpartition(-sims, k_eff)[:k_eff]
        weights = np.clip(sims[top_idx], 0.0, 1.0) ** 3
        denom = float(weights.sum()) + 1e-9
        return ((weights[:, None] * self.Y_train[top_idx]).sum(axis=0) / denom).astype(np.float32)

    def analyze_protein(
        self,
        sequence: str,
        uniprot_id: Optional[str] = None,
        min_confidence: float = 0.20,
    ) -> Dict[str, Any]:
        """
        Full multi-modal protein analysis:
        - ESM2 embedding + Multi-layer Attention Rollout Saliency
        - 4-Paradigm Model Arena (Frequency Prior, Real 3-mer kNN, ESM2 kNN, PyTorch MLP, Ensemble)
        - Fixed-Point True Path Rule DAG Propagation + React Flow JSON (MF/BP/CC)
        - AlphaFold PDB + per-residue pLDDT structural profile
        """
        t0 = time.perf_counter()
        clean_seq = self.esm.clean_sequence(sequence, maxlen=512)
        if not clean_seq:
            raise ValueError("Empty or invalid amino acid sequence.")

        seq_hash = hashlib.sha256(clean_seq.encode("utf-8")).hexdigest()
        cache_key = f"{seq_hash}:{uniprot_id or 'none'}"

        if cache_key in self._protein_cache:
            self.telemetry["cache_hits"] += 1
            cached = dict(self._protein_cache[cache_key])
            cached["cached"] = True
            cached["latency_ms"] = round((time.perf_counter() - t0) * 1000.0, 2)
            return cached

        # 1. ESM2 Embedding + Attention Rollout Saliency
        esm_out = self.esm.embed_and_saliency(clean_seq)
        emb = esm_out["embedding"]

        # 2. Multi-Model Inference (with individual timing for Model Arena)
        t_3m = time.perf_counter()
        p_3mer = self.baseline_3mer.predict(clean_seq)
        ms_3mer = round((time.perf_counter() - t_3m) * 1000.0, 2)

        t_knn = time.perf_counter()
        p_knn = self.predict_knn(emb)
        ms_knn = round((time.perf_counter() - t_knn) * 1000.0, 2)

        t_mlp = time.perf_counter()
        p_mlp = self.predict_mlp(emb)
        ms_mlp = round((time.perf_counter() - t_mlp) * 1000.0, 2)

        p_blend = (0.5 * p_mlp + 0.5 * p_knn).astype(np.float32)

        # 3. Exact True Path Rule DAG Propagation
        t_dag = time.perf_counter()
        p_prop, dag_audit = self.dag.propagate_true_path(p_blend)
        ms_dag = round((time.perf_counter() - t_dag) * 1000.0, 2)

        categorized = self.dag.categorize_predictions(p_blend, p_prop, min_score=0.05)

        # Interactive React Flow DAG payloads for all 3 sub-ontologies
        dags = {
            asp: self.dag.build_react_flow_dag(p_blend, p_prop, aspect=asp, min_conf=min_confidence)
            for asp in ("MF", "BP", "CC")
        }

        # 4. Model Arena comparative top terms
        top_indices = np.argsort(-p_prop)[:15]
        arena_rows = []
        for idx in top_indices:
            term = self.dag.top_terms[idx]
            arena_rows.append({
                "term": term,
                "name": self.dag.term_names.get(term, term),
                "aspect": self.dag.term_aspects.get(term, "MF"),
                "ia_weight": round(float(self.dag.ia_vector[idx]), 3),
                "prior": round(float(self.freq_prior[idx]), 4),
                "kmer_3": round(float(p_3mer[idx]), 4),
                "esm2_knn": round(float(p_knn[idx]), 4),
                "esm2_mlp": round(float(p_mlp[idx]), 4),
                "ensemble_raw": round(float(p_blend[idx]), 4),
                "true_path_final": round(float(p_prop[idx]), 4),
            })

        # 5. AlphaFold 3D Structure & pLDDT profile
        pdb_text, resolved_af_id, is_exact_pdb = self.structure.fetch_alphafold_pdb(uniprot_id)
        structure_summary: Dict[str, Any] = {
            "available": False,
            "alphafold_id": resolved_af_id,
            "is_exact_match": is_exact_pdb,
            "mean_plddt": None,
            "confidence_bands": None,
            "plddt_profile": [],
            "pdb_content": None,
        }
        if pdb_text:
            parsed = self.structure.parse_pdb_structure(pdb_text, cache_key=resolved_af_id)
            structure_summary = {
                "available": True,
                "alphafold_id": resolved_af_id,
                "is_exact_match": is_exact_pdb,
                "mean_plddt": parsed["mean_plddt"],
                "num_residues_3d": parsed["num_residues"],
                "confidence_bands": parsed["confidence_bands"],
                "plddt_profile": parsed["plddt_profile"][:512],
                "pdb_content": pdb_text,
            }

        # Build aligned per-residue dual-track profile (Saliency + pLDDT)
        plddt_map = {
            row["position"]: row["plddt"] for row in structure_summary["plddt_profile"]
        }
        residue_profile = [
            {
                "position": i + 1,
                "aa": clean_seq[i],
                "saliency": esm_out["saliency_scores"][i],
                "plddt": plddt_map.get(i + 1, None),
                "is_hotspot": (i + 1) in esm_out["hotspot_indices"],
            }
            for i in range(len(clean_seq))
        ]

        elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        self.telemetry["protein_runs"] += 1
        self.telemetry["total_latency_ms"] += elapsed_ms

        result = {
            "sequence": clean_seq,
            "sequence_length": len(clean_seq),
            "est_mass_kda": round(len(clean_seq) * 0.11, 2),
            "sequence_sha256": seq_hash,
            "uniprot_id": uniprot_id,
            "cached": False,
            "latency_ms": elapsed_ms,
            "model_metadata": {
                "backbone": self.esm.model_name,
                "real_3mer_trained": self.baseline_3mer.is_real_trained,
                "num_go_terms": len(self.dag.top_terms),
                "training_proteins": int(self.X_train.shape[0]),
            },
            "categorized": categorized,
            "summary_counts": {
                "MF": sum(1 for x in categorized["MF"] if x["score"] >= min_confidence),
                "BP": sum(1 for x in categorized["BP"] if x["score"] >= min_confidence),
                "CC": sum(1 for x in categorized["CC"] if x["score"] >= min_confidence),
                "total_active": sum(
                    1
                    for asp in ("MF", "BP", "CC")
                    for x in categorized[asp]
                    if x["score"] >= min_confidence
                ),
            },
            "dag_audit": dag_audit,
            "dags": dags,
            "xai": {
                "method": "Multi-Layer ESM2 Attention Rollout (70%) + Activation Norm (30%)",
                "mean_saliency": esm_out["mean_saliency"],
                "hotspot_count": len(esm_out["hotspot_indices"]),
                "hotspot_indices": esm_out["hotspot_indices"],
                "top_hotspots": esm_out["top_hotspots"][:15],
                "residue_profile": residue_profile,
            },
            "model_arena": {
                "rows": arena_rows,
                "timings_ms": {
                    "kmer_3": ms_3mer,
                    "esm2_knn": ms_knn,
                    "esm2_mlp": ms_mlp,
                    "dag_propagation": ms_dag,
                },
            },
            "structure": structure_summary,
            # Internal arrays stored only in memory cache for fast downstream variant diffs
            "_internal": {
                "embedding": emb,
                "p_propagated": p_prop,
                "pdb_text": pdb_text,
            },
        }
        self._protein_cache[cache_key] = result
        return result

    def analyze_variant_and_pocket_dms(
        self,
        sequence: str,
        pos_1based: int,
        mut_aa: str,
        uniprot_id: Optional[str] = None,
        run_pocket_dms: bool = True,
        max_pocket_residues: int = 8,
    ) -> Dict[str, Any]:
        """
        Flagship Differentiated Pipeline:
        1. Wild-type vs. Mutant ESM2 + MLP/kNN + True Path DAG differential inference (Delta-GO_IA)
        2. Exact Zero-Shot ESM2 Masked-Marginal LLR at target position
        3. Real 3D AlphaFold 5 A Spatial Pocket extraction (pLDDT + burial contacts)
        4. Batched 3D-Pocket Zero-Shot Deep Mutational Scanning (Pocket Residues x 20 AAs)
        5. Auditable Dual-Axis Clinical Risk Fusion Score
        """
        t0 = time.perf_counter()
        clean_seq = self.esm.clean_sequence(sequence, maxlen=512)
        if not clean_seq:
            raise ValueError("Invalid amino acid sequence.")
        if pos_1based < 1 or pos_1based > len(clean_seq):
            raise ValueError(f"Position {pos_1based} out of sequence range [1, {len(clean_seq)}].")

        mut_aa = mut_aa.strip().upper()
        if mut_aa not in CANONICAL_AAS:
            raise ValueError(f"Invalid target amino acid '{mut_aa}'. Must be one of 20 canonical AAs.")

        wt_aa = clean_seq[pos_1based - 1]
        mutation_label = f"{wt_aa}{pos_1based}{mut_aa}"

        # 1. Wild-type analysis (reuses cache in ~0 ms if already analyzed!)
        wt_full = self.analyze_protein(clean_seq, uniprot_id=uniprot_id)
        wt_internal = wt_full["_internal"]
        wt_emb = wt_internal["embedding"]
        wt_prop = wt_internal["p_propagated"]
        pdb_text = wt_internal["pdb_text"]

        # 2. Mutated sequence inference for Delta-GO_IA & cosine embedding shift
        mut_seq = clean_seq[: pos_1based - 1] + mut_aa + clean_seq[pos_1based:]
        mut_esm = self.esm.embed_and_saliency(mut_seq)
        mut_emb = mut_esm["embedding"]
        mut_blend = 0.5 * self.predict_mlp(mut_emb) + 0.5 * self.predict_knn(mut_emb)
        mut_prop, mut_dag_audit = self.dag.propagate_true_path(mut_blend)

        cos_sim = float(
            np.dot(wt_emb, mut_emb)
            / (max(float(np.linalg.norm(wt_emb)), 1e-9) * max(float(np.linalg.norm(mut_emb)), 1e-9))
        )
        embedding_shift = round(max(0.0, 1.0 - cos_sim), 6)

        go_disruption = self.dag.compute_ia_disruption(wt_prop, mut_prop)

        # 3. 3D Structural Pocket (5 A heavy-atom contact shell & 8 A burial)
        pocket = self.structure.extract_spatial_pocket(
            pdb_text,
            target_pos=pos_1based,
            pocket_radius=5.0,
            burial_radius=8.0,
            max_pocket_residues=max_pocket_residues,
            cache_key=wt_full["structure"].get("alphafold_id"),
        )

        # 4. Zero-Shot ESM2 Masked-Marginal LLR + Batched 3D Pocket DMS Heatmap
        if run_pocket_dms:
            scan_positions = [p for p in pocket["pocket_positions"] if 1 <= p <= len(clean_seq)]
            if pos_1based not in scan_positions:
                scan_positions = [pos_1based] + scan_positions
            # If no 3D structure exists, scan local +/- 3 residue sequence window
            if len(scan_positions) == 1:
                lo = max(1, pos_1based - 3)
                hi = min(len(clean_seq), pos_1based + 3)
                scan_positions = [pos_1based] + [p for p in range(lo, hi + 1) if p != pos_1based]
            scan_positions = scan_positions[:max_pocket_residues]
            self.telemetry["dms_runs"] += 1
        else:
            scan_positions = [pos_1based]

        dms_map = self.esm.compute_position_aa_llrs(clean_seq, scan_positions)
        target_llr_data = dms_map.get(pos_1based, {})
        llr_score = float(target_llr_data.get("aa_llr", {}).get(mut_aa, 0.0))
        if wt_aa == mut_aa:
            llr_score = 0.0

        # Build structured 3D-Pocket DMS matrix for frontend heatmap
        pocket_dist_map = {
            n["position"]: n["distance_angstrom"] for n in pocket.get("pocket_residues", [])
        }
        pocket_plddt_map = {
            n["position"]: n["plddt"] for n in pocket.get("pocket_residues", [])
        }
        if pocket.get("target_plddt") is not None:
            pocket_plddt_map[pos_1based] = pocket["target_plddt"]

        dms_rows = []
        rescue_candidates = []
        fragile_hotspots = []
        for pos in scan_positions:
            p_info = dms_map.get(pos)
            if not p_info:
                continue
            row = {
                "position": pos,
                "wt_aa": p_info["wt_aa"],
                "is_target": pos == pos_1based,
                "distance_angstrom": 0.0 if pos == pos_1based else pocket_dist_map.get(pos, None),
                "plddt": pocket_plddt_map.get(pos, None),
                "conservation": p_info["conservation"],
                "scores": p_info["aa_llr"],
                "best_tolerated": p_info["best_tolerated"],
                "most_damaging": p_info["most_damaging"],
            }
            dms_rows.append(row)
            # Track top tolerated/stabilizing substitutions across the pocket
            for cand in p_info["best_tolerated"]:
                if cand["llr"] >= -0.25:
                    rescue_candidates.append({
                        "mutation": f"{p_info['wt_aa']}{pos}{cand['aa']}",
                        "position": pos,
                        "wt_aa": p_info["wt_aa"],
                        "alt_aa": cand["aa"],
                        "llr": cand["llr"],
                        "is_target_site": pos == pos_1based,
                        "distance_angstrom": row["distance_angstrom"],
                    })
            if p_info["most_damaging"]:
                worst = p_info["most_damaging"][0]
                fragile_hotspots.append({
                    "mutation": f"{p_info['wt_aa']}{pos}{worst['aa']}",
                    "position": pos,
                    "llr": worst["llr"],
                    "conservation": p_info["conservation"],
                })

        rescue_candidates.sort(key=lambda x: x["llr"], reverse=True)
        fragile_hotspots.sort(key=lambda x: x["llr"])

        # 5. Auditable Multi-Modal Clinical Risk Fusion Score (0 .. 100)
        # Combines:
        #   a) Evolutionary intolerance: calibrated 8M-scale ESM2 Masked-Marginal LLR + BLOSUM62 radicality
        #   b) 3D AlphaFold Structural Microenvironment: pLDDT order + 8 A core burial + 5 A contact density
        #   c) Hierarchical Functional Shift: IA-weighted Delta-GO_IA + cosine embedding shift
        evo_llr_risk = 0.0 if wt_aa == mut_aa else _sigmoid((-llr_score - 0.85) / 1.15)
        blosum_risk = blosum62_radicality(wt_aa, mut_aa)
        evo_risk = 0.55 * evo_llr_risk + 0.45 * blosum_risk

        go_risk = min(1.0, go_disruption["fdi_normalized"] * 3.5 + embedding_shift * 12.0)

        plddt_val = pocket.get("target_plddt")
        if plddt_val is not None:
            # Structured core (pLDDT > 80) carries much higher folding sensitivity than disordered loops (< 55)
            plddt_order_risk = _sigmoid((plddt_val - 72.0) / 11.0)
            contact_risk = min(1.0, (pocket.get("burial_contacts_8A", 0) / 11.0))
            struct_risk = 0.65 * plddt_order_risk + 0.35 * contact_risk
        else:
            struct_risk = float(pocket.get("burial_score", 0.5))

        if wt_aa == mut_aa:
            composite_risk = 0.0
        else:
            # Structural context gates evolutionary damage (mutations in disordered loops are far more tolerated)
            composite_risk = round(
                100.0 * (0.42 * evo_risk + 0.43 * struct_risk + 0.15 * go_risk), 2
            )

        if wt_aa == mut_aa:
            risk_tier = "Synonymous / Wild-Type (No Change)"
            acmg_hint = "Benign (Synonymous)"
            severity = "benign"
        elif composite_risk >= 68.0 or (llr_score <= -3.5 and struct_risk >= 0.6):
            risk_tier = "Pathogenic / High Structural & Evolutionary Disruption"
            acmg_hint = "PP3_Strong (Deleterious Core / Active-Site Disruption)"
            severity = "pathogenic"
        elif composite_risk >= 52.0:
            risk_tier = "Likely Pathogenic / Moderate-High Perturbation"
            acmg_hint = "PP3_Moderate (Structured Domain Intolerance)"
            severity = "likely_pathogenic"
        elif composite_risk >= 36.0:
            risk_tier = "VUS — Borderline Functional Sensitivity"
            acmg_hint = "PM2/PP3 Uncertain — Prioritize Functional Assay"
            severity = "vus"
        else:
            risk_tier = "Likely Benign / Evolutionarily Tolerated"
            acmg_hint = "BP4_Supporting (Tolerated / Disordered Context)"
            severity = "benign"

        elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        self.telemetry["variant_runs"] += 1
        self.telemetry["total_latency_ms"] += elapsed_ms

        return {
            "mutation": mutation_label,
            "position": pos_1based,
            "wt_aa": wt_aa,
            "mut_aa": mut_aa,
            "uniprot_id": uniprot_id,
            "latency_ms": elapsed_ms,
            "dual_axis_assessment": {
                "composite_risk_score": composite_risk,
                "risk_tier": risk_tier,
                "severity": severity,
                "acmg_computational_cue": acmg_hint,
                "evolutionary_llr": round(llr_score, 4),
                "evolutionary_risk_component": round(evo_risk * 100.0, 2),
                "functional_go_risk_component": round(go_risk * 100.0, 2),
                "structural_burial_component": round(struct_risk * 100.0, 2),
                "conservation_index": target_llr_data.get("conservation", 0.0),
                "wt_marginal_prob": target_llr_data.get("wt_prob", 0.0),
                "embedding_cosine_shift": embedding_shift,
                "fdi_score": go_disruption["fdi_score"],
            },
            "go_disruption": {
                **go_disruption,
                "mut_dag_violations_after": mut_dag_audit["violations_after"],
            },
            "structural_pocket": pocket,
            "pocket_dms": {
                "amino_acids": CANONICAL_AAS,
                "rows": dms_rows,
                "rescue_or_tolerated_candidates": rescue_candidates[:8],
                "most_fragile_pocket_mutations": fragile_hotspots[:6],
            },
            "wt_summary": {
                "sequence_length": wt_full["sequence_length"],
                "alphafold_id": wt_full["structure"].get("alphafold_id"),
                "mean_plddt": wt_full["structure"].get("mean_plddt"),
            },
        }

    def strip_internal(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {k: v for k, v in payload.items() if k != "_internal"}
