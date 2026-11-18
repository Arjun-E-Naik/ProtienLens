"""
ProteinLens-OS Real Lexical 3-mer Sparse kNN Baseline
Eliminates simulated heuristics by building and querying a real 8,000-dimensional
L2-normalized log(1 + count) 3-mer feature matrix aligned with the 2,000 CAFA 6
training proteins and Y_train ground-truth GO label matrix.
"""

from __future__ import annotations

import itertools
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import List, Optional, Tuple
import numpy as np
from scipy import sparse


AA = "ACDEFGHIKLMNPQRSTVWY"
KMERS = {"".join(k): i for i, k in enumerate(itertools.product(AA, repeat=3))}
NUM_KMERS = len(KMERS)  # 8,000


def featurize_sequence_3mer(sequence: str) -> sparse.csr_matrix:
    """Compute real 8,000-d L2-normalized log1p 3-mer count vector."""
    clean = "".join(sequence.strip().upper().split())
    counts = defaultdict(int)
    for i in range(max(0, len(clean) - 2)):
        tri = clean[i : i + 3]
        idx = KMERS.get(tri)
        if idx is not None:
            counts[idx] += 1

    if not counts:
        return sparse.csr_matrix((1, NUM_KMERS), dtype=np.float32)

    cols = np.fromiter(counts.keys(), dtype=np.int32)
    vals = np.log1p(np.fromiter(counts.values(), dtype=np.float32))
    norm = float(np.linalg.norm(vals)) + 1e-9
    vals = vals / norm
    rows = np.zeros(len(cols), dtype=np.int32)
    return sparse.csr_matrix((vals, (rows, cols)), shape=(1, NUM_KMERS), dtype=np.float32)


def _read_first_n_fasta_from_zip(zip_path: Path, limit: int) -> List[str]:
    seqs: List[str] = []
    cur: List[str] = []
    with zipfile.ZipFile(zip_path, "r") as zf:
        fasta_member = next(
            (n for n in zf.namelist() if n.endswith("train_sequences.fasta")), None
        )
        if not fasta_member:
            return []
        with zf.open(fasta_member, "r") as raw:
            for raw_line in raw:
                line = raw_line.decode("utf-8", errors="ignore").strip()
                if not line:
                    continue
                if line.startswith(">"):
                    if cur:
                        seqs.append("".join(cur))
                        cur = []
                        if len(seqs) >= limit:
                            break
                else:
                    cur.append(line)
            if cur and len(seqs) < limit:
                seqs.append("".join(cur))
    return seqs


class Real3MerBaseline:
    def __init__(self, assets_dir: Path, Y_train: np.ndarray, cafa_zip_path: Optional[Path] = None):
        self.assets_dir = assets_dir
        self.Y_train = Y_train.astype(np.float32)
        self.matrix_path = assets_dir / "train_3mer_matrix.npz"
        self.X_train_3mer: Optional[sparse.csr_matrix] = None
        self.is_real_trained = False

        self._load_or_build(cafa_zip_path)

    def _load_or_build(self, cafa_zip_path: Optional[Path]) -> None:
        if self.matrix_path.exists():
            try:
                mat = sparse.load_npz(self.matrix_path)
                if mat.shape[0] == self.Y_train.shape[0]:
                    self.X_train_3mer = mat.tocsr()
                    self.is_real_trained = True
                    return
            except Exception:
                pass

        # Attempt to build directly from the CAFA 6 zip archive if available
        candidate_zips = []
        if cafa_zip_path:
            candidate_zips.append(cafa_zip_path)
        candidate_zips.append(Path(r"C:\Users\arjun\Downloads\cafa-6-protein-function-prediction.zip"))
        candidate_zips.append(self.assets_dir.parent.parent.parent / "cafa-6-protein-function-prediction.zip")

        for zpath in candidate_zips:
            if zpath and zpath.exists():
                n_train = self.Y_train.shape[0]
                seqs = _read_first_n_fasta_from_zip(zpath, limit=n_train)
                if len(seqs) == n_train:
                    rows, cols, data = [], [], []
                    for row_idx, seq in enumerate(seqs):
                        clean = seq.strip().upper()
                        counts = defaultdict(int)
                        for i in range(max(0, len(clean) - 2)):
                            k_idx = KMERS.get(clean[i : i + 3])
                            if k_idx is not None:
                                counts[k_idx] += 1
                        if not counts:
                            continue
                        c_arr = np.fromiter(counts.keys(), dtype=np.int32)
                        v_arr = np.log1p(np.fromiter(counts.values(), dtype=np.float32))
                        v_arr /= float(np.linalg.norm(v_arr)) + 1e-9
                        rows.extend([row_idx] * len(c_arr))
                        cols.extend(c_arr.tolist())
                        data.extend(v_arr.tolist())

                    mat = sparse.csr_matrix(
                        (np.asarray(data, dtype=np.float32), (rows, cols)),
                        shape=(n_train, NUM_KMERS),
                        dtype=np.float32,
                    )
                    sparse.save_npz(self.matrix_path, mat)
                    self.X_train_3mer = mat
                    self.is_real_trained = True
                    return

    def predict(self, sequence: str, k: int = 15) -> np.ndarray:
        """
        Real cosine kNN voting in 8,000-d 3-mer space.
        Falls back to empirical prior ONLY if no training sequences matrix exists.
        """
        if self.X_train_3mer is None:
            return self.Y_train.mean(axis=0).astype(np.float32)

        q = featurize_sequence_3mer(sequence)
        sims = (self.X_train_3mer @ q.T).toarray().ravel()
        k_eff = min(k, len(sims))
        top_idx = np.argpartition(-sims, k_eff)[:k_eff]
        weights = np.clip(sims[top_idx], 0.0, 1.0) ** 2
        denom = float(weights.sum())
        if denom < 1e-9:
            return self.Y_train.mean(axis=0).astype(np.float32)
        return ((weights[:, None] * self.Y_train[top_idx]).sum(axis=0) / denom).astype(np.float32)

    def predict_batch_matrix(self, X_query: sparse.csr_matrix, X_ref: sparse.csr_matrix, Y_ref: np.ndarray, k: int = 15) -> np.ndarray:
        """Batch 3-mer kNN prediction for reproducible benchmark evaluation."""
        sims = (X_query @ X_ref.T).toarray()
        out = np.zeros((X_query.shape[0], Y_ref.shape[1]), dtype=np.float32)
        prior = Y_ref.mean(axis=0).astype(np.float32)
        for i in range(sims.shape[0]):
            row = sims[i]
            top_idx = np.argpartition(-row, min(k, len(row) - 1))[:k]
            w = np.clip(row[top_idx], 0.0, 1.0) ** 2
            denom = float(w.sum())
            if denom < 1e-9:
                out[i] = prior
            else:
                out[i] = (w[:, None] * Y_ref[top_idx]).sum(axis=0) / denom
        return out
