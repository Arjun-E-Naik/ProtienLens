"""
Generate clean, original 300-DPI software-drafted diagrams for the IIITN Report & Defense PPT:
1. fig0_architecture.png — Decoupled Full-Stack ProteinLens-OS System Architecture
2. fig_dag_concept.png   — Fixed-Point True Path Rule DAG Monotonicity Repair Diagram
"""

from __future__ import annotations

from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT = Path(__file__).resolve().parent / "output"
OUT.mkdir(parents=True, exist_ok=True)


def draw_box(ax, x, y, w, h, title, subtitle, fc, ec, tc="#0f172a", title_size=9.5, sub_size=7.5):
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.015,rounding_size=0.02",
        facecolor=fc, edgecolor=ec, linewidth=1.6, zorder=3
    )
    ax.add_patch(box)
    ax.text(x + w / 2, y + h * 0.66, title, ha="center", va="center", fontsize=title_size, fontweight="bold", color=tc, zorder=4)
    if subtitle:
        ax.text(x + w / 2, y + h * 0.30, subtitle, ha="center", va="center", fontsize=sub_size, color="#334155", zorder=4)


def draw_arrow(ax, x1, y1, x2, y2, color="#475569", lw=1.6, rad=0.0):
    arr = FancyArrowPatch(
        (x1, y1), (x2, y2),
        arrowstyle="-|>,head_length=6,head_width=3.5",
        connectionstyle=f"arc3,rad={rad}",
        color=color, linewidth=lw, zorder=5
    )
    ax.add_patch(arr)


