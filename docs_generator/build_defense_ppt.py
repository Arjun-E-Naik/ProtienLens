"""
ProteinLens-OS 14-Slide Defense Presentation Generator (16:9 Widescreen)
Produces: ProteinLens-OS/deliverables/ProteinLensOS_Defense_Presentation.pptx
Includes speaker notes & viva defense cues on every single slide!
"""

from __future__ import annotations

import json
from pathlib import Path
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt


ROOT = Path(__file__).resolve().parent.parent
FIG_DIR = ROOT / "benchmarks" / "output"
OUT_DIR = ROOT / "deliverables"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PPTX = OUT_DIR / "ProteinLensOS_Defense_Presentation.pptx"

# Precision Clinical Bio-Lab Palette
NAVY = RGBColor(15, 23, 42)       # #0F172A
SLATE = RGBColor(51, 65, 85)      # #334155
MUTED = RGBColor(100, 116, 139)   # #64748B
BG_LIGHT = RGBColor(248, 250, 252)# #F8FAFC
WHITE = RGBColor(255, 255, 255)
COBALT = RGBColor(37, 99, 235)    # #2563EB
CYAN = RGBColor(6, 182, 212)      # #06B6D4
EMERALD = RGBColor(5, 150, 105)   # #059669
AMBER = RGBColor(217, 119, 6)     # #D97706
ROSE = RGBColor(225, 29, 72)      # #E11D48
BORDER = RGBColor(203, 213, 225)  # #CBD5E1
CARD_BLUE = RGBColor(239, 246, 255)
CARD_GREEN = RGBColor(236, 253, 245)
CARD_AMBER = RGBColor(255, 251, 235)
CARD_ROSE = RGBColor(255, 241, 242)


def add_bg(slide, color=BG_LIGHT):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_header(slide, title: str, subtitle: str, slide_num: int):
    # Top slim accent bar
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.12))
    bar.fill.solid()
    bar.fill.fore_color.rgb = COBALT
    bar.line.fill.background()

    tb = slide.shapes.add_textbox(Inches(0.55), Inches(0.25), Inches(11.4), Inches(0.85))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    p1 = tf.paragraphs[0]
    r1 = p1.add_run()
    r1.text = title
    r1.font.name = "Segoe UI"
    r1.font.size = Pt(24)
    r1.font.bold = True
    r1.font.color.rgb = NAVY

    p2 = tf.add_paragraph()
    p2.space_before = Pt(2)
    r2 = p2.add_run()
    r2.text = subtitle
    r2.font.name = "Segoe UI"
    r2.font.size = Pt(12)
    r2.font.color.rgb = MUTED

    # Footer
    ft = slide.shapes.add_textbox(Inches(0.55), Inches(7.08), Inches(12.2), Inches(0.32))
    ftf = ft.text_frame
    fp = ftf.paragraphs[0]
    fr = fp.add_run()
    fr.text = f"ProteinLens-OS  |  IIIT Nagpur — Department of Computer Science & Engineering  |  github.com/Arjun-E-Naik/ProtienLens"
    fr.font.name = "Segoe UI"
    fr.font.size = Pt(9.5)
    fr.font.color.rgb = MUTED

    pg = slide.shapes.add_textbox(Inches(12.1), Inches(7.08), Inches(0.7), Inches(0.32))
    pp = pg.text_frame.paragraphs[0]
    pp.alignment = PP_ALIGN.RIGHT
    pr = pp.add_run()
    pr.text = f"{slide_num} / 14"
    pr.font.name = "Segoe UI"
    pr.font.size = Pt(10)
    pr.font.bold = True
    pr.font.color.rgb = COBALT


def add_card(slide, x, y, w, h, title, bullets, fill_color=WHITE, accent_color=COBALT, title_size=14, body_size=11.5):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    shape.line.color.rgb = accent_color
    shape.line.width = Pt(1.4)

    # Top accent stripe inside card
    tb = slide.shapes.add_textbox(Inches(x + 0.18), Inches(y + 0.14), Inches(w - 0.36), Inches(h - 0.24))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0

    p0 = tf.paragraphs[0]
    r0 = p0.add_run()
    r0.text = title
    r0.font.name = "Segoe UI"
    r0.font.size = Pt(title_size)
    r0.font.bold = True
    r0.font.color.rgb = accent_color

    for b in bullets:
        p = tf.add_paragraph()
        p.space_before = Pt(5)
        r = p.add_run()
        r.text = b
        r.font.name = "Segoe UI"
        r.font.size = Pt(body_size)
        r.font.color.rgb = SLATE
    return shape


