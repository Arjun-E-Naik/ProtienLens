"""
ProteinLens-OS Curated Clinical Variant Presets & Institutional Teaching Lab Pack
Enables colleges (B.Tech / M.Sc / MBBS / Biotech) and research labs to use ProteinLens-OS
immediately on day one with scientifically grounded real-world cases.
"""

from __future__ import annotations

from typing import Any, Dict, List


CLINICAL_VARIANT_PRESETS: List[Dict[str, Any]] = [
    {
        "id": "tp53-r273h",
        "title": "TP53 p.R273H — DNA-Binding Contact Hotspot",
        "gene_symbol": "TP53",
        "uniprot_id": "P04637",
        "protein_name": "Tumor Protein p53",
        "position": 273,
        "wt_aa": "R",
        "mut_aa": "H",
        "clinical_context": "Li-Fraumeni Syndrome & Pan-Cancer Somatic Driver; abolishes direct electrostatic DNA phosphate contact.",
        "expected_category": "Pathogenic (Known Driver)",
    },
    {
        "id": "tp53-r175h",
        "title": "TP53 p.R175H — Structural Zinc-Pocket Conformational Mutant",
        "gene_symbol": "TP53",
        "uniprot_id": "P04637",
        "protein_name": "Tumor Protein p53",
        "position": 175,
        "wt_aa": "R",
        "mut_aa": "H",
        "clinical_context": "Destabilizes the L2/L3 zinc-binding structural core, causing global misfolding of the p53 DBD.",
        "expected_category": "Pathogenic (Structural)",
    },
    {
        "id": "hbb-e7v",
        "title": "HBB p.E7V (E6V) — Sickle Cell Anemia Hydrophobic Switch",
        "gene_symbol": "HBB",
        "uniprot_id": "P68871",
        "protein_name": "Hemoglobin Subunit Beta",
        "position": 7,
        "wt_aa": "E",
        "mut_aa": "V",
        "clinical_context": "Replaces negatively charged Glutamate with hydrophobic Valine (UniProt pos 7, mature pos 6), driving deoxy-HbS polymerization.",
        "expected_category": "Pathogenic (Mendelian)",
    },
    {
        "id": "ins-c96y",
        "title": "INS p.C96Y — Akita Neonatal Diabetes Disulfide Loss",
        "gene_symbol": "INS",
        "uniprot_id": "P01308",
        "protein_name": "Human Insulin",
        "position": 96,
        "wt_aa": "C",
        "mut_aa": "Y",
        "clinical_context": "Breaks the critical A7-B7 interchain disulfide bond in proinsulin, causing ER stress and beta-cell apoptosis.",
        "expected_category": "Pathogenic (Disulfide Core)",
    },
    {
        "id": "tp53-p72r",
        "title": "TP53 p.P72R — Common Benign Population Polymorphism",
        "gene_symbol": "TP53",
        "uniprot_id": "P04637",
        "protein_name": "Tumor Protein p53",
        "position": 72,
        "wt_aa": "P",
        "mut_aa": "R",
        "clinical_context": "High-frequency benign polymorphism in the disordered proline-rich N-terminal region (low pLDDT).",
        "expected_category": "Benign Control",
    },
    {
        "id": "gfp-y66h",
        "title": "GFP p.Y66H — Blue Fluorescent Protein (BFP) Chromophore Shift",
        "gene_symbol": "GFP",
        "uniprot_id": "P42212",
        "protein_name": "Green Fluorescent Protein (GFP)",
        "position": 66,
        "wt_aa": "Y",
        "mut_aa": "H",
        "clinical_context": "Classic protein engineering chromophore mutation inside the 11-stranded beta-barrel shifting emission from green to blue.",
        "expected_category": "Protein Engineering Case",
    },
]


