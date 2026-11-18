# ProteinLens-OS: A Local-First Full-Stack Platform Unifying Zero-Shot 3D-Pocket Deep Mutational Scanning, True-Path Gene Ontology Propagation, and Multi-LLM Explainable AI for Clinical Variant Triage

**Authors**: [Student Name 1], [Student Name 2], [Student Name 3], and [Supervisor Name]  
**Affiliation**: Department of Computer Science and Engineering, Indian Institute of Information Technology, Nagpur (IIITN), Nagpur, Maharashtra, India  
**Open-Source Repository**: `ProteinLens-OS` (MIT License)

---

## Abstract

Interpreting Variants of Uncertain Significance (VUS) and uncharacterized protein sequences remains a major bottleneck in clinical genomics and translational bioinformatics. While large GPU-bound protein language models (650M–15B parameters) and proprietary commercial interpretation suites (\$15,000–\$100,000/year) achieve strong predictive performance, they remain inaccessible to under-resourced hospitals, academic teaching laboratories, and privacy-regulated local clinics. We present **ProteinLens-OS**, an open-source, local-first full-stack web platform (Next.js 15 + FastAPI + SQLite) running entirely on consumer CPU hardware that unifies four capabilities previously fragmented across separate tools: (1) batched **3D-Pocket Zero-Shot Deep Mutational Scanning (DMS)** coupling `EsmForMaskedLM` (`facebook/esm2_t6_8M_UR50D`) Masked-Marginal Log-Likelihood Ratios (LLR) with 5.0 Å AlphaFold heavy-atom spatial contact extraction; (2) **Multi-Modal Dual-Axis Clinical Risk Fusion** integrating 8M-scale evolutionary LLR, BLOSUM62 physicochemical radicality, AlphaFold pLDDT structural order/burial, and Information-Accretion weighted Gene Ontology disruption ($\Delta\text{GO}_{\text{IA}}$); (3) **Fixed-Point True Path Rule DAG Propagation** guaranteeing `0.00%` post-repair ontology contradictions with interactive pan/zoom visualization; and (4) an **Auto-Configuring Multi-Provider Explainable AI (XAI) Router** (Google Gemini, xAI Grok, Groq, Local Ollama, and zero-key evidence-cited fallback) strictly grounded in computed metrics and live federated UniProt, NCBI ClinVar, and Open Targets APIs. On a leakage-free 80/20 CAFA 6 held-out validation split, our ESM2 PyTorch MLP achieves `wFmax = 0.4454` (+27.4% over a real 8,000-dimensional sparse 3-mer kNN baseline at `0.3496`), while Fixed-Point True Path Propagation eliminates `88.4` mean ontology violations per protein down to exact `0.0`. Crucially, on a curated 24-variant clinical missense benchmark across `TP53`, `HBB`, and `INS`, fusing 3D structural microenvironment and hierarchical GO disruption lifts CPU-class 8M ESM2 discrimination from `AUROC = 0.5071` (standalone LLR) to **`AUROC = 0.7714` (`AUPRC = 0.8408`)**—a **+0.2643 AUROC gain** without requiring GPU infrastructure.

**Index Terms** — Clinical Variant Triage, Deep Mutational Scanning (DMS), Protein Language Models, Gene Ontology DAG, True Path Rule, AlphaFold pLDDT, Explainable AI (XAI), Open-Source Bioinformatics.

---

## I. Introduction

High-throughput genomic sequencing has produced over 250 million cataloged protein sequences and millions of clinical missense variants; however, fewer than 1% of proteins possess experimentally verified Gene Ontology (GO) annotations, and 40%–55% of human clinical variants in ClinVar remain **Variants of Uncertain Significance (VUS)**. Existing open-source bioinformatics tools force clinicians, researchers, and students into fragmented workflows: tabular variant annotators (OpenCRAVAT, Ensembl VEP) lack interactive 3D structural pocket inspection and hierarchical pathway explanations; 3D coordinate repositories (AlphaFold DB) provide atomic structures without variant pathogenicity or GO functional prediction; and academic CAFA pipelines (DeepGOPlus, GOAlpha) operate as command-line scripts requiring high-memory servers or Docker clusters.

To close both the **technical fragmentation gap** and the **institutional accessibility gap**, we engineered **ProteinLens-OS**, a decoupled, privacy-preserving full-stack software platform deployable natively on consumer laptops and college computer labs.

