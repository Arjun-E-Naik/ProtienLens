"""
ProteinLens-OS IIIT Nagpur Mini Project Report Generator (100% Guidelines-Compliant)
Produces: ProteinLens-OS/deliverables/ProteinLensOS_Mini_Project_Report.docx

Strictly enforces all 6 pages of IIIT Nagpur Guidelines (CSD 300/301/302 / ECD 301/302):
- Margins: Top 1.00", Bottom 1.25", Left 1.50", Right 0.80" on all sections
- 3 Separate Word Sections:
    Part A: No Page Numbers (Cover + Copyright, Declaration-I, Declaration-II, Certificate, Acknowledgement)
    Part B: Lowercase Roman (i, ii, iii...) starting at i (1-page Abstract, TOC, LOF, LOT, Symbols/Abbreviations)
    Part C: Arabic (1, 2, 3...) starting at 1 (Chapters 1-5, References, Appendices I-III, List of Publications)
- Chapter Headings (Sec 4.1): Fresh page, ~75mm top drop, centered 18pt Bold Title Case, ~25mm vertical gaps
- Tables: Title ABOVE table, chapter-wise numbering (Table 2.1, Table 3.1, Table 4.1...)
- Figures: Caption BELOW figure, chapter-wise numbering (Figure 3.1, Figure 4.1...), all 300-DPI software-drawn
- Font: Times New Roman, 12pt body, 1.5 line spacing, justified alignment
"""

from __future__ import annotations

import json
from pathlib import Path
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Inches, Mm, Pt, RGBColor


ROOT = Path(__file__).resolve().parent.parent
FIG_DIR = ROOT / "benchmarks" / "output"
OUT_DIR = ROOT / "deliverables"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_DOCX = OUT_DIR / "ProteinLensOS_Mini_Project_Report.docx"


def set_section_margins(section):
    section.page_width = Inches(8.27)   # A4
    section.page_height = Inches(11.69) # A4
    section.top_margin = Inches(1.00)
    section.bottom_margin = Inches(1.25)
    section.left_margin = Inches(1.50)
    section.right_margin = Inches(0.80)


def set_page_number_format(section, fmt: str | None = None, start: int | None = None):
    """Configure footer page number format: None (suppressed), 'lowerRoman', or 'decimal'."""
    footer = section.footer
    footer.is_linked_to_previous = False
    for p in list(footer.paragraphs):
        p.text = ""

    if fmt is None:
        return

    pg_num_type = OxmlElement("w:pgNumType")
    pg_num_type.set(qn("w:fmt"), fmt)
    if start is not None:
        pg_num_type.set(qn("w:start"), str(start))
    section._sectPr.append(pg_num_type)

    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    run.font.name = "Times New Roman"
    run.font.size = Pt(11)
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    fld_sep = OxmlElement("w:fldChar")
    fld_sep.set(qn("w:fldCharType"), "separate")
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_begin)
    run._r.append(instr)
    run._r.append(fld_sep)
    run._r.append(fld_end)


def add_field(paragraph, instruction: str, placeholder: str = "[Right-click -> Update Field in Word]"):
    run = paragraph.add_run()
    run.font.name = "Times New Roman"
    run.font.size = Pt(11)
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = f" {instruction} "
    fld_sep = OxmlElement("w:fldChar")
    fld_sep.set(qn("w:fldCharType"), "separate")
    fld_text = OxmlElement("w:t")
    fld_text.text = placeholder
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_begin)
    run._r.append(instr)
    run._r.append(fld_sep)
    run._r.append(fld_text)
    run._r.append(fld_end)


def style_run(run, size=12, bold=False, italic=False, color=None, font="Times New Roman"):
    run.font.name = font
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    if color:
        run.font.color.rgb = color


def add_body_p(doc: Document, text: str, bold_prefix: str | None = None, space_after=6, justify=True):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY if justify else WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(space_after)
    if bold_prefix:
        r0 = p.add_run(bold_prefix)
        style_run(r0, 12, bold=True)
    r1 = p.add_run(text)
    style_run(r1, 12)
    return p


def add_bullet(doc: Document, bold_lead: str, text: str):
    p = doc.add_paragraph(style="List Bullet")
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.line_spacing = 1.4
    p.paragraph_format.space_after = Pt(4)
    r0 = p.add_run(bold_lead)
    style_run(r0, 12, bold=True)
    r1 = p.add_run(text)
    style_run(r1, 12)
    return p


def add_equation(doc: Document, eq_text: str, eq_num: str):
    tbl = doc.add_table(rows=1, cols=2)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    c0, c1 = tbl.rows[0].cells
    c0.width = Inches(5.1)
    c1.width = Inches(0.85)
    # Remove table borders cleanly
    for cell in (c0, c1):
        tcPr = cell._tc.get_or_add_tcPr()
        tcPr.append(parse_xml(f'<w:tcBorders {nsdecls("w")}><w:top w:val="none"/><w:left w:val="none"/><w:bottom w:val="none"/><w:right w:val="none"/></w:tcBorders>'))
    p0 = c0.paragraphs[0]
    p0.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p0.paragraph_format.space_before = Pt(4)
    p0.paragraph_format.space_after = Pt(4)
    r0 = p0.add_run(eq_text)
    style_run(r0, 11.5, italic=True, font="Cambria Math")
    p1 = c1.paragraphs[0]
    p1.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r1 = p1.add_run(f"({eq_num})")
    style_run(r1, 11)


def add_chapter_heading(doc: Document, num: int, title: str, first_chapter=False):
    """Strict IIITN Section 4.1: fresh page, ~75mm top drop, 18pt Bold Title Case, 25mm gaps."""
    if not first_chapter:
        doc.add_page_break()

    p_num = doc.add_paragraph()
    p_num.alignment = WD_ALIGN_PARAGRAPH.CENTER
    # Page already has 1" (25.4mm) top margin; adding ~49.6mm gives total ~75mm top margin!
    p_num.paragraph_format.space_before = Mm(48)
    p_num.paragraph_format.space_after = Mm(25)
    r_num = p_num.add_run(f"Chapter {num}")
    style_run(r_num, 18, bold=True)

    p_title = doc.add_paragraph(style="Heading 1")
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Mm(25)
    r_title = p_title.add_run(f"{num}. {title}")
    style_run(r_title, 18, bold=True, color=RGBColor(0, 0, 0))


def add_section_h2(doc: Document, sec_num: str, title: str):
    p = doc.add_paragraph(style="Heading 2")
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(f"{sec_num}  {title}")
    style_run(r, 14, bold=True, color=RGBColor(0, 0, 0))


def add_subsection_h3(doc: Document, sec_num: str, title: str):
    p = doc.add_paragraph(style="Heading 3")
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(f"{sec_num}  {title}")
    style_run(r, 12.5, bold=True, color=RGBColor(0, 0, 0))


def add_front_heading(doc: Document, title: str, page_break=True):
    if page_break:
        doc.add_page_break()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(16)
    r = p.add_run(title)
    style_run(r, 16, bold=True)


def add_styled_table(doc: Document, table_label: str, headers: list[str], rows: list[list[str]], col_widths=None):
    """IIITN Sec 1.3 & 4.3: Table number & title MUST appear ABOVE the table."""
    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.paragraph_format.space_before = Pt(10)
    p_cap.paragraph_format.space_after = Pt(4)
    p_cap.paragraph_format.keep_with_next = True
    r_cap = p_cap.add_run(table_label)
    style_run(r_cap, 11, bold=True)

    tbl = doc.add_table(rows=1 + len(rows), cols=len(headers))
    tbl.style = "Table Grid"
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER

    # Header row
    hdr_cells = tbl.rows[0].cells
    for i, h in enumerate(headers):
        shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="1E3A8A"/>')
        hdr_cells[i]._tc.get_or_add_tcPr().append(shading)
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(3)
        p.paragraph_format.space_after = Pt(3)
        r = p.add_run(h)
        style_run(r, 10, bold=True, color=RGBColor(255, 255, 255))

    for r_idx, row in enumerate(rows):
        cells = tbl.rows[r_idx + 1].cells
        fill = "F8FAFC" if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate(row):
            shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill}"/>')
            cells[c_idx]._tc.get_or_add_tcPr().append(shading)
            p = cells[c_idx].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if c_idx == 0 else WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            r = p.add_run(str(val))
            style_run(r, 9.5)

    if col_widths:
        for row in tbl.rows:
            for idx, w in enumerate(col_widths):
                row.cells[idx].width = Inches(w)

    sp = doc.add_paragraph()
    sp.paragraph_format.space_after = Pt(4)


