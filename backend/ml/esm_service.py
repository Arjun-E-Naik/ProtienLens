"""
ProteinLens-OS ESM2 Evolutionary Language Model Engine
Single-load `EsmForMaskedLM` (facebook/esm2_t6_8M_UR50D) delivering:
1. Mean-pooled 320-d sequence embeddings
2. Multi-Layer Attention-Rollout Residue Saliency (true transformer attribution)
3. Exact Zero-Shot Masked-Marginal Log-Likelihood Ratio (LLR) for variant pathogenicity
4. Single-Batch 3D-Pocket Deep Mutational Scanning (DMS: Pocket Positions x 20 AAs)
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple
import numpy as np
import torch


CANONICAL_AAS = list("ACDEFGHIKLMNPQRSTVWY")


class ESM2Service:
    def __init__(self, model_name: str = "facebook/esm2_t6_8M_UR50D"):
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.aa_token_ids: Dict[str, int] = {}
        self.mask_token_id: int = -1
        self._embed_cache: Dict[str, Dict[str, Any]] = {}
        self._llr_cache: Dict[Tuple[str, int], Dict[str, float]] = {}

    def _ensure_loaded(self) -> None:
        if self.model is not None:
            return
        from transformers import AutoTokenizer, EsmForMaskedLM

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        try:
            self.model = EsmForMaskedLM.from_pretrained(
                self.model_name, attn_implementation="eager"
            ).eval()
        except TypeError:
            self.model = EsmForMaskedLM.from_pretrained(self.model_name).eval()

        self.mask_token_id = int(self.tokenizer.mask_token_id)
        self.aa_token_ids = {
            aa: int(self.tokenizer.convert_tokens_to_ids(aa)) for aa in CANONICAL_AAS
        }

    @staticmethod
    def clean_sequence(sequence: str, maxlen: int = 512) -> str:
        # Strip FASTA header lines if pasted directly
        lines = [
            ln.strip() for ln in sequence.strip().splitlines() if not ln.strip().startswith(">")
        ]
        raw = "".join(lines).upper().replace(" ", "")
        return "".join(ch for ch in raw if ch.isalpha())[:maxlen]

    def embed_and_saliency(self, sequence: str, maxlen: int = 512) -> Dict[str, Any]:
        """
        Single forward pass extracting:
        - 320-d mean-pooled ESM2 embedding (matching training pipeline)
        - Multi-layer attention-rollout + activation-weighted residue saliency in [0, 1]
        """
        clean = self.clean_sequence(sequence, maxlen=maxlen)
        if not clean:
            return {
                "sequence": "",
                "embedding": np.zeros(320, dtype=np.float32),
                "saliency_scores": [],
                "hotspot_indices": [],
                "top_hotspots": [],
                "mean_saliency": 0.0,
            }
        if clean in self._embed_cache:
            return self._embed_cache[clean]

        self._ensure_loaded()
        with torch.no_grad():
            enc = self.tokenizer(
                [clean],
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=maxlen + 2,
            )
            outputs = self.model(
                **enc,
                output_hidden_states=True,
                output_attentions=True,
            )
            last_hidden = outputs.hidden_states[-1]  # [1, L+2, 320]
            mask = enc["attention_mask"].unsqueeze(-1).to(last_hidden.dtype)
            pooled = (last_hidden * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
            embedding = pooled[0].cpu().numpy().astype(np.float32)

            # Residue tokens sit at indices 1 .. len(clean)
            L = min(len(clean), last_hidden.shape[1] - 2)
            res_hidden = last_hidden[0, 1 : L + 1, :]
            act_norms = torch.norm(res_hidden, dim=-1).cpu().numpy()

            # True Multi-Layer Attention Rollout (Abnar & Zuidema 2020)
            attentions = outputs.attentions  # tuple of [1, heads, T, T]
            if attentions and len(attentions) > 0:
                T = attentions[0].shape[-1]
                rollout = torch.eye(T, dtype=torch.float32)
                for attn_layer in attentions:
                    # Mean across attention heads + residual connection
                    attn_heads_mean = attn_layer[0].mean(dim=0).float()
                    attn_aug = 0.5 * attn_heads_mean + 0.5 * torch.eye(T, dtype=torch.float32)
                    attn_aug = attn_aug / attn_aug.sum(dim=-1, keepdim=True).clamp(min=1e-9)
                    rollout = attn_aug @ rollout
                # Incoming attention importance received by each residue token
                attn_importance = rollout[:, 1 : L + 1].mean(dim=0).cpu().numpy()
            else:
                attn_importance = act_norms.copy()

        # Min-max normalize both signals and blend (70% attention rollout + 30% activation magnitude)
        def _minmax(arr: np.ndarray) -> np.ndarray:
            if len(arr) == 0:
                return arr
            lo, hi = float(arr.min()), float(arr.max())
            return (arr - lo) / (hi - lo) if (hi - lo) > 1e-9 else np.zeros_like(arr)

        combined = 0.70 * _minmax(attn_importance) + 0.30 * _minmax(act_norms)
        saliency = _minmax(combined)

        k_hotspots = max(3, min(40, int(len(saliency) * 0.12)))
        top_idx = np.argsort(-saliency)[:k_hotspots]
        hotspot_positions = sorted([int(i + 1) for i in top_idx])
        top_hotspots = [
            {
                "position": pos,
                "residue": clean[pos - 1],
                "saliency": round(float(saliency[pos - 1]), 4),
            }
            for pos in hotspot_positions
        ]
        top_hotspots.sort(key=lambda x: x["saliency"], reverse=True)

        result = {
            "sequence": clean,
            "embedding": embedding,
            "saliency_scores": [round(float(v), 4) for v in saliency.tolist()],
            "hotspot_indices": hotspot_positions,
            "top_hotspots": top_hotspots,
            "mean_saliency": round(float(np.mean(saliency)), 4) if len(saliency) else 0.0,
        }
        self._embed_cache[clean] = result
        return result

    def compute_position_aa_llrs(self, sequence: str, positions_1based: List[int], maxlen: int = 512) -> Dict[int, Dict[str, Any]]:
        r"""
        Compute exact ESM2 Masked-Marginal Log-Likelihood Ratios (LLR) for one or more positions
        in a SINGLE batched forward pass:
            LLR(pos, mut) = log P(x_pos = mut | x_{\pos}) - log P(x_pos = wt | x_{\pos})
        """
        clean = self.clean_sequence(sequence, maxlen=maxlen)
        valid_positions = [p for p in positions_1based if 1 <= p <= len(clean)]
        if not valid_positions:
            return {}

        self._ensure_loaded()
        out: Dict[int, Dict[str, Any]] = {}
        to_compute: List[int] = []
        for pos in valid_positions:
            key = (clean, pos)
            if key in self._llr_cache:
                out[pos] = self._llr_cache[key]
            else:
                to_compute.append(pos)

        if to_compute:
            enc = self.tokenizer(
                [clean], return_tensors="pt", truncation=True, max_length=maxlen + 2
            )
            base_ids = enc["input_ids"][0]  # [T]
            base_mask = enc["attention_mask"][0]  # [T]

            # Build batch where row b has token at `pos` masked (index = pos because token 0 is <cls>)
            batch_ids = base_ids.unsqueeze(0).repeat(len(to_compute), 1)
            batch_mask = base_mask.unsqueeze(0).repeat(len(to_compute), 1)
            for b_idx, pos in enumerate(to_compute):
                batch_ids[b_idx, pos] = self.mask_token_id

            with torch.no_grad():
                logits = self.model(input_ids=batch_ids, attention_mask=batch_mask).logits
                log_probs = torch.log_softmax(logits, dim=-1)

            for b_idx, pos in enumerate(to_compute):
                wt_aa = clean[pos - 1]
                wt_tid = self.aa_token_ids.get(wt_aa)
                pos_log_probs = log_probs[b_idx, pos]
                wt_lp = float(pos_log_probs[wt_tid].item()) if wt_tid is not None else -5.0

                aa_scores: Dict[str, float] = {}
                aa_probs: Dict[str, float] = {}
                for aa in CANONICAL_AAS:
                    tid = self.aa_token_ids[aa]
                    lp = float(pos_log_probs[tid].item())
                    aa_scores[aa] = round(lp - wt_lp, 4)
                    aa_probs[aa] = round(float(np.exp(lp)), 5)

                # Evolutionary conservation entropy over 20 canonical AAs
                p_vec = np.array([aa_probs[a] for a in CANONICAL_AAS], dtype=np.float64)
                p_vec = p_vec / (p_vec.sum() + 1e-12)
                entropy = float(-np.sum(p_vec * np.log2(p_vec + 1e-12)))
                conservation = round(max(0.0, 1.0 - entropy / np.log2(20.0)), 4)

                # Rank stabilizing / tolerated vs. most damaging mutations
                non_wt = [(a, s) for a, s in aa_scores.items() if a != wt_aa]
                non_wt.sort(key=lambda x: x[1], reverse=True)
                best_tolerated = [{"aa": a, "llr": s} for a, s in non_wt[:3]]
                most_damaging = [{"aa": a, "llr": s} for a, s in non_wt[-3:][::-1]]

                payload = {
                    "position": pos,
                    "wt_aa": wt_aa,
                    "wt_prob": round(float(np.exp(wt_lp)), 5),
                    "conservation": conservation,
                    "aa_llr": aa_scores,
                    "best_tolerated": best_tolerated,
                    "most_damaging": most_damaging,
                }
                self._llr_cache[(clean, pos)] = payload
                out[pos] = payload

        return out

    def compute_single_variant_llr(self, sequence: str, pos_1based: int, mut_aa: str) -> Dict[str, Any]:
        mut_aa = mut_aa.strip().upper()
        res = self.compute_position_aa_llrs(sequence, [pos_1based])
        if pos_1based not in res:
            return {
                "position": pos_1based,
                "wt_aa": "?",
                "mut_aa": mut_aa,
                "llr": 0.0,
                "wt_prob": 0.05,
                "conservation": 0.0,
                "aa_llr": {},
                "best_tolerated": [],
                "most_damaging": [],
            }
        pos_data = res[pos_1based]
        llr = float(pos_data["aa_llr"].get(mut_aa, 0.0))
        return {
            **pos_data,
            "mut_aa": mut_aa,
            "llr": round(llr, 4),
        }