### Core Contributions
1. **3D-Pocket Zero-Shot Deep Mutational Scanning (DMS)**: Automatic extraction of the 5.0 Å heavy-atom structural contact shell around any target residue from AlphaFold coordinates, paired with a single batched `EsmForMaskedLM` pass scoring all 20 canonical amino acids per pocket site.
2. **CPU-Viable Multi-Modal Clinical Risk Fusion**: Empirical demonstration that fusing 3D AlphaFold structural order (pLDDT + 8.0 Å core burial), BLOSUM62 radicality, and $\Delta\text{GO}_{\text{IA}}$ overcomes the zero-shot LLR noise of compact 8M CPU models (+0.2643 AUROC improvement).
3. **Exact Fixed-Point True Path Rule DAG Engine**: Provable `0.00%` monotonicity contradiction with interactive transitive-reduced `@xyflow/react` visualization and repair audit trails.
4. **Auto-Configuring Grounded XAI & Institutional Deployment**: In-app automatic provider detection (Gemini, xAI Grok, Groq, Local Ollama, deterministic fallback), white-label institutional PDF/SHA-256 JSON dossiers, and a 4-module Academic Teaching Lab pack.

---

## II. Comparative Platform Positioning

| Platform | 3D Pocket DMS (20-AA) | True-Path GO DAG | Local CPU Privacy | Grounded Multi-LLM XAI | Institutional Lab Pack |
| :--- | :---: | :---: | :---: | :---: | :---: |
| OpenCRAVAT / VEP | No | No | Partial | No | No |
| AlphaFold DB / Mol* | No | No | Cloud | No | No |
| DeepGOPlus / GOAlpha | No | CLI Only | High RAM/GPU | No | No |
| Commercial Suites (QIAGEN / Schrödinger) | Paid (\$20k+) | No | Cloud | Proprietary | Paid |
| **ProteinLens-OS (Ours)** | **Yes (Batched)** | **Interactive (0% Viol.)** | **Yes (Native CPU)** | **Auto-Config (Gemini/Grok)** | **Yes (MIT Open-Source)** |

---

## III. Methodology & Mathematical Formulation

### A. Single-Load ESM2 Representation, Attention Rollout & Masked-Marginal LLR
Using `EsmForMaskedLM` (`facebook/esm2_t6_8M_UR50D`, 6 transformer layers, 320 hidden dimensions), a single model instance serves four tasks:
1. **Sequence Embeddings**: Mean pooling of final-layer hidden states across non-padded residue tokens ($\mathbf{e} \in \mathbb{R}^{320}$).
2. **Multi-Layer Attention Rollout**: Layer-wise head-averaged self-attention matrices with residual identity augmentation ($\tilde{\mathbf{A}}^{(l)} = 0.5\mathbf{A}^{(l)} + 0.5\mathbf{I}$) multiplied recursively to obtain residue-level saliency blended (70/30) with token activation norms.
3. **Zero-Shot Masked-Marginal LLR**: For residue position $i$ with wild-type amino acid $a_{\text{wt}}$ and candidate substitution $a_{\text{mut}}$, position $i$ is replaced by `<mask>` and scored as:
   $$\text{LLR}(i, a_{\text{wt}} \to a_{\text{mut}}) = \log P\!\left(x_i = a_{\text{mut}} \mid x_{\setminus i}\right) - \log P\!\left(x_i = a_{\text{wt}} \mid x_{\setminus i}\right)$$
4. **Batched 3D-Pocket DMS**: Given the 5.0 Å heavy-atom spatial pocket $\mathcal{P}_i$ ($|\mathcal{P}_i| \le 8$) extracted from AlphaFold atomic coordinates, all $|\mathcal{P}_i|$ masked copies are evaluated in one batched forward pass, producing a $|\mathcal{P}_i| \times 20$ pathogenicity and tolerance heatmap.

### B. Multi-Model GO Classification & Fixed-Point True Path Propagation
We benchmark four distinct paradigms over the top 500 CAFA 6 GO terms across Molecular Function (MF), Biological Process (BP), and Cellular Component (CC): Frequency Prior, Real 8,000-d Sparse 3-mer Cosine kNN, 320-d ESM2 Cubic-Weighted Cosine kNN ($k=10$), and a 2-layer PyTorch MLP (`320 → 512 → 256 → 500`, `BCEWithLogitsLoss`, AdamW). Raw ensemble probabilities $\mathbf{P}_{\text{raw}} = 0.5\mathbf{P}_{\text{MLP}} + 0.5\mathbf{P}_{\text{kNN}}$ are passed through a fixed-point bottom-up True Path Rule operator until convergence:
$$P_{\text{prop}}(u) \leftarrow \max\!\left(P_{\text{prop}}(u),\; \max_{v \in \text{Children}(u)} P_{\text{prop}}(v)\right)$$
guaranteeing zero monotonicity violations across multi-hop ancestor chains.

