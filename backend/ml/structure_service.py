"""
ProteinLens-OS 3D Structural Microenvironment Engine
Parses AlphaFold PDB atomic coordinates to extract:
1. Per-residue pLDDT structural confidence (from PDB B-factor column)
2. 3D Euclidean contact shell (5.0 A active pocket & 8.0 A burial density)
3. AlphaFold DB live fetching with persistent local PDB caching
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import requests


AA3_TO_1 = {
    "ALA": "A", "CYS": "C", "ASP": "D", "GLU": "E", "PHE": "F",
    "GLY": "G", "HIS": "H", "ILE": "I", "LYS": "K", "LEU": "L",
    "MET": "M", "ASN": "N", "PRO": "P", "GLN": "Q", "ARG": "R",
    "SER": "S", "THR": "T", "VAL": "V", "TRP": "W", "TYR": "Y",
}


class StructureService:
    def __init__(self, pdbs_dir: Path):
        self.pdbs_dir = pdbs_dir
        self.pdbs_dir.mkdir(parents=True, exist_ok=True)
        self._parsed_cache: Dict[str, Dict[str, Any]] = {}

    def fetch_alphafold_pdb(self, identifier: Optional[str]) -> Tuple[Optional[str], Optional[str], bool]:
        """
        Fetch 3D PDB structure from local cache or live AlphaFold EBI API.
        Returns (pdb_text, resolved_af_id, is_exact_match).
        """
        if not identifier or not identifier.strip():
            return None, None, False

        clean_id = identifier.strip().upper()
        if clean_id.startswith("AF-") and "-" in clean_id[3:]:
            uniprot_id = clean_id.split("-")[1]
        else:
            uniprot_id = clean_id

        local_pdb = self.pdbs_dir / f"{uniprot_id}.pdb"
        if local_pdb.exists():
            try:
                content = local_pdb.read_text(encoding="utf-8", errors="ignore")
                if len(content) > 1000:
                    return content, f"AF-{uniprot_id}-F1", True
            except Exception:
                pass

        # Live AlphaFold EBI API lookup
        api_url = f"https://alphafold.ebi.ac.uk/api/prediction/{uniprot_id}"
        try:
            resp = requests.get(api_url, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and len(data) > 0 and "pdbUrl" in data[0]:
                    pdb_resp = requests.get(data[0]["pdbUrl"], timeout=12)
                    if pdb_resp.status_code == 200 and len(pdb_resp.text) > 1000:
                        try:
                            local_pdb.write_text(pdb_resp.text, encoding="utf-8")
                        except Exception:
                            pass
                        return pdb_resp.text, f"AF-{uniprot_id}-F1", True
        except Exception:
            pass

        return None, None, False

    def parse_pdb_structure(self, pdb_text: str, cache_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Parse CA coordinates and per-residue pLDDT confidence from an AlphaFold PDB.
        """
        if cache_key and cache_key in self._parsed_cache:
            return self._parsed_cache[cache_key]

        residues: Dict[int, Dict[str, Any]] = {}
        heavy_atoms_by_res: Dict[int, List[Tuple[float, float, float]]] = {}

        for line in pdb_text.splitlines():
            if not line.startswith("ATOM  "):
                continue
            atom_name = line[12:16].strip()
            res_name = line[17:20].strip().upper()
            try:
                res_seq = int(line[22:26].strip())
                x = float(line[30:38].strip())
                y = float(line[38:46].strip())
                z = float(line[46:54].strip())
                bfactor = float(line[60:66].strip())
            except (ValueError, IndexError):
                continue

            heavy_atoms_by_res.setdefault(res_seq, []).append((x, y, z))
            if atom_name == "CA" or res_seq not in residues:
                residues[res_seq] = {
                    "position": res_seq,
                    "aa": AA3_TO_1.get(res_name, "X"),
                    "res_name": res_name,
                    "ca": (x, y, z),
                    "plddt": round(bfactor, 2),
                }

        sorted_positions = sorted(residues.keys())
        plddt_list = [residues[p]["plddt"] for p in sorted_positions]
        mean_plddt = round(float(np.mean(plddt_list)), 2) if plddt_list else 0.0

        bands = {
            "very_high": sum(1 for v in plddt_list if v >= 90.0),
            "confident": sum(1 for v in plddt_list if 70.0 <= v < 90.0),
            "low": sum(1 for v in plddt_list if 50.0 <= v < 70.0),
            "very_low_disordered": sum(1 for v in plddt_list if v < 50.0),
        }

        parsed = {
            "num_residues": len(sorted_positions),
            "positions": sorted_positions,
            "residues": residues,
            "heavy_atoms": heavy_atoms_by_res,
            "mean_plddt": mean_plddt,
            "plddt_profile": [
                {"position": p, "aa": residues[p]["aa"], "plddt": residues[p]["plddt"]}
                for p in sorted_positions
            ],
            "confidence_bands": bands,
        }
        if cache_key:
            self._parsed_cache[cache_key] = parsed
        return parsed

    @staticmethod
    def _min_atom_distance(
        atoms_a: List[Tuple[float, float, float]],
        atoms_b: List[Tuple[float, float, float]],
    ) -> float:
        arr_a = np.asarray(atoms_a, dtype=np.float32)
        arr_b = np.asarray(atoms_b, dtype=np.float32)
        diff = arr_a[:, None, :] - arr_b[None, :, :]
        dists = np.sqrt(np.sum(diff * diff, axis=-1))
        return float(dists.min())

    def extract_spatial_pocket(
        self,
        pdb_text: Optional[str],
        target_pos: int,
        pocket_radius: float = 5.0,
        burial_radius: float = 8.0,
        max_pocket_residues: int = 10,
        cache_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Extract the real 3D structural microenvironment around `target_pos`:
        - Exact heavy-atom 5.0 A contacting pocket residues
        - 8.0 A CA burial contact count (core vs. surface indicator)
        - Local pLDDT structural order confidence
        """
        if not pdb_text:
            return {
                "available": False,
                "target_position": target_pos,
                "target_plddt": None,
                "structural_region": "Unknown (No 3D structure)",
                "burial_contacts_8A": 0,
                "burial_score": 0.5,
                "pocket_radius_angstrom": pocket_radius,
                "pocket_residues": [],
                "pocket_positions": [target_pos],
            }

        parsed = self.parse_pdb_structure(pdb_text, cache_key=cache_key)
        residues = parsed["residues"]
        heavy_atoms = parsed["heavy_atoms"]

        if target_pos not in residues:
            return {
                "available": False,
                "target_position": target_pos,
                "target_plddt": None,
                "structural_region": "Outside resolved 3D coordinates",
                "burial_contacts_8A": 0,
                "burial_score": 0.5,
                "pocket_radius_angstrom": pocket_radius,
                "pocket_residues": [],
                "pocket_positions": [target_pos],
            }

        target_info = residues[target_pos]
        target_ca = np.asarray(target_info["ca"], dtype=np.float32)
        target_atoms = heavy_atoms[target_pos]

        neighbors: List[Dict[str, Any]] = []
        burial_contacts = 0

        for pos, info in residues.items():
            if pos == target_pos:
                continue
            ca = np.asarray(info["ca"], dtype=np.float32)
            ca_dist = float(np.linalg.norm(target_ca - ca))
            if ca_dist <= burial_radius:
                burial_contacts += 1
            # Pre-filter with CA <= 14 A before exact heavy-atom minimum distance
            if ca_dist <= 14.0:
                min_d = self._min_atom_distance(target_atoms, heavy_atoms[pos])
                if min_d <= pocket_radius:
                    neighbors.append({
                        "position": pos,
                        "aa": info["aa"],
                        "res_name": info["res_name"],
                        "distance_angstrom": round(min_d, 2),
                        "ca_distance_angstrom": round(ca_dist, 2),
                        "plddt": info["plddt"],
                        "is_sequence_adjacent": abs(pos - target_pos) == 1,
                    })

        neighbors.sort(key=lambda x: x["distance_angstrom"])
        # Keep target residue first, then closest 3D pocket neighbors up to max_pocket_residues
        selected_neighbors = neighbors[: max(0, max_pocket_residues - 1)]
        pocket_positions = [target_pos] + [n["position"] for n in selected_neighbors]

        plddt = target_info["plddt"]
        if plddt >= 90.0:
            order_label = "Structured Core / Very High Confidence (pLDDT >= 90)"
        elif plddt >= 70.0:
            order_label = "Folded Domain / Confident (70 <= pLDDT < 90)"
        elif plddt >= 50.0:
            order_label = "Flexible Loop / Low Confidence (50 <= pLDDT < 70)"
        else:
            order_label = "Intrinsically Disordered Region (pLDDT < 50)"

        # Normalized burial score in [0, 1] combining pLDDT order & 8 A neighbor density
        contact_norm = min(1.0, burial_contacts / 14.0)
        plddt_norm = min(1.0, max(0.0, plddt / 100.0))
        burial_score = round(0.55 * plddt_norm + 0.45 * contact_norm, 4)

        return {
            "available": True,
            "target_position": target_pos,
            "target_aa": target_info["aa"],
            "target_plddt": plddt,
            "structural_region": order_label,
            "burial_contacts_8A": burial_contacts,
            "burial_score": burial_score,
            "pocket_radius_angstrom": pocket_radius,
            "pocket_residues": selected_neighbors,
            "all_5A_contact_count": len(neighbors),
            "pocket_positions": pocket_positions,
        }