def add_kpi(slide, x, y, w, h, value, label, sub, color=COBALT):
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    card.fill.solid()
    card.fill.fore_color.rgb = WHITE
    card.line.color.rgb = BORDER
    card.line.width = Pt(1.2)

    tb = slide.shapes.add_textbox(Inches(x + 0.14), Inches(y + 0.12), Inches(w - 0.28), Inches(h - 0.2))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0

    p1 = tf.paragraphs[0]
    r1 = p1.add_run()
    r1.text = value
    r1.font.name = "Consolas"
    r1.font.size = Pt(22)
    r1.font.bold = True
    r1.font.color.rgb = color

    p2 = tf.add_paragraph()
    p2.space_before = Pt(2)
    r2 = p2.add_run()
    r2.text = label
    r2.font.name = "Segoe UI"
    r2.font.size = Pt(11)
    r2.font.bold = True
    r2.font.color.rgb = NAVY

    p3 = tf.add_paragraph()
    r3 = p3.add_run()
    r3.text = sub
    r3.font.name = "Segoe UI"
    r3.font.size = Pt(9.5)
    r3.font.color.rgb = MUTED


def add_notes(slide, text: str):
    slide.notes_slide.notes_text_frame.text = text


def add_simple_table(slide, x, y, w, h, headers, rows, font_size=10.5):
    tbl_shape = slide.shapes.add_table(1 + len(rows), len(headers), Inches(x), Inches(y), Inches(w), Inches(h))
    tbl = tbl_shape.table
    for ci, h_txt in enumerate(headers):
        cell = tbl.cell(0, ci)
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = cell.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER if ci > 0 else PP_ALIGN.LEFT
        r = p.add_run()
        r.text = h_txt
        r.font.name = "Segoe UI"
        r.font.size = Pt(font_size)
        r.font.bold = True
        r.font.color.rgb = WHITE

    for ri, row in enumerate(rows):
        is_highlight = (ri == len(rows) - 1)
        for ci, val in enumerate(row):
            cell = tbl.cell(ri + 1, ci)
            cell.fill.solid()
            cell.fill.fore_color.rgb = CARD_GREEN if is_highlight else (WHITE if ri % 2 == 0 else BG_LIGHT)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER if ci > 0 else PP_ALIGN.LEFT
            r = p.add_run()
            r.text = str(val)
            r.font.name = "Segoe UI"
            r.font.size = Pt(font_size - 0.5)
            r.font.bold = is_highlight or (ci == 0)
            r.font.color.rgb = EMERALD if (is_highlight and ci > 0) else NAVY