ACADEMIC_TEACHING_LABS: List[Dict[str, Any]] = [
    {
        "lab_id": "lab-1-oncology-dms",
        "code": "BIO-LAB 101",
        "title": "Oncology Hotspot & 3D Pocket Deep Mutational Scanning (TP53 R273H)",
        "difficulty": "Intermediate",
        "duration_min": 25,
        "target_courses": ["B.Tech Bioinformatics", "M.Sc Computational Biology", "MBBS Molecular Medicine"],
        "uniprot_id": "P04637",
        "gene_symbol": "TP53",
        "position": 273,
        "mut_aa": "H",
        "objectives": [
            "Inspect AlphaFold pLDDT confidence around residue 273 vs. the disordered N-terminus (residue 72).",
            "Interpret the ESM2 Masked-Marginal LLR score and 20-amino-acid 3D Pocket DMS heatmap.",
            "Compare TP53 R273H (Pathogenic) against P72R (Benign Control) using Dual-Axis Risk Fusion.",
        ],
        "viva_questions": [
            "Why does ESM2 Masked-Marginal LLR detect pathogenicity at R273 without needing a Multiple Sequence Alignment (MSA)?",
            "How does the 5.0 A spatial contact shell distinguish buried active-site residues from flexible surface loops?",
        ],
    },
    {
        "lab_id": "lab-2-sickle-cell",
        "code": "BIO-LAB 102",
        "title": "Mendelian Molecular Medicine: Hemoglobin Beta E7V (Sickle Cell)",
        "difficulty": "Foundational",
        "duration_min": 20,
        "target_courses": ["Biotechnology", "Genetics", "Medical Biochemistry"],
        "uniprot_id": "P68871",
        "gene_symbol": "HBB",
        "position": 7,
        "mut_aa": "V",
        "objectives": [
            "Visualize Hemoglobin Subunit Beta in 3D and highlight the N-terminal residue E7 (mature position 6).",
            "Verify ClinVar live clinical concordance and Open Targets therapeutic landscape.",
            "Identify tolerated vs. disruptive substitutions at position 7 using the DMS landscape.",
        ],
        "viva_questions": [
            "Why is a polar-to-hydrophobic substitution (Glu -> Val) on a protein surface capable of causing polymerization?",
            "How does our XAI Co-Pilot stay grounded against hallucination when summarizing clinical variants?",
        ],
    },
    {
        "lab_id": "lab-3-disulfide-diabetes",
        "code": "BIO-LAB 103",
        "title": "Structural Folding & Disulfide Disruption in Human Insulin (C96Y)",
        "difficulty": "Intermediate",
        "duration_min": 20,
        "target_courses": ["Structural Biology", "Pharmaceutical Sciences"],
        "uniprot_id": "P01308",
        "gene_symbol": "INS",
        "position": 96,
        "mut_aa": "Y",
        "objectives": [
            "Analyze why Cysteine residues forming disulfide bridges display extreme evolutionary conservation.",
            "Measure the Information-Accretion weighted Functional Disruption Index (Delta-GO_IA).",
            "Generate a white-label Institutional Lab Report PDF for submission.",
        ],
        "viva_questions": [
            "Why do almost all 19 substitutions at Cysteine-96 score strongly negative in the DMS heatmap?",
            "What is Information Accretion (IA), and why is IA-weighted Fmax superior to unweighted F1?",
        ],
    },
    {
        "lab_id": "lab-4-dag-arena",
        "code": "ML-LAB 201",
        "title": "Extreme Multi-Label Bio-ML: True Path Rule DAG Repair & Model Arena",
        "difficulty": "Advanced",
        "duration_min": 30,
        "target_courses": ["B.Tech CSE (AI/ML)", "Data Science", "Bioinformatics"],
        "uniprot_id": "P00533",
        "gene_symbol": "EGFR",
        "position": 100,
        "mut_aa": "A",
        "objectives": [
            "Compare lexical 3-mer sparse kNN against ESM2 kNN, PyTorch MLP, and Ensemble predictions in Model Arena.",
            "Trace amber-highlighted True-Path repaired ancestor nodes in the interactive React Flow GO DAG.",
            "Audit pre-repair vs. post-repair monotonicity violations confirming exact 0.0% post-repair contradiction.",
        ],
        "viva_questions": [
            "How does fixed-point bottom-up True Path propagation resolve multi-hop ontology contradictions?",
            "Why does a 320-d transformer embedding outperform an 8,000-d 3-mer vector on remote homologs?",
        ],
    },
]
