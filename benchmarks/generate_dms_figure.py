"""Generate real 300-DPI 3D-Pocket Zero-Shot DMS Heatmap for TP53 p.R273H."""

from __future__ import annotations

import sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
from ml.engine import ProteinLensScientificEngine  # noqa: E402

OUT = ROOT / "benchmarks" / "output" / "fig4_pocket_dms_heatmap.png"


def main():
    eng = ProteinLensScientificEngine(ROOT / "backend" / "assets")
    p53 = [p["sequence"] for p in eng.presets if p["uniprot_id"] == "P04637"][0]
    res = eng.analyze_variant_and_pocket_dms(
        p53, 273, "H", uniprot_id="P04637", run_pocket_dms=True, max_pocket_residues=8
    )
    aas = res["pocket_dms"]["amino_acids"]
    rows = res["pocket_dms"]["rows"]
    mat = np.array([[r["scores"][a] for a in aas] for r in rows], dtype=float)
    ylabels = [
        f"{r['wt_aa']}{r['position']} ({'Target' if r['is_target'] else str(r['distance_angstrom']) + ' A'})"
        for r in rows
    ]

    fig, ax = plt.subplots(figsize=(10.2, 4.3), dpi=300)
    im = ax.imshow(mat, cmap="RdYlGn", vmin=-4.5, vmax=1.5, aspect="auto")
    ax.set_xticks(range(len(aas)))
    ax.set_xticklabels(aas, fontsize=9, fontweight="bold", family="monospace")
    ax.set_yticks(range(len(ylabels)))
    ax.set_yticklabels(ylabels, fontsize=8.5, fontweight="bold", family="monospace")

    for i in range(len(rows)):
        for j, a in enumerate(aas):
            val = mat[i, j]
            is_wt = a == rows[i]["wt_aa"]
            txt = "WT" if is_wt else f"{val:.1f}"
            color = "#0f172a" if (-2.3 < val < 0.9 and not is_wt) else "#ffffff"
            if is_wt:
                ax.add_patch(plt.Rectangle((j - 0.5, i - 0.5), 1, 1, facecolor="#1e293b", edgecolor="#ffffff", lw=1.0))
            ax.text(j, i, txt, ha="center", va="center", fontsize=6.8, color=color, fontweight="bold" if is_wt else "normal")

    cbar = fig.colorbar(im, ax=ax, shrink=0.92)
    cbar.set_label("ESM-2 Masked-Marginal LLR (Negative = Deleterious)", fontsize=8.5, fontweight="bold")
    ax.set_title("TP53 p.R273H: 5.0 A 3D-Pocket Zero-Shot Deep Mutational Scanning (DMS) Heatmap", fontsize=11, fontweight="bold", pad=10)
    plt.tight_layout()
    fig.savefig(OUT, dpi=300)
    plt.close(fig)
    print(f"Saved {OUT}")


if __name__ == "__main__":
    main()