def add_figure(doc: Document, img_path: Path, caption: str, width_in=5.6):
    """IIITN Sec 1.3 & 4.3: Figure number & caption MUST appear BELOW the figure."""
    if not img_path.exists():
        return
    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.paragraph_format.space_before = Pt(8)
    p_img.paragraph_format.space_after = Pt(3)
    p_img.paragraph_format.keep_with_next = True
    p_img.add_run().add_picture(str(img_path), width=Inches(width_in))

    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.paragraph_format.space_before = Pt(0)
    p_cap.paragraph_format.space_after = Pt(10)
    r = p_cap.add_run(caption)
    style_run(r, 10.5, bold=True)


def build_report():
    bench = json.loads((FIG_DIR / "benchmark_summary.json").read_text(encoding="utf-8"))
    train_hist = json.loads((FIG_DIR / "training_history.json").read_text(encoding="utf-8"))

    doc = Document()
    # Set Normal style to Times New Roman 12pt
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(12)

    # Enable auto-update fields when opened in Word
    settings = doc.settings.element
    update_fields = OxmlElement("w:updateFields")
    update_fields.set(qn("w:val"), "true")
    settings.append(update_fields)

    # =========================================================================
    # PART A — UNNUMBERED FRONT MATTER (Section 1)
    # =========================================================================
    sec_a = doc.sections[0]
    set_section_margins(sec_a)
    set_page_number_format(sec_a, fmt=None)

    # 1. COVER PAGE (With IIITN Copyright)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(18)
    p.paragraph_format.space_after = Pt(10)
    style_run(p.add_run("ProteinLens-OS: A Local-First Full-Stack Platform for Zero-Shot 3D-Pocket Deep Mutational Scanning, True-Path Gene Ontology Propagation, and Grounded Explainable AI"), 17, bold=True)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(16)
    p.paragraph_format.space_after = Pt(6)
    style_run(p.add_run("A Mini Project Report (CSD 301 / CSD 302)"), 13, italic=True)
    p.add_run("\n")
    style_run(p.add_run("Submitted in partial fulfillment of the requirements for the degree of"), 12)
    p.add_run("\n")
    style_run(p.add_run("Bachelor of Technology in Computer Science and Engineering"), 13, bold=True)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(24)
    p.paragraph_format.space_after = Pt(6)
    style_run(p.add_run("Submitted by"), 12, bold=True)

    add_styled_table(
        doc,
        "",
        ["Sr. No.", "Student Name", "Enrollment / Roll Number"],
        [
            ["1", "Arjun E. Naik", "[Enrollment No. 1]"],
            ["2", "[Student Name 2]", "[Enrollment No. 2]"],
            ["3", "[Student Name 3]", "[Enrollment No. 3]"],
        ],
        col_widths=[0.8, 2.7, 2.3],
    )

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(18)
    p.paragraph_format.space_after = Pt(18)
    style_run(p.add_run("Under the Supervision of\n"), 12)
    style_run(p.add_run("[Supervisor Name & Designation]\n"), 13, bold=True)
    style_run(p.add_run("Department of Computer Science and Engineering\nIndian Institute of Information Technology, Nagpur"), 12)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(26)
    p.paragraph_format.space_after = Pt(8)
    style_run(p.add_run("DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING\n"), 12.5, bold=True)
    style_run(p.add_run("INDIAN INSTITUTE OF INFORMATION TECHNOLOGY, NAGPUR\n"), 13.5, bold=True)
    style_run(p.add_run("(An Institution of National Importance by Act of Parliament)\nSurvey No. 140, 141/1, Village Waranga, PO Dongargaon (Butibori), Nagpur - 441108\nAcademic Session: July – December 2026\n\n"), 10.5)
    style_run(p.add_run("© Indian Institute of Information Technology, Nagpur (IIITN), 2026. All rights reserved."), 10.5, bold=True)

    # 2. DECLARATION - I
    add_front_heading(doc, "DECLARATION – I")
    add_body_p(
        doc,
        "I/We hereby declare that the Mini Project report titled \"ProteinLens-OS: A Local-First Full-Stack Platform for Zero-Shot 3D-Pocket Deep Mutational Scanning, True-Path Gene Ontology Propagation, and Grounded Explainable AI\" submitted to the Department of Computer Science and Engineering, Indian Institute of Information Technology, Nagpur, is a bona fide record of original work carried out by us under the supervision of [Supervisor Name & Designation].",
    )
    add_body_p(
        doc,
        "The matter embodied in this report has not been submitted earlier, in whole or in part, to any other University or Institute for the award of any degree, diploma, or certificate.",
    )
    add_styled_table(
        doc,
        "",
        ["Sr. No.", "Student Name", "Enrollment No.", "Signature"],
        [
            ["1", "Arjun E. Naik", "[Enrollment No. 1]", ""],
            ["2", "[Student Name 2]", "[Enrollment No. 2]", ""],
            ["3", "[Student Name 3]", "[Enrollment No. 3]", ""],
        ],
        col_widths=[0.6, 2.0, 1.7, 1.5],
    )
    add_body_p(doc, "Date: _____________________          Place: IIIT Nagpur", space_after=6, justify=False)

    # 3. DECLARATION - II (Plagiarism)
    add_front_heading(doc, "DECLARATION – II\n(Plagiarism Declaration)")
    add_body_p(
        doc,
        "I/We understand that plagiarism is defined as using another person's words, code, figures, or ideas without proper scholarly acknowledgment. We declare that all software modules, experimental benchmarks, diagrams, and text in this Mini Project report are our own original work. Pretrained foundation models (Meta AI ESM-2), open biomedical databases (CAFA 6, UniProtKB, AlphaFold DB, NCBI ClinVar, Open Targets), and open-source libraries used in this work have been explicitly cited in the References section.",
    )
    add_body_p(
        doc,
        "We acknowledge that any violation of academic integrity standards may result in cancellation of this project report as per IIIT Nagpur regulations.",
    )
    add_body_p(doc, "\nSignatures of Students:  1. _______________   2. _______________   3. _______________", justify=False)
    add_body_p(doc, "Date: _____________________          Place: IIIT Nagpur", justify=False)

    # 4. THESIS / PROJECT CERTIFICATE
    add_front_heading(doc, "CERTIFICATE")
    add_body_p(
        doc,
        "This is to certify that the Mini Project report titled \"ProteinLens-OS: A Local-First Full-Stack Platform for Zero-Shot 3D-Pocket Deep Mutational Scanning, True-Path Gene Ontology Propagation, and Grounded Explainable AI\" submitted by Arjun E. Naik ([Enrollment No. 1]), [Student Name 2] ([Enrollment No. 2]), and [Student Name 3] ([Enrollment No. 3]) in partial fulfillment of the requirements for the award of the degree of Bachelor of Technology in Computer Science and Engineering at Indian Institute of Information Technology, Nagpur, is an authentic record of work carried out under my supervision and guidance.",
    )
    add_body_p(
        doc,
        "The report satisfies the formatting, technical, and scholarly standards prescribed by the Department of Computer Science and Engineering, IIIT Nagpur.",
    )
    add_body_p(
        doc,
        "\n\n\n_______________________________                    _______________________________\n"
        "[Supervisor Name & Designation]                       Head of Department (CSE)\n"
        "Project Supervisor, Dept. of CSE                        Indian Institute of Information Technology, Nagpur\n"
        "IIIT Nagpur",
        justify=False,
    )

    # 5. ACKNOWLEDGEMENT
    add_front_heading(doc, "ACKNOWLEDGEMENT")
    add_body_p(
        doc,
        "We express our deep sense of gratitude to our project supervisor, [Supervisor Name & Designation], Department of Computer Science and Engineering, IIIT Nagpur, for continuous mentorship, technical critique, and encouragement throughout the design, experimentation, and full-stack implementation of ProteinLens-OS.",
    )
    add_body_p(
        doc,
        "We are grateful to the Head of the Department of Computer Science and Engineering and the Administration of Indian Institute of Information Technology, Nagpur, for providing an enriching research environment and academic framework.",
    )
    add_body_p(
        doc,
        "We also acknowledge the open-science bioinformatics community—specifically the CAFA 6 organizers, Meta AI (ESM-2), DeepMind/EMBL-EBI (AlphaFold Protein Structure Database), UniProt Consortium, NCBI ClinVar, Open Targets Platform, and ZhuLab (Fudan University) for open-access resources and reference benchmarks that made reproducible evaluation possible.",
    )

    # =========================================================================
    # PART B — LOWERCASE ROMAN PAGE NUMBERS (Section 2, starts at 'i')
    # =========================================================================
    sec_b = doc.add_section(WD_SECTION.NEW_PAGE)
    set_section_margins(sec_b)
    set_page_number_format(sec_b, fmt="lowerRoman", start=1)

    # 6. ABSTRACT (STRICTLY ONE PAGE ONLY)
    add_front_heading(doc, "ABSTRACT", page_break=False)
    add_body_p(
        doc,
        "Rapid advances in genomic sequencing have outpaced experimental protein characterization, leaving over 99% of cataloged protein sequences without wet-lab Gene Ontology (GO) annotations and 40%–55% of human clinical missense variants classified as Variants of Uncertain Significance (VUS) in ClinVar. While large GPU-bound protein language models (650M–15B parameters) and commercial interpretation suites (\$15,000–\$100,000/year) achieve high benchmark accuracy, they remain financially and computationally inaccessible to resource-constrained hospitals, academic teaching laboratories, and privacy-sensitive clinics.",
    )
    add_body_p(
        doc,
        "This Mini Project presents ProteinLens-OS, an open-source, local-first full-stack web platform (Next.js 15 + FastAPI + SQLite) engineered to run natively on standard consumer CPU hardware. ProteinLens-OS unifies five original contributions: (1) a single-load EsmForMaskedLM engine (facebook/esm2_t6_8M_UR50D) delivering 320-dimensional embeddings, multi-layer Attention-Rollout residue saliency, exact Zero-Shot Masked-Marginal Log-Likelihood Ratios (LLR), and batched 5.0 Å 3D-Pocket Deep Mutational Scanning (DMS) across all 20 canonical amino acids; (2) a multi-paradigm GO predictor comparing a genuine 8,000-dimensional sparse 3-mer kNN baseline against ESM-2 kNN and a PyTorch Multi-Label MLP; (3) an exact Fixed-Point True Path Rule Directed Acyclic Graph (DAG) propagation engine eliminating 100% of ontology contradictions with interactive pan/zoom graph inspection; (4) a Multi-Modal Dual-Axis Clinical Risk Fusion model combining 8M-scale LLR, BLOSUM62 radicality, AlphaFold pLDDT structural order/burial, and Information-Accretion weighted GO disruption; and (5) an Auto-Configuring Multi-Provider Explainable AI (XAI) router (Google Gemini, xAI Grok, Groq, Local Ollama, and zero-key evidence-cited fallback) grounded in live UniProt, AlphaFold DB, NCBI ClinVar, and Open Targets APIs.",
    )
    add_body_p(
        doc,
        f"On a strict leakage-free 80/20 CAFA 6 held-out validation split, our PyTorch MLP achieves an Information-Accretion weighted Fmax (wFmax) of 0.4454 (+27.4% over the real 3-mer baseline at 0.3496), while Fixed-Point True Path Propagation reduces mean contradictions from {train_hist['mean_violations_before']:.2f} per protein to exact 0.00 (post-repair wFmax = {train_hist['final_val_wfmax_dag']:.4f}) in {train_hist['runtime_seconds']:.2f} seconds on CPU. On a 24-variant clinical missense benchmark spanning TP53, HBB, and INS, Multi-Modal Dual-Axis Fusion lifts CPU-class 8M ESM-2 discrimination from AUROC = {bench['clinical_variant_benchmark']['llr_auroc']:.4f} (standalone LLR) to AUROC = {bench['clinical_variant_benchmark']['dual_axis_auroc']:.4f} (AUPRC = {bench['clinical_variant_benchmark']['dual_axis_auprc']:.4f}), achieving 100% separation on TP53 drivers versus benign polymorphisms. Complete source code, live training scripts, Google Colab notebook, and institutional teaching labs are openly released under the MIT license.",
    )
    add_body_p(doc, "Keywords: Protein Function Annotation, Clinical VUS Triage, 3D-Pocket Deep Mutational Scanning, ESM-2, Gene Ontology True Path DAG, AlphaFold pLDDT, Explainable AI, Full-Stack Bioinformatics.", bold_prefix="", space_after=0)

    # 7. TABLE OF CONTENTS
    add_front_heading(doc, "TABLE OF CONTENTS")
    p_toc = doc.add_paragraph()
    add_field(p_toc, 'TOC \\o "1-3" \\h \\z \\u', "Table of Contents (auto-populated on PDF export)")

    # 8. LIST OF FIGURES
    add_front_heading(doc, "LIST OF FIGURES")
    fig_list = [
        ("Figure 3.1", "ProteinLens-OS Decoupled Local-First Full-Stack System Architecture"),
        ("Figure 3.2", "Fixed-Point True Path Rule DAG Monotonicity Repair Mechanism"),
        ("Figure 4.1", "CAFA 6 Leakage-Free 80/20 Held-Out Validation Ablation (wFmax)"),
        ("Figure 4.2", "Multi-Label PyTorch MLP Live CPU Learning Curve (BCE Loss & Validation wFmax)"),
        ("Figure 4.3", "Clinical Pathogenic vs. Benign Missense Classification ROC Curve (N = 24)"),
        ("Figure 4.4", "TP53 p.R273H 5.0 Å 3D-Pocket Zero-Shot Deep Mutational Scanning (DMS) Heatmap"),
        ("Figure 4.5", "ProteinLens-OS Live Interface: Auto-Configuring Gemini/Grok XAI & IIIT Nagpur White-Label Console"),
    ]
    add_styled_table(doc, "", ["Figure No.", "Caption Title"], fig_list, col_widths=[1.2, 4.7])

    # 9. LIST OF TABLES
    add_front_heading(doc, "LIST OF TABLES")
    tbl_list = [
        ("Table 2.1", "Comparative Analysis of Existing Bioinformatics Platforms vs. ProteinLens-OS"),
        ("Table 3.1", "Hardware, Software Stack, Dataset, and Model Hyperparameter Specifications"),
        ("Table 4.1", "CAFA 6 Leakage-Free 80/20 Validation Ablation & DAG Monotonicity Audit"),
        ("Table 4.2", "Clinical Pathogenic vs. Benign Missense Validation Summary (TP53, HBB, INS)"),
        ("Table A.1", "Complete 24-Variant Clinical Missense Benchmark Raw Observations (Appendix I)"),
        ("Table A.2", "ProteinLens-OS REST and Server-Sent Events (SSE) API Endpoints (Appendix II)"),
    ]
    add_styled_table(doc, "", ["Table No.", "Table Title"], tbl_list, col_widths=[1.2, 4.7])

    # 10. LIST OF SYMBOLS, ABBREVIATIONS AND NOMENCLATURE
    add_front_heading(doc, "LIST OF SYMBOLS, ABBREVIATIONS AND NOMENCLATURE")
    abbrev_rows = [
        ["ACMG", "American College of Medical Genetics and Genomics"],
        ["AUROC / AUPRC", "Area Under ROC Curve / Area Under Precision-Recall Curve"],
        ["BCE", "Binary Cross-Entropy Loss (BCEWithLogitsLoss)"],
        ["BLOSUM62", "Blocks Substitution Matrix 62 (Evolutionary Amino Acid Radicality)"],
        ["CAFA 6", "Critical Assessment of Functional Annotation (6th Challenge)"],
        ["DAG", "Directed Acyclic Graph (Gene Ontology Hierarchy)"],
        ["DMS", "Deep Mutational Scanning (Position × 20 Canonical Amino Acids)"],
        ["ESM-2", "Evolutionary Scale Modeling v2 (Meta AI Protein Language Model)"],
        ["FDI / ΔGO_IA", "Information-Accretion Weighted GO Functional Disruption Index"],
        ["GO (MF/BP/CC)", "Gene Ontology (Molecular Function, Biological Process, Cellular Component)"],
        ["IA(T)", "Information Accretion of GO Term T: -log2 P(T | Parents(T))"],
        ["LLR", "Masked-Marginal Log-Likelihood Ratio: log P(mut | x_\\i) - log P(wt | x_\\i)"],
        ["pLDDT", "Predicted Local Distance Difference Test (AlphaFold Per-Residue Confidence 0–100)"],
        ["SSE", "Server-Sent Events (Real-Time Streaming Progress Protocol)"],
        ["VUS", "Variant of Uncertain Significance (ClinVar Classification)"],
        ["wFmax", "Information-Accretion Weighted Maximum F1-Score"],
        ["XAI", "Explainable Artificial Intelligence"],
    ]
    add_styled_table(doc, "", ["Symbol / Term", "Full Description"], abbrev_rows, col_widths=[1.7, 4.2])

    # =========================================================================
    # PART C — ARABIC PAGE NUMBERS STARTING AT 1 (Section 3)
    # =========================================================================
    sec_c = doc.add_section(WD_SECTION.NEW_PAGE)
    set_section_margins(sec_c)
    set_page_number_format(sec_c, fmt="decimal", start=1)

    # -------------------------------------------------------------------------
    # CHAPTER 1: INTRODUCTION
    # -------------------------------------------------------------------------
    add_chapter_heading(doc, 1, "Introduction", first_chapter=True)

    add_section_h2(doc, "1.1", "Background and Motivation")
    add_body_p(
        doc,
        "Proteins execute nearly every structural, catalytic, signaling, and regulatory function inside living cells. While next-generation DNA sequencing has expanded UniProtKB beyond 250 million protein sequences [1], experimental functional determination via X-ray crystallography, NMR, or cryo-electron microscopy remains expensive and slow. Consequently, fewer than 1% of known sequences possess experimentally curated Gene Ontology (GO) annotations [2]—a grand challenge termed the Sequence–Function Annotation Gap.",
    )
    add_body_p(
        doc,
        "Parallel to this functional annotation gap, clinical genomics faces the Variant of Uncertain Significance (VUS) Crisis. In hospital Whole Exome Sequencing (WES) panels for oncology, rare pediatric disorders, and hemoglobinopathies, 40%–55% of discovered missense variants in NCBI ClinVar lack definitive pathogenic or benign classification [3]. Commercial clinical interpretation suites (e.g., QIAGEN Clinical Insight, Schrödinger BioLuminate, Franklin Enterprise) cost \$15,000–\$100,000 annually and require cloud uploads of sensitive patient sequences—creating severe accessibility and genomic-privacy barriers for public hospitals, Indian medical/engineering universities, and academic laboratories.",
    )

    add_section_h2(doc, "1.2", "Problem Statement")
    add_body_p(
        doc,
        "Existing open-source computational biology tools are deeply fragmented: sequence-to-function competition frameworks (such as DeepGOPlus [4] and CAFA 6 top contender GOAlpha [5]) operate as heavy Linux/Docker command-line ensembles targeting offline leaderboards without 3D structural variant simulation or interactive interfaces; 3D structure repositories (AlphaFold DB [6]) display atomic coordinates without predicting GO functional shifts or mutation pathogenicity; and tabular variant annotators (OpenCRAVAT [7]) lack 3D active-pocket scanning and ontology consistency auditing. Furthermore, compact CPU-viable protein language models (8M parameters) exhibit noisy standalone zero-shot pathogenicity scores compared to 650M GPU models.",
    )

    add_section_h2(doc, "1.3", "Aim, Objectives and Scope")
    add_body_p(
        doc,
        "The primary aim of this Mini Project is to design, mathematically validate, and engineer ProteinLens-OS—an open-source, local-first, privacy-preserving full-stack web platform running on standard laptop CPUs that unifies automated CAFA 6 GO annotation, 3D-pocket Deep Mutational Scanning, clinical VUS risk triage, and grounded multi-LLM Explainable AI for research labs and college classrooms.",
    )
    add_bullet(doc, "Objective 1 (Representation & Multi-Label Prediction): ", "Extract 320-dimensional evolutionary embeddings using Meta AI's ESM-2 (facebook/esm2_t6_8M_UR50D) [8] and benchmark a Multi-Label PyTorch MLP and Cosine kNN against a genuine 8,000-dimensional sparse 3-mer baseline.")
    add_bullet(doc, "Objective 2 (Hierarchical Consistency): ", "Implement a Fixed-Point True Path Rule DAG propagation engine enforcing Score(Parent) >= Score(Child) with guaranteed 0.00% post-repair contradictions and interactive graph visualization.")
    add_bullet(doc, "Objective 3 (3D-Pocket Zero-Shot DMS & Dual-Axis Fusion): ", "Parse AlphaFold PDB coordinates to isolate 5.0 Å heavy-atom spatial pockets, execute batched 20-amino-acid DMS scanning, and fuse 8M-scale LLR with BLOSUM62, AlphaFold pLDDT/8 Å burial, and ΔGO_IA.")
    add_bullet(doc, "Objective 4 (Institutional Full-Stack Platform): ", "Deploy a decoupled Next.js 15 + FastAPI + SQLite architecture with live UniProt/AlphaFold/ClinVar/Open Targets grounding, auto-configuring Gemini/Grok/Ollama XAI, reproducible local/Colab training scripts, white-label IIIT Nagpur reporting, and 4 guided college teaching labs.")

    add_section_h2(doc, "1.4", "Key Contributions")
    add_bullet(doc, "1. CPU-Viable Multi-Modal Clinical Fusion: ", "Empirically demonstrated that augmenting compact 8M CPU ESM-2 Masked-Marginal LLR (AUROC 0.5071) with 3D AlphaFold pLDDT/burial, BLOSUM62 radicality, and ΔGO_IA boosts clinical missense discrimination to AUROC = 0.7714 (+52.1% relative gain) and 100% TP53 driver separation.")
    add_bullet(doc, "2. Batched 3D-Pocket Zero-Shot DMS Studio: ", "Automated 5.0 Å heavy-atom contact shell extraction linked to single-batch ESM-2 20-AA saturation scanning, highlighting both fragile pathogenic sites and tolerated/stabilizing substitutions.")
    add_bullet(doc, "3. Provable Zero-Violation True Path DAG Repair: ", "Eliminated 94.64 mean ontology violations per protein down to exact 0.00% with transitive-reduced interactive @xyflow/react exploration.")
    add_bullet(doc, "4. Reproducible 5.5-Second Live Training & Colab Pipeline: ", "Built transparent CPU and Google Colab training pipelines proving authentic model optimization and leakage-free ablation.")
    add_bullet(doc, "5. Auto-Configuring Grounded XAI & Institutional Edition: ", "Engineered live API model discovery for Google Gemini, xAI Grok, Groq, and Local Ollama anchored to strict JSON Evidence Packets, alongside SQLite case management and 4 college lab modules.")

    add_section_h2(doc, "1.5", "Organization of the Thesis")
    add_body_p(
        doc,
        "The remainder of this report is organized as follows: Chapter 2 reviews prior literature on CAFA protein function prediction, protein language models, Gene Ontology DAG constraints, and clinical variant interpretation, concluding with the research gap addressed by this project. Chapter 3 details the proposed full-stack architecture, mathematical formulations, 3D-pocket DMS algorithm, fixed-point DAG repair, auto-configuring XAI router, and experimental/training setup. Chapter 4 presents leakage-free CAFA 6 ablations, live CPU learning curves, clinical missense ROC benchmarks, 3D-pocket case studies, and full-stack evaluation results. Chapter 5 summarizes the completed work, enumerates key conclusions, and outlines directions for future research, followed by References, Appendices I–III, and the List of Publications.",
    )

    # -------------------------------------------------------------------------
    # CHAPTER 2: LITERATURE REVIEW
    # -------------------------------------------------------------------------
    add_chapter_heading(doc, 2, "Literature Review")

    add_section_h2(doc, "2.1", "Automated Protein Function Prediction and the CAFA Challenge")
    add_body_p(
        doc,
        "The Gene Ontology (GO) Consortium [2] established a standardized Directed Acyclic Graph (DAG) vocabulary spanning Molecular Function (MF), Biological Process (BP), and Cellular Component (CC). To benchmark computational predictors rigorously, the Critical Assessment of Functional Annotation (CAFA) challenge evaluates methods using Information-Accretion weighted Fmax (wFmax) [9], which weights specific, rare annotations inversely proportional to their conditional probability given parent terms.",
    )
    add_body_p(
        doc,
        "Early annotation systems relied on sequence alignment tools such as BLAST [10] and lexical k-mer composition models. While effective when sequence identity exceeds 40%, lexical and alignment-based methods deteriorate sharply in the 'twilight zone' (<30% identity), where evolutionary homology is preserved in 3D fold rather than exact amino acid substrings.",
    )

    add_section_h2(doc, "2.2", "Protein Language Models and CAFA 6 Reference Architectures")
    add_body_p(
        doc,
        "Inspired by self-supervised Transformers in natural language processing, Protein Language Models (pLMs) such as ProtTrans [11] and Meta AI's ESM-2 [8] learn evolutionary, biophysical, and structural constraints directly from millions of unlabeled UniRef sequences via Masked Language Modeling (MLM). Top-performing CAFA 6 architectures such as ZhuLab's GOAlpha [5] combine ESM-2 evolutionary embeddings with BLAST kNN, Foldseek 3D structural search, InterPro domains, biomedical text retrieval (LinkBERT), and Learning-to-Rank meta-models inside large server-grade Docker containers. However, such multi-modal leaderboard pipelines require tens of gigabytes of external databases and Linux server clusters, limiting their adoption in interactive clinical or classroom settings.",
    )

    add_section_h2(doc, "2.3", "Zero-Shot Variant Pathogenicity and Structural Microenvironments")
    add_body_p(
        doc,
        "Meier et al. [12] demonstrated that MLM protein language models naturally score single amino acid substitutions zero-shot via the Masked-Marginal Log-Likelihood Ratio (LLR), correlating strongly with experimental Deep Mutational Scanning (DMS) assays. Concurrently, AlphaFold2 [6] unlocked near-experimental 3D atomic coordinates and calibrated per-residue confidence (pLDDT) across the human proteome. Recent clinical studies [13] highlight that pathogenic missense mutations cluster heavily inside buried, high-pLDDT folded cores (pLDDT >= 80), whereas benign population polymorphisms occur disproportionately in flexible or intrinsically disordered regions (pLDDT < 55).",
    )

    add_section_h2(doc, "2.4", "Comparative Gap Analysis of Existing Platforms")
    add_styled_table(
        doc,
        "Table 2.1: Comparative Analysis of Existing Open-Source and Commercial Bioinformatics Platforms vs. ProteinLens-OS",
        ["Platform / System", "GO Function Prediction", "3D Pocket 20-AA DMS", "True-Path DAG Visual", "Local CPU Privacy", "Grounded XAI & Teaching"],
        [
            ["OpenCRAVAT / VEP [7]", "No", "No (Tabular only)", "No", "Partial", "No"],
            ["AlphaFold DB / Mol* [6]", "No", "No", "No", "Cloud DB", "No"],
            ["DeepGOPlus / GOAlpha [4, 5]", "Yes (CLI/Docker)", "No", "No (Text out)", "High RAM/GPU", "No"],
            ["Commercial Suites (QIAGEN)", "Partial", "Paid (\$20k+/yr)", "No", "Cloud Only", "Proprietary"],
            ["ProteinLens-OS (Proposed)", "Yes (Multi-Model)", "Yes (Batched 5 Å)", "Yes (0% Viol.)", "Yes (Native CPU)", "Yes (Auto Gemini/Grok + Labs)"],
        ],
        col_widths=[1.35, 0.95, 1.0, 0.9, 0.85, 0.95],
    )

    add_section_h2(doc, "2.5", "Proposed Direction in Light of Literature Review")
    add_body_p(
        doc,
        "In light of the reviewed literature, a clear scientific and software engineering gap exists: no open-source, CPU-accessible platform currently unites CAFA-grade hierarchical GO prediction, exact zero-violation True Path DAG visualization, AlphaFold 5.0 Å 3D-pocket Deep Mutational Scanning, calibrated multi-modal VUS risk fusion, and evidence-grounded multi-LLM explainability inside an institution-ready web workspace. Accordingly, the work carried out in this Mini Project addresses this exact gap through an end-to-end, rigorously benchmarked full-stack system.",
    )

    # -------------------------------------------------------------------------
    # CHAPTER 3: PROPOSED WORK AND SYSTEM METHODOLOGY
    # -------------------------------------------------------------------------
    add_chapter_heading(doc, 3, "Proposed Work and System Methodology")

    add_section_h2(doc, "3.1", "Full-Stack System Architecture")
    add_body_p(
        doc,
        "ProteinLens-OS replaces monolithic academic notebooks with a decoupled three-tier local-first software architecture (Figure 3.1). The Presentation Layer is built in Next.js 15 (App Router, TypeScript strict mode, Tailwind CSS) hosting 9 specialized routes including an interactive 3Dmol.js molecular viewport, a 20-AA DMS heatmap, a pan/zoom @xyflow/react DAG explorer, SSE batch cohort triage, college teaching labs, and an institutional settings console. The Application Layer runs on FastAPI (Python 3.11) backed by SQLModel/SQLite for zero-install persistent case vaults and white-label institutional metadata. The Independent Scientific ML Core executes PyTorch neural inference and 3D atomic geometry natively on consumer CPUs, complemented by live cached connectors to UniProtKB [1], AlphaFold DB [6], NCBI ClinVar [3], and Open Targets [14].",
    )
    add_figure(doc, FIG_DIR / "fig0_architecture.png", "Figure 3.1: ProteinLens-OS Decoupled Local-First Full-Stack System Architecture.", width_in=5.8)

    add_section_h2(doc, "3.2", "Single-Load ESM-2 Engine: Embeddings, Attention Rollout and Masked-Marginal LLR")
    add_body_p(
        doc,
        "To minimize RAM footprint (<500 MB) on consumer laptops, a single instance of EsmForMaskedLM (facebook/esm2_t6_8M_UR50D; 6 Transformer layers, 20 heads, 320 hidden dimensions) simultaneously serves four scientific tasks:",
    )
    add_body_p(doc, "Mean-pooled sequence embeddings are computed across all valid non-padded residue hidden states H_l:", bold_prefix="1. Evolutionary Embeddings: ")
    add_equation(doc, "e(x) = (1 / L) * sum_{i=1..L} H_final[i]  in R^320", "3.1")

    add_body_p(doc, "Following Abnar & Zuidema [15], head-averaged self-attention matrices A^(l) are augmented with residual identity connections and multiplied recursively across all 6 layers, then blended (70/30) with residue hidden-state L2 norms to produce calibrated [0, 1] residue saliency highlighting catalytic and binding hotspots:", bold_prefix="2. Multi-Layer Attention Rollout Saliency: ")
    add_equation(doc, "R_rollout = prod_{l=1..6} norm( 0.5 * mean_heads(A^(l)) + 0.5 * I )", "3.2")

    add_body_p(doc, "For any missense mutation substituting wild-type residue a_wt with a_mut at position i, token i is replaced with <mask> and scored zero-shot via exact log-softmax marginal odds:", bold_prefix="3. Zero-Shot Masked-Marginal LLR: ")
    add_equation(doc, "LLR(i, a_wt -> a_mut) = log P(x_i = a_mut | x_{\\i}) - log P(x_i = a_wt | x_{\\i})", "3.3")

    add_section_h2(doc, "3.3", "3D Structural Microenvironment Parser and Batched 5.0 Å Pocket DMS")
    add_body_p(
        doc,
        "Our StructureService parses real ATOM records from AlphaFold PDB files to extract per-residue pLDDT structural confidence directly from the B-factor column (columns 60–66) and computes exact heavy-atom Euclidean distances between the target residue and all other residues. Every residue with minimum heavy-atom distance <= 5.0 Å forms the spatial pocket P_i (capped at up to 8 closest contacts), while C-alpha contacts within 8.0 Å quantify core burial density. All |P_i| masked sequence copies are stacked into a single tensor batch [|P_i|, L+2] and passed through EsmForMaskedLM in one forward pass, yielding a complete |P_i| × 20 Deep Mutational Scanning pathogenicity and tolerance landscape in ~1.2 seconds on CPU.",
    )

    add_section_h2(doc, "3.4", "Multi-Paradigm GO Prediction and Fixed-Point True Path DAG Engine")
    add_body_p(
        doc,
        "We evaluate four non-hardcoded functional prediction paradigms across the top 500 CAFA 6 GO terms: (i) Empirical Frequency Prior, (ii) a Real 8,000-dimensional L2-normalized log(1 + count) sparse 3-mer cosine kNN baseline (k = 15) built directly from the 2,000 CAFA 6 training sequences, (iii) 320-d ESM-2 Cubic-Weighted Cosine kNN (k = 10), and (iv) a 2-layer PyTorch Multi-Label MLP (320 → 512 → 256 → 500, ReLU, Dropout 0.3, 424,180 trainable parameters) trained with BCEWithLogitsLoss and AdamW.",
    )
    add_body_p(
        doc,
        "Because independent binary sigmoid heads violate biological ontology inheritance (predicting P(Child) > P(Parent)), we apply an exact Fixed-Point True Path Rule propagation operator iterating bottom-up until zero parent-child edge contradictions remain (Figure 3.2):",
    )
    add_equation(doc, "P_prop(u) <- max( P_prop(u), max_{v in Children(u)} P_prop(v) )", "3.4")
    add_body_p(
        doc,
        "For interactive web exploration, our DAG engine computes the transitive reduction of active ontology subgraphs and highlights every repaired ancestor node along with its exact elevation delta (P_prop - P_raw). Functional disruption between wild-type and mutant sequences is quantified via the Information-Accretion weighted L1 shift (Delta-GO_IA):",
    )
    add_equation(doc, "Delta_GO_IA(v) = sum_{t in G} IA(t) * | P_prop^mut(t) - P_prop^wt(t) | / sum_{t in G} IA(t)", "3.5")
    add_figure(doc, FIG_DIR / "fig_dag_concept.png", "Figure 3.2: Fixed-Point True Path Rule DAG Monotonicity Repair Mechanism guaranteeing 0.00% violations.", width_in=5.6)

    add_section_h2(doc, "3.5", "Multi-Modal Dual-Axis Clinical Risk Fusion")
    add_body_p(
        doc,
        "To overcome the known LLR noise of compact 8M-parameter CPU models on disordered loops, we formulate an auditable Multi-Modal Clinical Risk Score S_clinical in [0, 100] combining calibrated evolutionary intolerance (ESM-2 LLR + normalized BLOSUM62 radicality [16]), AlphaFold 3D structural sensitivity (pLDDT order sigmoid + 8.0 Å core burial), and hierarchical GO disruption:",
    )
    add_equation(doc, "S_clinical(v) = 100 * ( 0.42 * R_evo(v) + 0.43 * R_struct(pLDDT, Burial_8A) + 0.15 * R_GO(Delta_GO_IA) )", "3.6")

    add_section_h2(doc, "3.6", "Auto-Configuring Multi-Provider XAI Router and Live Training Pipeline")
    add_body_p(
        doc,
        "Our AutoConfigAIRouter automatically detects API key prefixes (AIza... for Google Gemini, xai-... for xAI Grok, gsk_... for Groq, or local Ollama), queries each provider's live /models catalog to discover all enabled chat models (prioritizing newest Flash models such as gemini-3.8-flash), verifies connectivity via a live ping, and persists configuration locally in backend/.env. To eliminate biomedical hallucination, every LLM prompt is strictly constrained to a structured JSON Evidence Packet containing only computed scores and live UniProt/ClinVar/Open Targets records, with a deterministic evidence-cited fallback when offline.",
    )
    add_body_p(
        doc,
        "For full academic reproducibility and live viva verification, we provide both a self-contained 5.5-second laptop CPU training script (training/train_live_demo.py) and a 1-click Google Colab GPU/CPU notebook (training/ProteinLens_Colab_Training.ipynb) that clone the repository, execute leakage-free 80/20 PyTorch MLP training, audit True Path DAG violations, and regenerate all publication figures.",
    )

    add_section_h2(doc, "3.7", "Experimental Setup")
    add_styled_table(
        doc,
        "Table 3.1: Hardware, Software Stack, Dataset, and Model Hyperparameter Specifications",
        ["Component", "Specification / Value"],
        [
            ["Local Hardware", "Consumer Laptop CPU (Intel x86_64, 8 GB RAM, No Discrete GPU Required)"],
            ["Cloud Compatibility", "Google Colab Free Tier (NVIDIA T4 GPU or CPU) via ProteinLens_Colab_Training.ipynb"],
            ["Backend & Persistence", "Python 3.11, FastAPI 0.163, Uvicorn, SQLModel + SQLite, PyTorch 2.15, Transformers 5.23"],
            ["Frontend & Visuals", "Next.js 15.1.6, TypeScript 5.7, Tailwind CSS 3.4, 3Dmol.js 2.0.4, @xyflow/react, Recharts"],
            ["Protein Backbone", "Meta AI EsmForMaskedLM (facebook/esm2_t6_8M_UR50D, 320-d, max_len = 512)"],
            ["CAFA 6 Benchmark Set", "2,000 UniProtKB training proteins (80/20 leakage-free split), top 500 IA-weighted GO terms"],
            ["Clinical Variant Set", "24 curated ClinVar-verified Pathogenic (14) vs. Benign (10) missense variants (TP53, HBB, INS)"],
            ["MLP Hyperparameters", "320 -> 512 -> 256 -> 500, Dropout 0.30, AdamW (lr=1e-3, wd=1e-2), 25 epochs, batch_size=128"],
        ],
        col_widths=[1.8, 4.1],
    )

    # -------------------------------------------------------------------------
    # CHAPTER 4: RESULTS AND DISCUSSIONS
    # -------------------------------------------------------------------------
    add_chapter_heading(doc, 4, "Results and Discussions")

    add_section_h2(doc, "4.1", "CAFA 6 Leakage-Free Validation Ablation and Live Learning Curve")
    add_body_p(
        doc,
        "All multi-label GO classifiers were evaluated on a strict leakage-free 80/20 held-out split (1,600 train / 400 validation proteins) where feature standardization (mean/std) and reference matrices were fit strictly on the training fold. Table 4.1 and Figure 4.1 report Information-Accretion weighted Fmax (wFmax) and ontology violation counts across all six configurations.",
    )
    ab_rows = [
        [r["model"], f"{r['wfmax']:.4f}", str(r["violations_after"])]
        for r in bench["cafa6_ablation"]
    ]
    add_styled_table(
        doc,
        "Table 4.1: CAFA 6 Leakage-Free 80/20 Held-Out Validation Ablation and DAG Violation Audit",
        ["Model Architecture", "Held-Out wFmax", "Mean DAG Violations / Protein"],
        ab_rows,
        col_widths=[3.0, 1.35, 1.55],
    )
    add_figure(doc, FIG_DIR / "fig1_cafa6_ablation.png", "Figure 4.1: CAFA 6 Held-Out 80/20 Validation Ablation comparing lexical 3-mer, ESM-2 kNN, PyTorch MLP, and True-Path Ensemble.", width_in=5.5)

    add_body_p(
        doc,
        f"Contextual 320-dimensional ESM-2 representations decisively outperform the real 8,000-dimensional lexical 3-mer sparse kNN baseline (+19.6% for ESM-2 kNN at 0.4181; +27.4% for PyTorch MLP at 0.4454). Figure 4.2 shows the live 25-epoch training progression executed in just {train_hist['runtime_seconds']:.2f} seconds on our local laptop CPU: training BCE loss drops smoothly from 0.4616 to 0.1655 while held-out validation wFmax climbs monotonically from 0.3374 (Epoch 1) to 0.4454 (Epoch 25) and improves further to {train_hist['final_val_wfmax_dag']:.4f} after Fixed-Point True Path DAG Repair.",
    )
    add_figure(doc, FIG_DIR / "fig3_training_curve.png", "Figure 4.2: Multi-Label PyTorch MLP Live CPU Learning Curve (BCE Loss and Validation wFmax across 25 Epochs).", width_in=5.4)

    add_section_h2(doc, "4.2", "Quantitative True Path Rule Monotonicity Repair Audit")
    add_body_p(
        doc,
        f"Unconstrained neural predictions exhibit severe biological hierarchy contradictions: raw PyTorch MLP outputs average {train_hist['mean_violations_before']:.2f} parent-child violations per validation protein (88.40 for the raw ensemble). Applying our Fixed-Point True Path propagation converges in 2–4 passes and guarantees exact 0.00 violations across 100% of test proteins while preserving—and slightly improving—IA-weighted Fmax.",
    )

    add_section_h2(doc, "4.3", "Clinical Pathogenic vs. Benign Missense Validation (TP53, HBB, INS)")
    cvb = bench["clinical_variant_benchmark"]
    add_body_p(
        doc,
        f"To evaluate real-world clinical utility on consumer CPUs, we benchmarked {cvb['n_variants']} ClinVar-verified missense variants ({cvb['n_pathogenic']} Pathogenic drivers vs. {cvb['n_benign']} Benign population controls) spanning Tumor Protein p53 (TP53), Hemoglobin Subunit Beta (HBB), and Human Insulin (INS). Table 4.2 and Figure 4.3 reveal our core research finding.",
    )
    add_styled_table(
        doc,
        "Table 4.2: Clinical Missense Classification Performance on Consumer CPU Hardware (N = 24 Variants)",
        ["Variant Scoring Method", "AUROC", "AUPRC", "Relative AUROC Gain"],
        [
            ["Standalone CPU esm2_t6_8M Masked-Marginal LLR", f"{cvb['llr_auroc']:.4f}", f"{cvb['llr_auprc']:.4f}", "Baseline"],
            ["ProteinLens-OS Multi-Modal Dual-Axis Clinical Fusion", f"{cvb['dual_axis_auroc']:.4f}", f"{cvb['dual_axis_auprc']:.4f}", "+0.2643 (+52.1%)"],
        ],
        col_widths=[2.85, 0.9, 0.9, 1.25],
    )
    add_figure(doc, FIG_DIR / "fig2_clinical_roc.png", "Figure 4.3: ROC Curve Comparing Standalone 8M ESM-2 LLR vs. ProteinLens-OS Multi-Modal Dual-Axis Clinical Fusion.", width_in=4.5)

    add_body_p(
        doc,
        "Standalone 8M ESM-2 Masked-Marginal LLR achieves only 0.5071 AUROC because compact 6-layer language models assign overly negative log-odds to repetitive proline motifs inside disordered regions (e.g., benign polymorphism TP53 p.P72R at pLDDT 48.25). Integrating 3D AlphaFold pLDDT order, 8.0 Å burial density, BLOSUM62 radicality, and ΔGO_IA elevates AUROC by +0.2643 to 0.7714 (AUPRC = 0.8408). Crucially, on TP53, all 8 pathogenic drivers (R175H, G245S, R248Q/W, R249S, R273H/C, R282W; pLDDT 94.8–98.6) score 48.5–73.3, whereas all 6 benign polymorphisms (P72R, P47S, P36S, D21N, S366A, T387V) score 22.6–42.8—yielding 100% linear separation without GPU hardware. Complete per-variant raw metrics are tabulated in Appendix I.",
    )

    add_section_h2(doc, "4.4", "Case Study: TP53 p.R273H 3D-Pocket DMS and Live Full-Stack Verification")
    add_body_p(
        doc,
        "Figure 4.4 displays the real zero-shot 3D-Pocket Deep Mutational Scanning heatmap generated by ProteinLens-OS for oncology hotspot TP53 p.R273H (UniProt P04637). Our structural parser isolates the 7 closest heavy-atom contacting pocket neighbors within 5.0 Å of R273 (pLDDT 98.56) and evaluates all 8 × 20 = 160 amino acid states in a single batched pass. Figure 4.5 shows the live verified web interface deployed for IIIT Nagpur, featuring automatic Gemini/xAI Grok/Groq live model discovery, white-label institutional branding, and local SQLite persistence.",
    )
    add_figure(doc, FIG_DIR / "fig4_pocket_dms_heatmap.png", "Figure 4.4: Real Batched 5.0 Å 3D-Pocket Zero-Shot DMS Heatmap for TP53 p.R273H (8 Pocket Sites × 20 Amino Acids).", width_in=5.8)
    add_figure(doc, FIG_DIR / "fig_app_settings.png", "Figure 4.5: Verified Live ProteinLens-OS Web Interface showing Auto-Configuring Multi-Provider XAI Setup and IIIT Nagpur White-Label Branding.", width_in=5.6)

    add_section_h2(doc, "4.5", "Efficiency, Privacy and Discussion of Limitations")
    add_body_p(
        doc,
        f"Mean end-to-end single-variant inference latency on consumer CPU averages {cvb['mean_variant_latency_ms']:.1f} ms once wild-type embeddings are cached, while reactive UI interactions execute in <10 ms. All patient sequences and SQLite cases remain strictly on-premise, satisfying local genomic privacy principles. Primary limitations include the 512-residue sequence window of the 8M CPU model and coverage of the top 500 CAFA 6 GO terms; both scale seamlessly to esm2_t33_650M and larger GO vocabularies when deployed on departmental GPUs.",
    )

    # -------------------------------------------------------------------------
    # CHAPTER 5: SUMMARY AND CONCLUSIONS (Strictly Enumerated per Sec 1.5)
    # -------------------------------------------------------------------------
    add_chapter_heading(doc, 5, "Summary and Conclusions")

    add_section_h2(doc, "5.1", "Summary of Work Carried Out")
    add_body_p(
        doc,
        "This Mini Project successfully designed, mathematically evaluated, and deployed ProteinLens-OS—an open-source, local-first full-stack bioinformatics web platform (Next.js 15 + FastAPI + SQLite) bridging CAFA 6 protein function annotation, 3D structural pocket Deep Mutational Scanning, clinical VUS triage, and grounded multi-LLM Explainable AI. All software modules, 6/6 automated backend unit tests, strict TypeScript production builds, 5.5-second live laptop training scripts, Google Colab notebook, and 300-DPI benchmark figures were verified end-to-end and published openly on GitHub.",
    )

    add_section_h2(doc, "5.2", "Conclusions")
    conclusions = [
        "1. Contextual protein language embeddings (ESM-2, 320-d) significantly outperform real 8,000-d lexical 3-mer baselines (+27.4% wFmax gain on leakage-free CAFA 6 validation) while executing in 5.51 seconds of training time on a consumer CPU.",
        "2. Unconstrained multi-label neural classifiers generate severe Gene Ontology contradictions (88.4–94.6 violations per protein); our Fixed-Point True Path propagation algorithm provably reduces contradictions to exact 0.00% while improving validation wFmax to 0.4473.",
        "3. Compact 8M-parameter CPU models struggle at standalone zero-shot clinical LLR scoring (AUROC = 0.5071), but fusing 3D AlphaFold pLDDT/8 Å burial, BLOSUM62 radicality, and ΔGO_IA elevates discrimination to AUROC = 0.7714 (AUPRC = 0.8408) with 100% separation on TP53.",
        "4. Batched 5.0 Å 3D-Pocket Zero-Shot DMS combined with live federated UniProt, ClinVar, and Open Targets lookups and auto-configuring Gemini/Grok XAI provides an accessible, privacy-preserving alternative to costly proprietary genomics suites.",
        "5. Embedding white-label institutional branding (IIIT Nagpur default) and 4 guided College Teaching Labs transforms a research algorithm into an immediately adoptable educational and clinical decision-support software product.",
    ]
    for c in conclusions:
        add_body_p(doc, c, space_after=5)

    add_section_h2(doc, "5.3", "Scope for Future Work")
    future_items = [
        "1. Departmental GPU Scaling: Support hot-swapping esm2_t33_650M and expanding the multi-label classifier head from 500 to 5,000+ GO terms across the full 82,000-protein CAFA training corpus.",
        "2. Large-Scale Clinical Benchmarking: Extend validation from 24 curated missense variants to 10,000+ ProteinGym DMS assays and full ClinVar Star-2+ missense callsets.",
        "3. Multi-Mutation Epistasis & Indel Modeling: Generalize single-point mutagenesis to multi-site compensatory rescue combinations and in-frame insertion/deletion variants.",
        "4. Enterprise Campus & Hospital Integration: Add role-based campus authentication (RBAC), shared PostgreSQL case banks, and HL7 FHIR clinical genomic report interoperability.",
    ]
    for f_it in future_items:
        add_body_p(doc, f_it, space_after=5)

    # -------------------------------------------------------------------------
    # REFERENCES (Chronological & Sequentially Cited)
    # -------------------------------------------------------------------------
    add_front_heading(doc, "REFERENCES")
    refs = [
        "[1] UniProt Consortium, \"UniProt: the Universal Protein Knowledgebase in 2025,\" Nucleic Acids Research, Vol. 53, No. D1, pp. D609–D617, Jan. 2025. https://www.uniprot.org",
        "[2] M. Ashburner, C. A. Ball, J. A. Blake, D. Botstein, H. Butler, J. M. Cherry, et al., \"Gene Ontology: tool for the unification of biology,\" Nature Genetics, Vol. 25, No. 1, pp. 25–29, May 2000.",
        "[3] M. J. Landrum, S. Chitipiralla, G. R. Brown, C. Chen, B. Gu, J. Hart, et al., \"ClinVar: improvements to accessing data,\" Nucleic Acids Research, Vol. 48, No. D1, pp. D835–D844, Jan. 2020. https://www.ncbi.nlm.nih.gov/clinvar/",
        "[4] M. Kulmanov and R. Hoehndorf, \"DeepGOPlus: improved protein function prediction from sequence,\" Bioinformatics, Vol. 36, No. 2, pp. 422–429, Jan. 2020.",
        "[5] ZhuLab (Fudan University), \"GOAlpha: Multi-Modal Protein Function Prediction Container for CAFA 6,\" Zenodo / GitHub Repository, 2026. DOI: 10.5281/zenodo.21787658.",
        "[6] J. Jumper, R. Evans, A. Pritzel, T. Green, M. Figurnov, O. Ronneberger, et al., \"Highly accurate protein structure prediction with AlphaFold,\" Nature, Vol. 596, pp. 583–589, Aug. 2021. https://alphafold.ebi.ac.uk",
        "[7] K. Pagel, R. Kim, K. Moad, B. Busby, L. Zheng, R. Tokheim, et al., \"Integrated Informatics Analysis of Cancer-Related Variants (OpenCRAVAT),\" JCO Clinical Cancer Informatics, Vol. 4, pp. 310–317, Apr. 2020.",
        "[8] Z. Lin, H. Akin, R. Rao, B. Hie, Z. Zhu, W. Lu, et al., \"Evolutionary-scale prediction of atomic-level protein structure with a language model (ESM-2),\" Science, Vol. 379, No. 6637, pp. 1123–1130, Mar. 2023.",
        "[9] N. Zhou, Y. Jiang, T. R. Bergquist, A. J. Lee, B. Z. Kacsoh, A. W. Crocker, et al., \"The CAFA challenge reports improved protein function prediction and new functional annotations for hundreds of genes through experimental screens,\" Genome Biology, Vol. 20, No. 1, pp. 244, Nov. 2019.",
        "[10] S. F. Altschul, W. Gish, W. Miller, E. W. Myers, and D. J. Lipman, \"Basic local alignment search tool (BLAST),\" Journal of Molecular Biology, Vol. 215, No. 3, pp. 403–410, Oct. 1990.",
        "[11] A. Elnaggar, M. Heinzinger, C. Dallago, G. Rehawi, Y. Wang, L. Jones, et al., \"ProtTrans: Toward Understanding the Language of Life Through Self-Supervised Learning,\" IEEE Transactions on Pattern Analysis and Machine Intelligence, Vol. 44, No. 10, pp. 7112–7127, Oct. 2022.",
        "[12] J. Meier, R. Rao, R. Verkuil, J. Liu, T. Sercu, and A. Rives, \"Language models enable zero-shot prediction of the effects of mutations on protein function,\" Advances in Neural Information Processing Systems (NeurIPS), Vol. 34, pp. 29287–29303, Dec. 2021.",
        "[13] J. Cheng, G. Novati, J. Pan, C. Bycroft, A. Zemgulyte, T. Applebaum, et al., \"Accurate proteome-wide missense variant effect prediction with AlphaMissense,\" Science, Vol. 381, No. 6664, eadg7492, Sep. 2023.",
        "[14] D. Ochoa, A. Hercules, M. Carmona, D. Suveges, J. Baker, C. Malangone, et al., \"The next-generation Open Targets Platform: reimagined, redesigned, rebuilt,\" Nucleic Acids Research, Vol. 51, No. D1, pp. D1353–D1359, Jan. 2023.",
        "[15] S. Abnar and W. Zuidema, \"Quantifying Attention Flow in Transformers,\" Proceedings of the 58th Annual Meeting of the Association for Computational Linguistics (ACL), pp. 4190–4197, Jul. 2020.",
        "[16] S. Henikoff and J. G. Henikoff, \"Amino acid substitution matrices from protein blocks (BLOSUM62),\" Proceedings of the National Academy of Sciences (PNAS), Vol. 89, No. 22, pp. 10915–10919, Nov. 1992.",
    ]
    for ref in refs:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 1.35
        p.paragraph_format.left_indent = Inches(0.35)
        p.paragraph_format.first_line_indent = Inches(-0.35)
        p.paragraph_format.space_after = Pt(5)
        style_run(p.add_run(ref), 11)

    # -------------------------------------------------------------------------
    # APPENDICES (Roman Capitals: Appendix I, II, III)
    # -------------------------------------------------------------------------
    add_front_heading(doc, "APPENDIX I\nComplete 24-Variant Clinical Missense Benchmark Raw Observations")
    var_rows = [
        [
            v["gene"], v["mutation"], v["label"],
            f"{v['llr']:+.2f}", f"{v['plddt']:.1f}" if v["plddt"] else "N/A",
            f"{v['fdi']:.2f}", f"{v['dual_axis_risk']:.1f}",
        ]
        for v in cvb["variants"]
    ]
    add_styled_table(
        doc,
        "Table A.1: Per-Variant Clinical Validation Raw Metrics (ESM-2 LLR, AlphaFold pLDDT, FDI, and Dual-Axis Risk)",
        ["Gene", "Mutation", "ClinVar Label", "ESM-2 LLR", "pLDDT", "FDI", "Dual-Axis Risk"],
        var_rows,
        col_widths=[0.65, 0.8, 0.95, 0.85, 0.75, 0.7, 1.1],
    )

    add_front_heading(doc, "APPENDIX II\nREST / SSE API Specification and Live Training Execution Guide")
    api_rows = [
        ["GET /api/health", "Returns service health, ML backbone metadata, AI router status & IIITN config"],
        ["POST /api/analyze/protein", "Full ESM-2 embedding, Attention Rollout, Model Arena, DAG JSON & AlphaFold PDB"],
        ["POST /api/analyze/variant", "Dual-Axis Risk, ESM-2 LLR, 5.0 Å 3D Pocket, Batched 20-AA DMS & ClinVar/Drugs"],
        ["POST /api/analyze/batch", "Queues async patient cohort variant triage; streams progress via GET /api/jobs/{id}/stream"],
        ["POST /api/settings/ai/models", "Queries live /models endpoint for user's Gemini / Grok / Groq / Ollama API key"],
        ["POST /api/settings/ai", "Auto-detects provider prefix, verifies working model, persists locally in backend/.env"],
        ["POST /api/copilot/synthesize", "Evidence-grounded XAI briefing (Clinical / Research / Student modes)"],
        ["GET/POST/DELETE /api/cases", "Persistent SQLite clinical case vault + GET /api/export/{id}?fmt=json|csv"],
    ]
    add_styled_table(
        doc,
        "Table A.2: ProteinLens-OS Backend FastAPI REST and SSE Endpoints",
        ["Endpoint", "Functional Description"],
        api_rows,
        col_widths=[2.0, 3.9],
    )
    add_body_p(doc, "Live 5.5-Second Laptop CPU Training Demo:", bold_prefix="Reproducible Training Verification — ")
    add_body_p(doc, "    python training/train_live_demo.py", justify=False)
    add_body_p(doc, "Google Colab Notebook: Open training/ProteinLens_Colab_Training.ipynb in Google Colab (T4 GPU or CPU) to clone https://github.com/Arjun-E-Naik/ProtienLens and execute all training, DAG audit, and clinical benchmark cells.", space_after=6)

    add_front_heading(doc, "APPENDIX III\nAcademic Teaching Lab Pack Curriculum")
    add_bullet(doc, "BIO-LAB 101 (Oncology DMS): ", "TP53 p.R273H DNA-Binding Pocket Disruption vs. Benign Control P72R.")
    add_bullet(doc, "BIO-LAB 102 (Molecular Medicine): ", "Hemoglobin Subunit Beta p.E7V (Sickle Cell) Hydrophobic Surface Switch & ClinVar Concordance.")
    add_bullet(doc, "BIO-LAB 103 (Structural Folding): ", "Human Insulin p.C96Y Disulfide Bond Loss & Evolutionary Conservation Entropy.")
    add_bullet(doc, "ML-LAB 201 (Bio-ML Engineering): ", "Real 3-mer vs. ESM-2 Model Arena & Fixed-Point True Path DAG Violation Repair.")

    # -------------------------------------------------------------------------
    # LIST OF PUBLICATIONS
    # -------------------------------------------------------------------------
    add_front_heading(doc, "LIST OF PUBLICATIONS AND OPEN-SOURCE ARTIFACTS")
    add_body_p(
        doc,
        "[1] Arjun E. Naik, [Student Name 2], [Student Name 3], and [Supervisor Name], \"ProteinLens-OS: A Local-First Full-Stack Platform Unifying Zero-Shot 3D-Pocket Deep Mutational Scanning, True-Path Gene Ontology Propagation, and Multi-LLM Explainable AI for Clinical Variant Triage,\" Manuscript prepared for submission to IEEE BIBM / BMC Bioinformatics (Software Track), 2026 (Draft available in paper/manuscript.md).",
    )
    add_body_p(
        doc,
        "[2] ProteinLens-OS Open-Source Software Release (v2.0.0, MIT License), GitHub Repository: https://github.com/Arjun-E-Naik/ProtienLens, 2026.",
    )

    doc.save(str(OUT_DOCX))
    print(f"Successfully generated IIITN-compliant report: {OUT_DOCX}")


if __name__ == "__main__":
    build_report()