### C. Multi-Modal Clinical Risk Fusion
For a missense variant $v = (i, a_{\text{wt}} \to a_{\text{mut}})$, we fuse evolutionary constraint (calibrated 8M-scale LLR + normalized BLOSUM62 radicality), AlphaFold 3D structural sensitivity (pLDDT order sigmoid + 8.0 Å $C_\alpha$ core burial), and IA-weighted GO disruption ($\Delta\text{GO}_{\text{IA}}$):
$$S_{\text{clinical}}(v) = 100 \cdot \left(0.42\,R_{\text{evo}}(v) + 0.43\,R_{\text{struct}}(\text{pLDDT}_i, \text{Contacts}_{8\text{Å}}) + 0.15\,R_{\text{GO}}(\Delta\text{GO}_{\text{IA}}, \Delta_{\text{cos}})\right)$$

---

## IV. Experimental Results

All experiments were executed reproducibly via `benchmarks/run_paper_benchmarks.py` on consumer CPU hardware without GPUs.

### A. Table I — CAFA 6 Held-Out 80/20 Validation Ablation (Leakage-Free)

| Model Architecture | Feature Space | Held-Out $wF_{\max}$ | Mean DAG Violations / Protein |
| :--- | :--- | :---: | :---: |
| Frequency Prior Baseline | Marginal Class Prior | `0.3429` | `0.0` |
| Real 3-mer Sparse kNN | 8,000-d Lexical $k$-mer | `0.3496` | `0.0` |
| ESM2 Cosine kNN | 320-d Transformer | `0.4181` (+19.6%) | `0.0` |
| ESM2 PyTorch MLP | 320-d Transformer | **`0.4454`** (+27.4%) | `94.0` |
| Ensemble Blend (Raw) | 0.5 MLP + 0.5 kNN | `0.4421` | `88.4` |
| **Ensemble + True-Path DAG Engine** | **0.5 MLP + 0.5 kNN + DAG** | **`0.4413`** | **`0.0` (100% Repaired)** |

*(See Publication Figure: `benchmarks/output/fig1_cafa6_ablation.png`)*

### B. Table II — Clinical Pathogenic vs. Benign Missense Validation ($N = 24$ Variants across `TP53`, `HBB`, `INS`)

| Scoring Method | AUROC | AUPRC | Relative AUROC Gain |
| :--- | :---: | :---: | :---: |
| Standalone CPU `esm2_t6_8M` Masked-Marginal LLR | `0.5071` | `0.5940` | Baseline |
| **ProteinLens-OS Multi-Modal Dual-Axis Clinical Fusion** | **`0.7714`** | **`0.8408`** | **`+0.2643` (+52.1%)** |

**Key Clinical Finding**: On `TP53`, all 8 curated pathogenic somatic/germline drivers (`R175H`, `G245S`, `R248Q`, `R248W`, `R249S`, `R273H`, `R273C`, `R282W`) lie in high-confidence folded core domains (`pLDDT 94.8–98.6`) and score `48.5–73.3`, whereas all 6 benign population polymorphisms (`P72R`, `P47S`, `P36S`, `D21N`, `S366A`, `T387V`) lie primarily in disordered regions (`pLDDT 37.6–72.1`) and score `22.6–42.8`—achieving **100% separation on `TP53`** using only an 8M-parameter CPU model.

*(See Publication Figure: `benchmarks/output/fig2_clinical_roc.png`)*

---

## V. Full-Stack System Architecture & Institutional Impact

ProteinLens-OS separates concerns across a **Next.js 15 TypeScript/Tailwind frontend** (`:3000`) and a **FastAPI + SQLModel/SQLite backend** (`:8000`) with Server-Sent Events (SSE) for real-time batch cohort triage. Federated queries to UniProt REST, AlphaFold DB, NCBI ClinVar E-utilities, and Open Targets GraphQL are cached locally with graceful offline degradation. The built-in **Auto-Configuring XAI Router** accepts Google Gemini, xAI Grok, Groq, or air-gapped Local Ollama credentials inside `/settings`, binding every LLM response to a strict JSON Evidence Packet to mitigate biomedical hallucination.

---

## VI. Ethics, Limitations & Conclusion

**Limitations**: The local CPU configuration uses `esm2_t6_8M_UR50D` (512-residue window) and the top 500 CAFA 6 GO terms; scaling to `esm2_t33_650M` on departmental GPUs is a single configuration flag. **Clinical Disclaimer**: ProteinLens-OS is intended strictly for *research, academic education, and computational decision support*—not standalone regulatory-approved clinical diagnosis. By uniting zero-shot 3D-pocket DMS, exact DAG repair, grounded multi-LLM XAI, and white-label institutional workflows in an MIT-licensed local-first stack, ProteinLens-OS democratizes enterprise-grade structural variant intelligence for colleges, researchers, and resource-constrained clinics worldwide.