def build_architecture_diagram():
    fig, ax = plt.subplots(figsize=(11.5, 6.2), dpi=300)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.5, 0.96, "ProteinLens-OS: Decoupled Local-First Full-Stack Architecture", ha="center", va="center", fontsize=13.5, fontweight="bold", color="#0f172a")
    ax.text(0.5, 0.92, "Next.js 15 Institutional Frontend  |  FastAPI + SQLite Backend  |  Independent ESM-2 & 3D Structural ML Core  |  Federated Open-Bio APIs", ha="center", va="center", fontsize=8.5, color="#475569")

    # Layer 1: Frontend (Top)
    bg1 = FancyBboxPatch((0.03, 0.72), 0.94, 0.16, boxstyle="round,pad=0.01,rounding_size=0.02", facecolor="#eff6ff", edgecolor="#93c5fd", lw=1.2, zorder=1)
    ax.add_patch(bg1)
    ax.text(0.05, 0.855, "PRESENTATION LAYER — Next.js 15 + TypeScript + Tailwind CSS (Port 3000)", fontsize=8.5, fontweight="bold", color="#1d4ed8", zorder=2)
    draw_box(ax, 0.05, 0.74, 0.20, 0.095, "3D Structure Studio", "3Dmol.js pLDDT & XAI Hotspots", "#ffffff", "#2563eb")
    draw_box(ax, 0.28, 0.74, 0.21, 0.095, "3D-Pocket DMS Lab", "20-AA Heatmap + Dual-Axis Risk", "#ffffff", "#2563eb")
    draw_box(ax, 0.52, 0.74, 0.20, 0.095, "Interactive GO DAG", "@xyflow/react + Repair Audit", "#ffffff", "#2563eb")
    draw_box(ax, 0.75, 0.74, 0.20, 0.095, "Labs, Cases & Settings", "Teaching Pack + AI Key Wizard", "#ffffff", "#2563eb")

    # Layer 2: API & Persistence (Middle)
    bg2 = FancyBboxPatch((0.03, 0.46), 0.94, 0.19, boxstyle="round,pad=0.01,rounding_size=0.02", facecolor="#f0fdf4", edgecolor="#86efac", lw=1.2, zorder=1)
    ax.add_patch(bg2)
    ax.text(0.05, 0.625, "APPLICATION & API LAYER — FastAPI + Uvicorn + SQLModel (Port 8000)", fontsize=8.5, fontweight="bold", color="#15803d", zorder=2)
    draw_box(ax, 0.05, 0.485, 0.27, 0.11, "REST & SSE Streaming Gateway", "Protein, Variant, Batch Triage & SHA-256 Export", "#ffffff", "#16a34a")
    draw_box(ax, 0.36, 0.485, 0.28, 0.11, "Auto-Config Multi-LLM XAI Router", "Live Model Discovery: Gemini / Grok / Groq / Ollama", "#ffffff", "#16a34a")
    draw_box(ax, 0.68, 0.485, 0.27, 0.11, "Local SQLite Institutional Vault", "ClinicalCase, BatchJob & White-Label Config", "#ffffff", "#16a34a")

    # Layer 3: Independent ML Core & Federated APIs (Bottom)
    bg3 = FancyBboxPatch((0.03, 0.06), 0.62, 0.33, boxstyle="round,pad=0.01,rounding_size=0.02", facecolor="#fefce8", edgecolor="#fde047", lw=1.2, zorder=1)
    ax.add_patch(bg3)
    ax.text(0.05, 0.365, "INDEPENDENT SCIENTIFIC ML CORE (CPU-Viable PyTorch + Transformers)", fontsize=8.5, fontweight="bold", color="#a16207", zorder=2)
    draw_box(ax, 0.05, 0.22, 0.27, 0.115, "Single-Load EsmForMaskedLM", "320-d Emb | Attn Rollout | Masked LLR | DMS", "#ffffff", "#d97706")
    draw_box(ax, 0.35, 0.22, 0.28, 0.115, "Multi-Paradigm GO Predictors", "Real 3-mer kNN | ESM2 kNN | PyTorch MLP", "#ffffff", "#d97706")
    draw_box(ax, 0.05, 0.08, 0.27, 0.11, "3D AlphaFold Pocket Parser", "pLDDT B-Factor + 5A Shell + 8A Burial", "#ffffff", "#d97706")
    draw_box(ax, 0.35, 0.08, 0.28, 0.11, "Fixed-Point True Path DAG & Fusion", "0.00% Violations + Dual-Axis Clinical Risk", "#ffffff", "#d97706")

    bg4 = FancyBboxPatch((0.68, 0.06), 0.29, 0.33, boxstyle="round,pad=0.01,rounding_size=0.02", facecolor="#fdf2f8", edgecolor="#f9a8d4", lw=1.2, zorder=1)
    ax.add_patch(bg4)
    ax.text(0.70, 0.365, "FEDERATED OPEN-BIO APIs", fontsize=8.5, fontweight="bold", color="#be185d", zorder=2)
    draw_box(ax, 0.70, 0.255, 0.25, 0.08, "UniProtKB & AlphaFold DB", "Sequences, Diseases & 3D PDBs", "#ffffff", "#db2777")
    draw_box(ax, 0.70, 0.16, 0.25, 0.08, "NCBI ClinVar E-Utilities", "Real Clinical Significance", "#ffffff", "#db2777")
    draw_box(ax, 0.70, 0.075, 0.25, 0.075, "Open Targets GraphQL", "Approved Drugs & Tractability", "#ffffff", "#db2777")

    # Vertical Arrows
    draw_arrow(ax, 0.18, 0.72, 0.18, 0.65, color="#1d4ed8")
    draw_arrow(ax, 0.50, 0.72, 0.50, 0.65, color="#1d4ed8")
    draw_arrow(ax, 0.82, 0.72, 0.82, 0.65, color="#1d4ed8")
    draw_arrow(ax, 0.25, 0.46, 0.25, 0.39, color="#15803d")
    draw_arrow(ax, 0.48, 0.46, 0.48, 0.39, color="#15803d")
    draw_arrow(ax, 0.82, 0.46, 0.82, 0.39, color="#be185d")

    plt.tight_layout()
    fig.savefig(OUT / "fig0_architecture.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def build_dag_repair_diagram():
    fig, ax = plt.subplots(figsize=(9.5, 4.4), dpi=300)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.5, 0.95, "Fixed-Point True Path Rule DAG Monotonicity Repair Mechanism", ha="center", va="center", fontsize=12.5, fontweight="bold", color="#0f172a")

    # Left: Before Repair
    ax.text(0.24, 0.86, "BEFORE: Raw Neural Ensemble (Contradiction!)", ha="center", fontsize=9.5, fontweight="bold", color="#be123c")
    draw_box(ax, 0.10, 0.65, 0.28, 0.14, "GO:0003674 (Root)", "Molecular Function | P = 0.62", "#fff1f2", "#e11d48", "#881337")
    draw_box(ax, 0.10, 0.40, 0.28, 0.14, "GO:0003676 (Parent)", "Nucleic Acid Binding | P = 0.48 (VIOLATION)", "#ffe4e6", "#e11d48", "#881337")
    draw_box(ax, 0.10, 0.14, 0.28, 0.14, "GO:0003677 (Child)", "DNA Binding | P = 0.89", "#eff6ff", "#2563eb", "#1e3a8a")
    draw_arrow(ax, 0.24, 0.65, 0.24, 0.54, color="#e11d48")
    draw_arrow(ax, 0.24, 0.40, 0.24, 0.28, color="#e11d48")

    # Center transform arrow
    draw_arrow(ax, 0.42, 0.48, 0.58, 0.48, color="#d97706", lw=2.8)
    ax.text(0.50, 0.57, "Fixed-Point Bottom-Up\nMax Propagation", ha="center", va="center", fontsize=9, fontweight="bold", color="#b45309")
    ax.text(0.50, 0.39, "P(u) = max(P(u), P(v))\nuntil 0 violations", ha="center", va="center", fontsize=8, family="monospace", color="#334155")

    # Right: After Repair
    ax.text(0.76, 0.86, "AFTER: True-Path Guaranteed (0.00% Violations)", ha="center", fontsize=9.5, fontweight="bold", color="#047857")
    draw_box(ax, 0.62, 0.65, 0.28, 0.14, "GO:0003674 (Repaired)", "0.62 -> 0.89 (+27.0% Elevated)", "#fef3c7", "#d97706", "#78350f")
    draw_box(ax, 0.62, 0.40, 0.28, 0.14, "GO:0003676 (Repaired)", "0.48 -> 0.89 (+41.0% Elevated)", "#fef3c7", "#d97706", "#78350f")
    draw_box(ax, 0.62, 0.14, 0.28, 0.14, "GO:0003677 (Child)", "DNA Binding | P = 0.89 (Anchored)", "#ecfdf5", "#059669", "#065f46")
    draw_arrow(ax, 0.76, 0.65, 0.76, 0.54, color="#059669")
    draw_arrow(ax, 0.76, 0.40, 0.76, 0.28, color="#059669")

    plt.tight_layout()
    fig.savefig(OUT / "fig_dag_concept.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    build_architecture_diagram()
    build_dag_repair_diagram()
    print("Generated fig0_architecture.png and fig_dag_concept.png")
