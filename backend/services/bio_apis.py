"""
ProteinLens-OS Federated Open-Biomedical Evidence Connector
Queries live public scientific databases with graceful offline fallback:
1. UniProt REST API (canonical sequence, gene symbol, disease associations, active sites)
2. NCBI ClinVar E-Utilities (real clinical significance records for gene/variant)
3. Open Targets GraphQL API (known clinical drugs, druggability & target tractability)
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional
import httpx


class BioEvidenceService:
    def __init__(self, timeout: float = 8.0):
        self.timeout = timeout
        self._mem_cache: Dict[str, Any] = {}

    async def fetch_uniprot_entry(self, uniprot_id: str) -> Dict[str, Any]:
        uid = uniprot_id.strip().upper()
        cache_key = f"uniprot:{uid}"
        if cache_key in self._mem_cache:
            return self._mem_cache[cache_key]

        url = f"https://rest.uniprot.org/uniprotkb/{uid}.json"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    return {"available": False, "uniprot_id": uid, "error": f"HTTP {resp.status_code}"}
                data = resp.json()

            gene_symbol = None
            genes = data.get("genes", [])
            if genes and "geneName" in genes[0]:
                gene_symbol = genes[0]["geneName"].get("value")

            protein_name = (
                data.get("proteinDescription", {})
                .get("recommendedName", {})
                .get("fullName", {})
                .get("value", uid)
            )
            organism = data.get("organism", {}).get("scientificName", "Unknown")
            sequence = data.get("sequence", {}).get("value", "")

            # Extract function & disease comments
            function_summary = ""
            diseases: List[Dict[str, str]] = []
            for comment in data.get("comments", []):
                ctype = comment.get("commentType", "")
                if ctype == "FUNCTION" and not function_summary:
                    texts = comment.get("texts", [])
                    if texts:
                        function_summary = texts[0].get("value", "")
                elif ctype == "DISEASE":
                    dis = comment.get("disease", {})
                    if dis.get("diseaseId"):
                        diseases.append({
                            "name": dis.get("diseaseId", ""),
                            "acronym": dis.get("acronym", ""),
                            "description": dis.get("description", "")[:240],
                        })

            # Extract known functional features (Active sites, Binding sites, Domains)
            features = []
            for feat in data.get("features", []):
                ftype = feat.get("type", "")
                if ftype in ("Active site", "Binding site", "DNA binding", "Domain", "Mutagenesis"):
                    loc = feat.get("location", {})
                    start = loc.get("start", {}).get("value")
                    end = loc.get("end", {}).get("value")
                    if start is not None:
                        features.append({
                            "type": ftype,
                            "start": start,
                            "end": end or start,
                            "description": feat.get("description", "")[:140],
                        })

            # Extract Ensembl Gene ID for Open Targets lookup
            ensembl_gene_id = None
            for xref in data.get("uniProtKBCrossReferences", []):
                if xref.get("database") == "Ensembl":
                    for prop in xref.get("properties", []):
                        if prop.get("key") == "GeneId":
                            ensembl_gene_id = prop.get("value", "").split(".")[0]
                            break
                if ensembl_gene_id:
                    break

            result = {
                "available": True,
                "source": "UniProtKB REST API",
                "uniprot_id": uid,
                "gene_symbol": gene_symbol,
                "ensembl_gene_id": ensembl_gene_id,
                "protein_name": protein_name,
                "organism": organism,
                "sequence": sequence,
                "sequence_length": len(sequence),
                "function_summary": function_summary[:500],
                "diseases": diseases[:6],
                "known_features": features[:20],
            }
            self._mem_cache[cache_key] = result
            return result
        except Exception as exc:
            return {"available": False, "uniprot_id": uid, "error": str(exc)}

    async def fetch_clinvar_variant(self, gene_symbol: Optional[str], mutation: str) -> Dict[str, Any]:
        """
        Query NCBI ClinVar E-utilities for clinical significance matching gene + protein change (e.g., TP53 + R273H).
        """
        if not gene_symbol:
            return {"available": False, "records": [], "note": "No gene symbol provided for ClinVar query."}

        cache_key = f"clinvar:{gene_symbol}:{mutation}"
        if cache_key in self._mem_cache:
            return self._mem_cache[cache_key]

        # Convert 1-letter R273H to 3-letter Arg273His for higher ClinVar hit rate
        aa1_to_3 = {
            "A": "Ala", "C": "Cys", "D": "Asp", "E": "Glu", "F": "Phe",
            "G": "Gly", "H": "His", "I": "Ile", "K": "Lys", "L": "Leu",
            "M": "Met", "N": "Asn", "P": "Pro", "Q": "Gln", "R": "Arg",
            "S": "Ser", "T": "Thr", "V": "Val", "W": "Trp", "Y": "Tyr",
        }
        hgvs_3 = mutation
        if len(mutation) >= 3 and mutation[0] in aa1_to_3 and mutation[-1] in aa1_to_3:
            hgvs_3 = f"p.{aa1_to_3[mutation[0]]}{mutation[1:-1]}{aa1_to_3[mutation[-1]]}"

        term = f"{gene_symbol}[gene] AND ({hgvs_3} OR {mutation})"
        esearch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        esummary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r1 = await client.get(
                    esearch_url,
                    params={"db": "clinvar", "term": term, "retmode": "json", "retmax": 5},
                )
                r1.raise_for_status()
                id_list = r1.json().get("esearchresult", {}).get("idlist", [])
                if not id_list:
                    out = {
                        "available": True,
                        "source": "NCBI ClinVar E-Utilities",
                        "query": term,
                        "matched": False,
                        "records": [],
                        "summary_classification": "Not Reported in ClinVar (Novel / Uncataloged Variant)",
                    }
                    self._mem_cache[cache_key] = out
                    return out

                r2 = await client.get(
                    esummary_url,
                    params={"db": "clinvar", "id": ",".join(id_list[:4]), "retmode": "json"},
                )
                r2.raise_for_status()
                summaries = r2.json().get("result", {})

            records = []
            for vid in id_list[:4]:
                item = summaries.get(str(vid))
                if not isinstance(item, dict):
                    continue
                germline = item.get("germline_classification", {})
                sig = (
                    germline.get("description")
                    or item.get("clinical_significance", {}).get("description")
                    or "Uncertain significance"
                )
                review = germline.get("review_status", "")
                traits = [
                    t.get("trait_name", "")
                    for t in germline.get("trait_set", [])
                    if t.get("trait_name")
                ]
                records.append({
                    "variation_id": str(vid),
                    "title": item.get("title", ""),
                    "clinical_significance": sig,
                    "review_status": review,
                    "conditions": traits[:4],
                    "url": f"https://www.ncbi.nlm.nih.gov/clinvar/variation/{vid}/",
                })

            top_sig = records[0]["clinical_significance"] if records else "Uncertain significance"
            out = {
                "available": True,
                "source": "NCBI ClinVar E-Utilities",
                "query": term,
                "matched": len(records) > 0,
                "records": records,
                "summary_classification": top_sig,
            }
            self._mem_cache[cache_key] = out
            return out
        except Exception as exc:
            return {
                "available": False,
                "source": "NCBI ClinVar E-Utilities",
                "matched": False,
                "records": [],
                "error": str(exc),
                "summary_classification": "ClinVar Offline / Lookup Unavailable",
            }

    async def fetch_opentargets_drugs(self, ensembl_gene_id: Optional[str]) -> Dict[str, Any]:
        """
        Query Open Targets Platform GraphQL API for approved & clinical-stage drugs targeting this protein.
        """
        if not ensembl_gene_id:
            return {"available": False, "drugs": [], "tractability": []}

        cache_key = f"opentargets:{ensembl_gene_id}"
        if cache_key in self._mem_cache:
            return self._mem_cache[cache_key]

        query = """
        query TargetDrugs($ensemblId: String!) {
          target(ensemblId: $ensemblId) {
            id
            approvedSymbol
            tractability {
              label
              modality
              value
            }
            knownDrugs(size: 8) {
              uniqueDrugs
              rows {
                drugId
                prefName
                drugType
                phase
                mechanismOfAction
                disease {
                  name
                }
              }
            }
          }
        }
        """
        url = "https://api.platform.opentargets.org/api/v4/graphql"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(url, json={"query": query, "variables": {"ensemblId": ensembl_gene_id}})
                resp.raise_for_status()
                payload = resp.json()

            target = (payload.get("data") or {}).get("target")
            if not target:
                return {"available": False, "drugs": [], "tractability": []}

            tractability = [
                {"label": t["label"], "modality": t["modality"]}
                for t in target.get("tractability", [])
                if t.get("value") is True
            ][:8]

            seen = set()
            drugs = []
            known = target.get("knownDrugs") or {}
            for row in known.get("rows", []):
                dname = row.get("prefName")
                if not dname or dname in seen:
                    continue
                seen.add(dname)
                drugs.append({
                    "chembl_id": row.get("drugId", ""),
                    "name": dname,
                    "type": row.get("drugType", ""),
                    "phase": row.get("phase", 0),
                    "mechanism": row.get("mechanismOfAction", ""),
                    "disease": (row.get("disease") or {}).get("name", ""),
                })

            out = {
                "available": True,
                "source": "Open Targets Platform GraphQL",
                "ensembl_gene_id": ensembl_gene_id,
                "approved_symbol": target.get("approvedSymbol"),
                "unique_drug_count": known.get("uniqueDrugs", len(drugs)),
                "tractability": tractability,
                "drugs": drugs[:8],
            }
            self._mem_cache[cache_key] = out
            return out
        except Exception as exc:
            return {"available": False, "drugs": [], "tractability": [], "error": str(exc)}