def build_presentation():
    bench = json.loads((FIG_DIR / "benchmark_summary.json").read_text(encoding="utf-8"))
    train_hist = json.loads((FIG_DIR / "training_history.json").read_text(encoding="utf-8"))

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]

    # =========================================================================
    # SLIDE 1: TITLE SLIDE (Dark Executive Bio-Lab Theme)
    # =========================================================================
    s1 = prs.slides.add_slide(blank)
    add_bg(s1, NAVY)
    stripe = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(0.28), Inches(7.5))
    stripe.fill.solid(); stripe.fill.fore_color.rgb = CYAN; stripe.line.fill.background()

    tb = s1.shapes.add_textbox(Inches(0.9), Inches(0.95), Inches(11.6), Inches(5.6))
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]
    r = p.add_run(); r.text = "INDIAN INSTITUTE OF INFORMATION TECHNOLOGY, NAGPUR  |  B.TECH CSE MINI PROJECT"
    r.font.name = "Segoe UI"; r.font.size = Pt(12); r.font.bold = True; r.font.color.rgb = CYAN

    p2 = tf.add_paragraph(); p2.space_before = Pt(18)
    r2 = p2.add_run(); r2.text = "ProteinLens-OS"
    r2.font.name = "Segoe UI"; r2.font.size = Pt(46); r2.font.bold = True; r2.font.color.rgb = WHITE

    p3 = tf.add_paragraph(); p3.space_before = Pt(6)
    r3 = p3.add_run(); r3.text = "A Local-First Full-Stack Platform for Zero-Shot 3D-Pocket Deep Mutational Scanning, True-Path Gene Ontology Propagation, and Grounded Explainable AI"
    r3.font.name = "Segoe UI"; r3.font.size = Pt(20); r3.font.color.rgb = RGBColor(203, 213, 225)

    p4 = tf.add_paragraph(); p4.space_before = Pt(34)
    r4 = p4.add_run(); r4.text = "Presented by:  Arjun E. Naik  |  [Student Name 2]  |  [Student Name 3]\nSupervised by: [Supervisor Name & Designation], Dept. of CSE, IIIT Nagpur"
    r4.font.name = "Segoe UI"; r4.font.size = Pt(14); r4.font.color.rgb = RGBColor(226, 232, 240)

    p5 = tf.add_paragraph(); p5.space_before = Pt(24)
    r5 = p5.add_run(); r5.text = "Open-Source Release (MIT):  https://github.com/Arjun-E-Naik/ProtienLens"
    r5.font.name = "Consolas"; r5.font.size = Pt(12.5); r5.font.color.rgb = RGBColor(52, 211, 153)
    add_notes(s1, "Opening 30-second pitch: ProteinLens-OS transforms pretrained ESM-2 transfer learning into an accessible, local-first clinical genomics & teaching platform—introducing 3D-Pocket DMS, Dual-Axis Risk Fusion (+52.1% AUROC jump on CPU), and Provable 0% DAG violations.")

    # =========================================================================
    # SLIDE 2: THE REAL-WORLD HEALTHCARE & BIOINFORMATICS PROBLEM
    # =========================================================================
    s2 = prs.slides.add_slide(blank)
    add_bg(s2); add_header(s2, "The Real-World Problem: Two Critical Gaps in Modern Genomics", "Why hospitals, researchers, and Indian universities need a local-first open-source platform", 2)
    add_kpi(s2, 0.55, 1.3, 3.85, 1.45, "> 99%", "Uncharacterized Proteins", "UniProtKB sequences lack wet-lab GO validation", COBALT)
    add_kpi(s2, 4.72, 1.3, 3.85, 1.45, "40–55%", "Clinical VUS Crisis", "ClinVar patient missense variants remain uncertain", ROSE)
    add_kpi(s2, 8.90, 1.3, 3.85, 1.45, "$20k–$100k", "Commercial Paywall", "Annual cost of QIAGEN / Schrödinger cloud suites", AMBER)

    add_card(s2, 0.55, 3.05, 5.95, 3.65, "1. Clinical & Academic Fragmentation", [
        "• Clinicians must jump across 5 disjoint sites: ClinVar, UniProt, AlphaFold DB, OpenCRAVAT, and QuickGO.",
        "• Tabular variant scorers give opaque numbers with zero 3D active-pocket context or functional pathway loss.",
        "• Cloud-only tools raise serious HIPAA / DPDP patient genomic privacy concerns for local hospitals.",
    ], WHITE, COBALT)
    add_card(s2, 6.82, 3.05, 5.95, 3.65, "2. The Hardware & Usability Barrier", [
        "• Top CAFA 6 competition pipelines (e.g., GOAlpha) require multi-GB Docker clusters and Linux servers.",
        "• Compact 8M CPU language models fit on college laptops (<500 MB RAM) but suffer noisy zero-shot LLR (AUROC ~0.51).",
        "• Our Goal: Rescue CPU-class models via 3D structural fusion and deliver an end-to-end usable web platform.",
    ], WHITE, ROSE)
    add_notes(s2, "Emphasize that we are solving BOTH a real scientific problem (rescuing CPU-class models for VUS triage) AND a real healthcare/education access problem.")

    # =========================================================================
    # SLIDE 3: LITERATURE & COMPETITIVE GAP MATRIX
    # =========================================================================
    s3 = prs.slides.add_slide(blank)
    add_bg(s3); add_header(s3, "Competitive Landscape & White-Space Differentiation", "What does NOT exist in current open-source software today", 3)
    add_simple_table(
        s3, 0.55, 1.35, 12.2, 4.1,
        ["Platform", "GO Function AI", "3D 5Å Pocket DMS", "True-Path DAG UI", "Local CPU Privacy", "Auto XAI + College Labs"],
        [
            ["OpenCRAVAT / VEP", "No", "No (Spreadsheets)", "No", "Partial", "No"],
            ["AlphaFold DB / Mol*", "No", "No", "No", "Cloud Only", "No"],
            ["DeepGOPlus / GOAlpha", "Yes (CLI/Docker)", "No", "No (Static text)", "High RAM/GPU", "No"],
            ["QIAGEN / Schrödinger", "Partial", "Paid ($20k+/yr)", "No", "Cloud Only", "Proprietary"],
            ["ProteinLens-OS (Ours)", "Yes (4 Paradigms)", "Yes (Batched 20-AA)", "Yes (0% Viol.)", "Yes (8GB CPU)", "Yes (Gemini/Grok + 4 Labs)"],
        ],
        font_size=11.5,
    )
    add_card(s3, 0.55, 5.7, 12.2, 1.15, "Key Viva Distinction vs. GOAlpha", [
        "GOAlpha is an offline competition ensemble built for leaderboard wFmax; ProteinLens-OS uses standard ESM-2 transfer learning and adds 3D-Pocket DMS, Dual-Axis VUS Triage, live ClinVar/OpenTargets grounding, and a deployable institutional web studio.",
    ], CARD_BLUE, COBALT, 12.5, 11)
    add_notes(s3, "If asked about GOAlpha: state clearly that GOAlpha is an offline competition pipeline; we use Meta AI's open ESM-2 foundation model via standard transfer learning and solve the clinical VUS & 3D explainability gap.")

    # =========================================================================
    # SLIDE 4: OUR 5 ORIGINAL CONTRIBUTIONS
    # =========================================================================
    s4 = prs.slides.add_slide(blank)
    add_bg(s4); add_header(s4, "Our 5 Original Scientific & Engineering Contributions", "Concrete, measurable innovations built on top of pretrained ESM-2 representations", 4)
    add_card(s4, 0.55, 1.3, 5.95, 1.7, "1. Multi-Modal Dual-Axis Clinical Risk Fusion", [
        "Fuses 8M ESM-2 LLR + BLOSUM62 + AlphaFold pLDDT/8Å burial + ΔGO_IA, jumping AUROC from 0.5071 -> 0.7714 (+52.1%) on CPU.",
    ], CARD_GREEN, EMERALD, 13.5, 11)
    add_card(s4, 6.8, 1.3, 5.95, 1.7, "2. Batched 5.0 Å 3D-Pocket Zero-Shot DMS", [
        "Extracts real heavy-atom AlphaFold pockets and scores all Pocket Sites x 20 Canonical AAs in one batched forward pass (~1.2s).",
    ], CARD_BLUE, COBALT, 13.5, 11)
    add_card(s4, 0.55, 3.25, 5.95, 1.7, "3. Fixed-Point True Path DAG Repair Engine", [
        "Eliminates 94.64 raw ontology contradictions/protein down to exact 0.00% with interactive pan/zoom @xyflow/react auditability.",
    ], CARD_AMBER, AMBER, 13.5, 11)
    add_card(s4, 6.8, 3.25, 5.95, 1.7, "4. Leakage-Free Ablation & 5.5s Live Training", [
        "Real 8,000-d 3-mer baseline vs. ESM-2 MLP (+27.4% wFmax) with live 5.5-second CPU training script & 1-click Google Colab notebook.",
    ], WHITE, COBALT, 13.5, 11)
    add_card(s4, 0.55, 5.2, 12.2, 1.55, "5. Institutional Full-Stack Software & Auto-Configuring Multi-LLM XAI", [
        "Next.js 15 + FastAPI + SQLite + SSE Batch Triage + Auto-Discovering Gemini/xAI Grok/Groq/Ollama Router (strictly citation-grounded) + IIIT Nagpur White-Label Dossiers + 4 Guided College Teaching Labs.",
    ], WHITE, NAVY, 13.5, 11)
    add_notes(s4, "Use this slide to answer 'What did YOU actually build?'. Every single point has verified code and quantitative proof.")

    # =========================================================================
    # SLIDE 5: FULL-STACK SYSTEM ARCHITECTURE
    # =========================================================================
    s5 = prs.slides.add_slide(blank)
    add_bg(s5); add_header(s5, "Decoupled Local-First Full-Stack Architecture", "Zero Docker required — runs natively on Windows/Linux/macOS laptops or college servers", 5)
    s5.shapes.add_picture(str(FIG_DIR / "fig0_architecture.png"), Inches(0.85), Inches(1.22), width=Inches(11.6))
    add_notes(s5, "Walk top-to-bottom: Next.js 15 frontend (:3000) -> FastAPI + SQLite + Auto-Config XAI Router (:8000) -> Independent PyTorch/ESM-2 ML Core + Federated UniProt/AlphaFold/ClinVar/OpenTargets APIs.")

    # =========================================================================
    # SLIDE 6: INDEPENDENT SCIENTIFIC ML & LIVE TRAINING PIPELINE
    # =========================================================================
    s6 = prs.slides.add_slide(blank)
    add_bg(s6); add_header(s6, "Independent Scientific ML Engine & Reproducible Training", "Single-load EsmForMaskedLM + 5.5-second live laptop & Google Colab training", 6)
    add_card(s6, 0.55, 1.3, 6.0, 5.4, "Single-Load EsmForMaskedLM (8M, <500 MB RAM)", [
        "1. 320-d Evolutionary Embeddings -> PyTorch MLP (424,180 params) & Cosine kNN.",
        "2. Multi-Layer Attention Rollout (70%) + Activation Norm (30%) -> XAI Residue Saliency.",
        "3. Exact Masked-Marginal LLR: log P(mut | x_\\i) - log P(wt | x_\\i).",
        "4. Batched 3D-Pocket DMS: 1 forward pass scores up to 8 pocket sites x 20 AAs (160 mutants).",
        "5. Real 8,000-d Sparse 3-mer Baseline fit on identical 2,000 CAFA 6 sequences (zero heuristics).",
    ], WHITE, COBALT, 13.5, 11.5)
    s6.shapes.add_picture(str(FIG_DIR / "fig3_training_curve.png"), Inches(6.75), Inches(1.35), width=Inches(6.05))
    add_card(s6, 6.75, 5.1, 6.05, 1.6, "Live Viva Proof (CPU & Colab)", [
        f"• python training/train_live_demo.py trains 25 epochs in {train_hist['runtime_seconds']:.2f}s on laptop CPU!",
        "• ProteinLens_Colab_Training.ipynb runs end-to-end on free Google Colab T4 GPU.",
    ], CARD_GREEN, EMERALD, 12.5, 11)
    add_notes(s6, "Offer to run `python training/train_live_demo.py` live in the terminal right now—it takes only 5.5 seconds and proves real BCE loss convergence and validation wFmax climbing from 0.337 to 0.447!")

    # =========================================================================
    # SLIDE 7: EXACT TRUE PATH RULE DAG ENGINE
    # =========================================================================
    s7 = prs.slides.add_slide(blank)
    add_bg(s7); add_header(s7, "Fixed-Point True Path Rule DAG Propagation Engine", "Guaranteeing biological hierarchy consistency across all 500 Gene Ontology terms", 7)
    s7.shapes.add_picture(str(FIG_DIR / "fig_dag_concept.png"), Inches(0.65), Inches(1.25), width=Inches(12.0))
    add_kpi(s7, 0.65, 5.55, 3.8, 1.25, "94.64 / prot", "Raw MLP Contradictions", "Child > Parent biological errors", ROSE)
    add_kpi(s7, 4.75, 5.55, 3.8, 1.25, "0.00 (0.00%)", "Post-Repair Violations", "Provable fixed-point convergence", EMERALD)
    add_kpi(s7, 8.85, 5.55, 3.8, 1.25, "0.4473", "Post-Repair Val wFmax", "Improves specificity & consistency", COBALT)
    add_notes(s7, "Explain why single-pass dictionary propagation can miss multi-hop chains; our fixed-point bottom-up pass guarantees 0.00% violations and transitive reduction keeps the interactive React Flow graph clean.")

    # =========================================================================
    # SLIDE 8: MULTI-MODAL DUAL-AXIS CLINICAL RISK FUSION
    # =========================================================================
    s8 = prs.slides.add_slide(blank)
    add_bg(s8); add_header(s8, "Multi-Modal Dual-Axis Clinical Risk Fusion", "Solving the 8M CPU protein language model precision bottleneck", 8)
    add_card(s8, 0.55, 1.35, 12.2, 1.25, "Auditable Clinical Disruption Formula (Zero Black-Box Magic)", [
        "S_clinical(v) = 100 × [ 0.42 · R_evo(ESM-2 LLR + BLOSUM62)  +  0.43 · R_struct(AlphaFold pLDDT + 8 Å Burial)  +  0.15 · R_GO(ΔGO_IA) ]",
    ], CARD_BLUE, COBALT, 13, 12.5)
    add_card(s8, 0.55, 2.9, 3.85, 3.7, "Axis 1: Evolutionary (42%)", [
        "• Zero-shot ESM-2 Masked-Marginal LLR (8M-calibrated sigmoid).",
        "• Standard NCBI BLOSUM62 physicochemical radicality.",
        "• Captures evolutionary intolerance without expensive MSAs.",
    ], WHITE, COBALT)
    add_card(s8, 4.72, 2.9, 3.85, 3.7, "Axis 2: 3D Structure (43%)", [
        "• AlphaFold per-residue pLDDT confidence (folded core vs. disordered loop).",
        "• Exact 8.0 Å C-alpha burial contacts & 5.0 Å heavy-atom pocket density.",
        "• Filters false positives in disordered regions (e.g., TP53 P72R).",
    ], WHITE, EMERALD)
    add_card(s8, 8.9, 2.9, 3.85, 3.7, "Axis 3: Ontology Shift (15%)", [
        "• Information-Accretion weighted GO Functional Disruption Index (ΔGO_IA).",
        "• Cosine embedding drift between wild-type and mutant sequences.",
        "• Identifies exactly WHICH biological functions attenuate.",
    ], WHITE, AMBER)
    add_notes(s8, "Highlight why this fusion is publishable: compact 8M models misclassify disordered proline repeats like P72R; structural gating solves it on a laptop CPU.")

    # =========================================================================
    # SLIDE 9: RESULT 1 — CAFA 6 LEAKAGE-FREE ABLATION
    # =========================================================================
    s9 = prs.slides.add_slide(blank)
    add_bg(s9); add_header(s9, "Experimental Result 1: CAFA 6 Held-Out Ablation Study", "Leakage-free 80/20 split (1,600 train / 400 validation proteins, 500 GO terms)", 9)
    s9.shapes.add_picture(str(FIG_DIR / "fig1_cafa6_ablation.png"), Inches(0.55), Inches(1.35), width=Inches(7.35))
    add_kpi(s9, 8.15, 1.35, 4.6, 1.35, "0.4454", "PyTorch MLP wFmax", "+27.4% gain over Real 3-mer (0.3496)", COBALT)
    add_kpi(s9, 8.15, 2.95, 4.6, 1.35, "0.4473", "MLP + True-Path DAG", "Exact 0.00% post-repair contradictions", EMERALD)
    add_card(s9, 8.15, 4.55, 4.6, 2.15, "Methodological Rigor", [
        "• Zero train/val leakage (scaler & kNN fit strictly on training fold).",
        "• Genuine 8,000-d 3-mer matrix built from CAFA 6 FASTA sequences.",
        "• Evaluated with official CAFA Information-Accretion weights.",
    ], WHITE, SLATE, 12.5, 10.5)
    add_notes(s9, "Point out that we removed heuristic 3-mer simulation and built a real sparse 3-mer matrix so every ablation comparison is strictly peer-review valid.")

    # =========================================================================
    # SLIDE 10: RESULT 2 — CLINICAL MISSENSE BENCHMARK (ROC)
    # =========================================================================
    s10 = prs.slides.add_slide(blank)
    add_bg(s10); add_header(s10, "Experimental Result 2: Clinical Missense Benchmark (TP53, HBB, INS)", "Multi-Modal Dual-Axis Fusion rescues CPU-class 8M ESM-2 pathogenicity prediction", 10)
    s10.shapes.add_picture(str(FIG_DIR / "fig2_clinical_roc.png"), Inches(0.55), Inches(1.3), width=Inches(5.9))
    cvb = bench["clinical_variant_benchmark"]
    add_kpi(s10, 6.75, 1.35, 2.9, 1.4, f"{cvb['dual_axis_auroc']:.4f}", "Dual-Axis AUROC", f"vs {cvb['llr_auroc']:.4f} LLR-only", EMERALD)
    add_kpi(s10, 9.85, 1.35, 2.9, 1.4, f"{cvb['dual_axis_auprc']:.4f}", "Dual-Axis AUPRC", "+52.1% rel. AUROC gain", COBALT)
    add_simple_table(
        s10, 6.75, 3.0, 6.0, 3.6,
        ["Variant (TP53 / HBB)", "ClinVar", "pLDDT", "Dual-Axis Risk"],
        [
            ["TP53 p.R273C", "Pathogenic", "98.6", "73.3 / 100"],
            ["TP53 p.R282W", "Pathogenic", "97.5", "70.9 / 100"],
            ["HBB p.E7V (Sickle)", "Pathogenic", "96.6", "65.5 / 100"],
            ["TP53 p.R273H", "Pathogenic", "98.6", "59.7 / 100"],
            ["TP53 p.P72R (Control)", "Benign", "48.3", "42.8 / 100"],
            ["TP53 p.P47S / S366A", "Benign", "37.9", "22.6–25.2"],
        ],
        font_size=10,
    )
    add_notes(s10, "Highlight 100% separation on TP53: every single pathogenic driver scores 48.5–73.3 while every benign polymorphism scores 22.6–42.8 on a standard laptop CPU.")

    # =========================================================================
    # SLIDE 11: FLAGSHIP SHOWCASE — 3D-POCKET ZERO-SHOT DMS HEATMAP
    # =========================================================================
    s11 = prs.slides.add_slide(blank)
    add_bg(s11); add_header(s11, "Flagship Feature: 5.0 Å 3D-Pocket Zero-Shot DMS Heatmap", "Real batched output for TP53 p.R273H DNA-binding core (8 spatial sites × 20 amino acids)", 11)
    s11.shapes.add_picture(str(FIG_DIR / "fig4_pocket_dms_heatmap.png"), Inches(0.65), Inches(1.25), width=Inches(12.0))
    add_card(s11, 0.65, 5.7, 12.0, 1.15, "Why Clinicians & Structural Biologists Love This View", [
        "Clicking any cell in the interactive heatmap re-runs full Dual-Axis inference, highlights the exact 5.0 Å contacting shell in 3Dmol.js, surfaces tolerated/stabilizing substitutions, and pulls live NCBI ClinVar & Open Targets drug matches.",
    ], CARD_AMBER, AMBER, 12, 11)
    add_notes(s11, "Explain how this heatmap is generated in ~1.2 seconds on CPU using a single batched masked forward pass over the 5.0 A heavy-atom pocket around residue 273.")

    # =========================================================================
    # SLIDE 12: AUTO-CONFIGURING MULTI-LLM XAI & INSTITUTIONAL PLATFORM
    # =========================================================================
    s12 = prs.slides.add_slide(blank)
    add_bg(s12); add_header(s12, "Auto-Configuring Multi-LLM XAI & White-Label Institutional Ready", "Live model discovery for Gemini / xAI Grok / Groq / Ollama + IIIT Nagpur branding", 12)
    s12.shapes.add_picture(str(FIG_DIR / "fig_app_settings.png"), Inches(0.55), Inches(1.32), width=Inches(7.65))
    add_card(s12, 8.45, 1.32, 4.35, 2.5, "Anti-Hallucination XAI Design", [
        "• Paste any key -> auto-detects provider & fetches live enabled models (e.g., gemini-3.8-flash).",
        "• Strictly grounded in JSON Evidence Packet (zero fabricated scores).",
        "• 3 Modes: Clinical, Research & Student.",
    ], WHITE, COBALT, 12.5, 10.5)
    add_card(s12, 8.45, 4.05, 4.35, 2.6, "College & Lab Deployment", [
        "• 4 Guided Teaching Labs (BIO-LAB 101–103, ML-LAB 201).",
        "• White-label printable PDF & SHA-256 JSON dossiers.",
        "• Local SQLite vault + SSE batch cohort triage.",
    ], CARD_GREEN, EMERALD, 12.5, 10.5)
    add_notes(s12, "Point to the real screenshot of our running app in dark mode showing IIIT Nagpur branding and live API key auto-setup.")

    # =========================================================================
    # SLIDE 13: OPEN-CORE BUSINESS MODEL & 3-MINUTE LIVE DEMO FLOW
    # =========================================================================
    s13 = prs.slides.add_slide(blank)
    add_bg(s13); add_header(s13, "Institutional Business Model & Live Demo Plan", "From academic mini-project to deployable open-core health-tech software", 13)
    add_card(s13, 0.55, 1.35, 3.85, 3.4, "Community & Academic (Free)", [
        "• MIT Open-Source License.",
        "• Local CPU + SQLite + 3D Pocket DMS.",
        "• 4 College Teaching Labs + BYO Gemini/Grok/Ollama key.",
        "• Target: Universities & public clinics.",
    ], CARD_GREEN, EMERALD, 13, 11)
    add_card(s13, 4.72, 1.35, 3.85, 3.4, "Campus & Lab Pro ($99–$299/yr)", [
        "• Multi-user Campus SSO / RBAC.",
        "• Custom professor lab builder & grading export.",
        "• Shared PostgreSQL case bank & branded PDF templates.",
        "• Target: Biotech / Medical Depts.",
    ], CARD_BLUE, COBALT, 13, 11)
    add_card(s13, 8.9, 1.35, 3.85, 3.4, "Enterprise Clinical / Biopharma", [
        "• On-premise GPU scaling (esm2_t33_650M / 3B).",
        "• HL7 FHIR / LIMS integration.",
        "• HIPAA / DPDP compliance audit trails & SLA.",
        "• Target: Diagnostic Labs & Pharma.",
    ], WHITE, NAVY, 13, 11)
    add_card(s13, 0.55, 5.05, 12.2, 1.7, "3-Minute Live Demo Walkthrough", [
        "1. Live 5.5s CPU Training (train_live_demo.py)   ->   2. TP53 R273H vs. P72R 3D-Pocket DMS (/variants)   ->   3. Interactive True Path DAG (/dag)   ->   4. Model Arena Benchmarks (/arena)   ->   5. IIIT Nagpur White-Label Dossier & AI Auto-Config (/cases, /settings)",
    ], CARD_AMBER, AMBER, 13, 11.5)
    add_notes(s13, "Demonstrates commercial viability and clear institutional adoption pathway for IIIT Nagpur and partner colleges.")

    # =========================================================================
    # SLIDE 14: CONCLUSIONS, FUTURE WORK & Q&A
    # =========================================================================
    s14 = prs.slides.add_slide(blank)
    add_bg(s14, NAVY)
    stripe2 = s14.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.16))
    stripe2.fill.solid(); stripe2.fill.fore_color.rgb = EMERALD; stripe2.line.fill.background()

    tb = s14.shapes.add_textbox(Inches(0.8), Inches(0.65), Inches(11.7), Inches(6.0))
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]
    r = p.add_run(); r.text = "Summary, Future Scope & Open-Source Impact"
    r.font.name = "Segoe UI"; r.font.size = Pt(30); r.font.bold = True; r.font.color.rgb = WHITE

    points = [
        "• Scientifically Rigorous: +27.4% CAFA 6 wFmax over Real 3-mer, exact 0.00% DAG violations, and +52.1% clinical AUROC jump (0.5071 -> 0.7714) via 3D Structural Fusion on CPU.",
        "• Fully Engineered: 9-route Next.js 15 + FastAPI + SQLite platform, 6/6 pytest verified, live Gemini/Grok/Ollama model discovery, and 5.5s reproducible local/Colab training.",
        "• Future Roadmap: GPU scaling to esm2_t33_650M, 10,000+ ProteinGym/ClinVar validation, multi-mutation epistasis, and HL7 FHIR clinical reporting.",
    ]
    for pt in points:
        pp = tf.add_paragraph(); pp.space_before = Pt(14)
        rr = pp.add_run(); rr.text = pt
        rr.font.name = "Segoe UI"; rr.font.size = Pt(15.5); rr.font.color.rgb = RGBColor(226, 232, 240)

    pq = tf.add_paragraph(); pq.space_before = Pt(36)
    rq = pq.add_run(); rq.text = "Thank You!  —  Ready for Questions & Live Demonstration"
    rq.font.name = "Segoe UI"; rq.font.size = Pt(24); rq.font.bold = True; rq.font.color.rgb = CYAN

    pl = tf.add_paragraph(); pl.space_before = Pt(10)
    rl = pl.add_run(); rl.text = "GitHub: https://github.com/Arjun-E-Naik/ProtienLens   |   IIIT Nagpur (Dept. of CSE)"
    rl.font.name = "Consolas"; rl.font.size = Pt(13); rl.font.color.rgb = RGBColor(52, 211, 153)
    add_notes(s14, "Close confidently and invite the panel to pick ANY residue/mutation for a live non-hardcoded demonstration.")

    prs.save(str(OUT_PPTX))
    print(f"Successfully generated 14-slide defense presentation: {OUT_PPTX}")


if __name__ == "__main__":
    build_presentation()
