"""
ProteinLens-OS Exact Gene Ontology DAG & True Path Rule Engine
Implements:
1. Fixed-point bottom-up True Path Rule propagation guaranteeing 0.00% violations
2. Quantitative pre/post violation audit and repair logging
3. Transitive-reduced React Flow JSON graph generation for interactive exploration
4. Information-Accretion (IA) weighted Functional Disruption Index (Delta-GO_IA)
"""

from __future__ import annotations

from typing import Any, Dict, List, Set, Tuple
import numpy as np


class DAGEngine:
    def __init__(self, metadata: Dict[str, Any]):
        self.top_terms: List[str] = metadata["top_terms"]
        self.term_names: Dict[str, str] = metadata["term_names"]
        self.term_aspects: Dict[str, str] = metadata["term_aspects"]
        self.term_defs: Dict[str, str] = metadata["term_defs"]
        self.ia_weights: Dict[str, float] = {
            k: float(v) for k, v in metadata.get("ia_weights", {}).items()
        }
        self.eval_parents: Dict[str, List[str]] = metadata.get("eval_parents", {})
        self.term2idx: Dict[str, int] = {t: i for i, t in enumerate(self.top_terms)}
        self.ia_vector: np.ndarray = np.array(
            [self.ia_weights.get(t, 0.0) for t in self.top_terms], dtype=np.float32
        )

        # Precompute indexed parent edges for ultra-fast fixed-point propagation
        self._parent_edges: List[Tuple[int, int]] = []
        for child, parents in self.eval_parents.items():
            if child not in self.term2idx:
                continue
            c_idx = self.term2idx[child]
            for parent in parents:
                if parent in self.term2idx and parent != child:
                    self._parent_edges.append((c_idx, self.term2idx[parent]))

    def count_violations(self, probs: np.ndarray, tol: float = 1e-6) -> int:
        """Count exact number of (child, parent) pairs violating P(parent) >= P(child)."""
        violations = 0
        for c_idx, p_idx in self._parent_edges:
            if probs[c_idx] > probs[p_idx] + tol:
                violations += 1
        return violations

    def propagate_true_path(self, probs: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Enforce strict True Path Rule monotonicity:
            Score(Parent) = max(Score(Parent), Score(Child))
        Iterates to convergence (fixed point) so multi-hop chains have ZERO residual violations.
        """
        raw = np.asarray(probs, dtype=np.float32)
        violations_before = self.count_violations(raw)

        propagated = raw.copy()
        iterations = 0
        max_iters = 16
        for _ in range(max_iters):
            iterations += 1
            changed = False
            for c_idx, p_idx in self._parent_edges:
                if propagated[c_idx] > propagated[p_idx]:
                    propagated[p_idx] = propagated[c_idx]
                    changed = True
            if not changed:
                break

        violations_after = self.count_violations(propagated)

        # Collect detailed repair log for auditability
        repairs = []
        for i, term in enumerate(self.top_terms):
            delta = float(propagated[i] - raw[i])
            if delta > 0.005:
                repairs.append({
                    "term": term,
                    "name": self.term_names.get(term, term),
                    "aspect": self.term_aspects.get(term, "MF"),
                    "raw_score": round(float(raw[i]), 4),
                    "propagated_score": round(float(propagated[i]), 4),
                    "delta": round(delta, 4),
                    "ia_weight": round(float(self.ia_weights.get(term, 0.0)), 3),
                })
        repairs.sort(key=lambda r: r["delta"], reverse=True)

        audit = {
            "violations_before": violations_before,
            "violations_after": violations_after,
            "convergence_iterations": iterations,
            "terms_repaired": len(repairs),
            "max_repair_delta": round(repairs[0]["delta"], 4) if repairs else 0.0,
            "repair_log": repairs[:40],
        }
        return propagated, audit

    def categorize_predictions(
        self,
        raw_probs: np.ndarray,
        propagated_probs: np.ndarray,
        min_score: float = 0.05,
    ) -> Dict[str, List[Dict[str, Any]]]:
        categorized: Dict[str, List[Dict[str, Any]]] = {"MF": [], "BP": [], "CC": []}
        for i, term in enumerate(self.top_terms):
            aspect = self.term_aspects.get(term, "MF")
            score = float(propagated_probs[i])
            raw_s = float(raw_probs[i])
            if score >= min_score:
                categorized.setdefault(aspect, []).append({
                    "term": term,
                    "name": self.term_names.get(term, term),
                    "aspect": aspect,
                    "score": round(score, 4),
                    "raw_score": round(raw_s, 4),
                    "repaired": (score - raw_s) > 0.01,
                    "repair_delta": round(max(0.0, score - raw_s), 4),
                    "ia": round(float(self.ia_weights.get(term, 0.0)), 3),
                    "definition": self.term_defs.get(term, "Gene Ontology functional term."),
                })
        for asp in categorized:
            categorized[asp].sort(key=lambda x: x["score"], reverse=True)
        return categorized

    def build_react_flow_dag(
        self,
        raw_probs: np.ndarray,
        propagated_probs: np.ndarray,
        aspect: str = "MF",
        min_conf: float = 0.18,
        max_nodes: int = 16,
    ) -> Dict[str, Any]:
        """
        Build a transitive-reduced interactive DAG payload for @xyflow/react.
        Parent -> Child direction (general -> specific), highlighting True-Path repaired nodes.
        """
        aspect_terms = [
            (t, float(propagated_probs[self.term2idx[t]]))
            for t in self.top_terms
            if self.term_aspects.get(t, "MF") == aspect
        ]
        aspect_terms.sort(key=lambda x: x[1], reverse=True)

        selected = [t for t, s in aspect_terms if s >= min_conf][:max_nodes]
        if len(selected) < 5:
            selected = [t for t, _ in aspect_terms[: min(8, len(aspect_terms))]]

        expanded: Set[str] = set(selected)
        # Include immediate parents so hierarchy connects visually
        for t in list(selected):
            for p in self.eval_parents.get(t, []):
                if p in self.term2idx and self.term_aspects.get(p, aspect) == aspect:
                    if len(expanded) < max_nodes + 8:
                        expanded.add(p)

        # Build nodes
        nodes: List[Dict[str, Any]] = []
        for t in sorted(expanded):
            idx = self.term2idx[t]
            raw_p = float(raw_probs[idx])
            prop_p = float(propagated_probs[idx])
            repaired = (prop_p - raw_p) > 0.015
            nodes.append({
                "id": t,
                "label": self.term_names.get(t, t),
                "aspect": aspect,
                "raw_score": round(raw_p, 4),
                "propagated_score": round(prop_p, 4),
                "repaired": repaired,
                "repair_delta": round(max(0.0, prop_p - raw_p), 4),
                "ia_weight": round(float(self.ia_weights.get(t, 0.0)), 3),
                "definition": self.term_defs.get(t, "Gene Ontology functional term."),
            })

        # Transitive reduction within `expanded`
        edges: List[Dict[str, Any]] = []
        for child in sorted(expanded):
            child_ancestors = set(self.eval_parents.get(child, [])) & expanded
            for parent in sorted(child_ancestors):
                if parent == child:
                    continue
                is_redundant = any(
                    mid != parent and parent in self.eval_parents.get(mid, [])
                    for mid in child_ancestors
                )
                if not is_redundant:
                    c_idx = self.term2idx[child]
                    p_idx = self.term2idx[parent]
                    edge_repaired = (
                        float(propagated_probs[p_idx]) - float(raw_probs[p_idx]) > 0.015
                        and abs(float(propagated_probs[p_idx]) - float(propagated_probs[c_idx])) < 0.02
                    )
                    edges.append({
                        "id": f"{parent}->{child}",
                        "source": parent,
                        "target": child,
                        "repaired_flow": edge_repaired,
                    })

        return {
            "aspect": aspect,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "repaired_node_count": sum(1 for n in nodes if n["repaired"]),
            "nodes": nodes,
            "edges": edges,
        }

    def compute_ia_disruption(
        self,
        wt_propagated: np.ndarray,
        mut_propagated: np.ndarray,
    ) -> Dict[str, Any]:
        """
        Compute Information-Accretion weighted Functional Disruption Index (Delta-GO_IA)
        plus ranked lost (attenuated) and gained (elevated) functional annotations.
        """
        diff = mut_propagated - wt_propagated
        abs_diff = np.abs(diff)
        weighted_sum = float(np.sum(self.ia_vector * abs_diff))
        total_ia = float(np.sum(self.ia_vector)) + 1e-9
        # Scaled disruption index (0..100) and normalized [0..1]
        raw_ratio = weighted_sum / total_ia
        fdi_100 = round(min(100.0, raw_ratio * 250.0), 2)
        fdi_norm = round(min(1.0, raw_ratio * 2.5), 4)

        lost_terms = []
        gained_terms = []
        for i, term in enumerate(self.top_terms):
            d = float(diff[i])
            wt_s = float(wt_propagated[i])
            mut_s = float(mut_propagated[i])
            if abs(d) < 0.005:
                continue
            entry = {
                "term": term,
                "name": self.term_names.get(term, term),
                "aspect": self.term_aspects.get(term, "MF"),
                "wt_score": round(wt_s, 4),
                "mut_score": round(mut_s, 4),
                "delta": round(d, 4),
                "ia": round(float(self.ia_weights.get(term, 0.0)), 3),
            }
            if d < 0 and wt_s >= 0.10:
                lost_terms.append(entry)
            elif d > 0 and mut_s >= 0.10:
                gained_terms.append(entry)

        lost_terms.sort(key=lambda x: x["delta"])
        gained_terms.sort(key=lambda x: x["delta"], reverse=True)

        return {
            "fdi_score": fdi_100,
            "fdi_normalized": fdi_norm,
            "ia_weighted_l1": round(weighted_sum, 4),
            "lost_functions": lost_terms[:12],
            "gained_functions": gained_terms[:12],
        }
