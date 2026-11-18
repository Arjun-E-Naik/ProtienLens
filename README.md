# ProteinLens-OS: Open-Source Clinical Variant Intelligence, 3D-Pocket DMS & True-Path GO Platform

> **Default Institutional Deployment**: IIIT Nagpur — Computational Biology & AI Lab (White-Label Editable in `/settings`)

**ProteinLens-OS** is an open-source, local-first, privacy-preserving full-stack bioinformatics web platform (Next.js 15 + FastAPI + SQLite) uniting:

1. **Zero-Shot 3D-Pocket Deep Mutational Scanning (DMS)**: Extracts the real 5.0 Å heavy-atom spatial pocket from AlphaFold 3D coordinates and computes the complete `Pocket Positions × 20 Canonical Amino Acids` pathogenicity & tolerance landscape in a single batched `EsmForMaskedLM` pass.
2. **Multi-Modal Dual-Axis Clinical Variant Pathogenicity**: Combines zero-shot ESM2 Masked-Marginal Log-Likelihood Ratio (LLR), BLOSUM62 physicochemical radicality, AlphaFold pLDDT structural order/burial, and Information-Accretion weighted Gene Ontology disruption ($\Delta\text{GO}_{\text{IA}}$).
3. **Exact Fixed-Point True Path DAG Explorer**: Interactive pan/zoom `@xyflow/react` Gene Ontology hierarchy guaranteeing `0.00%` post-repair monotonicity contradictions.
4. **Auto-Configuring Multi-Provider Explainable AI (XAI)**: Automatically detects the provider prefix and live-discovers available models for **Google Gemini (`AIza...`)**, **xAI Grok (`xai-...`)**, **Groq (`gsk_...`)**, or **Local Ollama** right inside `/settings`, with a zero-key deterministic evidence-cited fallback when offline.
5. **College & Research Lab Readiness**: Built-in **4 Guided Academic Teaching Labs**, **Batch Cohort Triage (SSE streaming)**, **SQLite Case Vault**, **SHA-256 JSON/CSV audit dossiers**, and **White-Label Printable PDF Reports**.

---

## Verified Research Benchmarks

Reproducible via `benchmarks/run_paper_benchmarks.py` (manuscript in `paper/manuscript.md`):

- **CAFA 6 Leakage-Free 80/20 Validation**:
  - Frequency Prior: `wFmax = 0.3429`
  - Real 8,000-d Sparse 3-mer kNN: `wFmax = 0.3496`
  - ESM2 Cosine kNN: `wFmax = 0.4181` (+19.6%)
  - ESM2 PyTorch MLP: **`wFmax = 0.4454`** (+27.4%)
  - Ensemble + Fixed-Point True Path DAG: **`wFmax = 0.4413`** with **`0` monotonicity violations** (down from `88.4` mean violations/protein)
- **Clinical Pathogenic vs. Benign Missense Benchmark ($N=24$ variants across `TP53`, `HBB`, `INS`)**:
  - Standalone CPU `esm2_t6_8M` Masked-Marginal LLR: `AUROC = 0.5071`, `AUPRC = 0.5940`
  - **ProteinLens-OS Multi-Modal Dual-Axis Fusion**: **`AUROC = 0.7714`**, **`AUPRC = 0.8408`** (**+0.2643 AUROC gain** on consumer CPU)

---

## Installation & Quick Start (Zero Docker)

### 1. Clone & Install Backend (Python 3.11+)
```bash
git clone https://github.com/Arjun-E-Naik/ProtienLens.git
cd ProtienLens

python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux / macOS:
# source .venv/bin/activate

pip install -r backend/requirements.txt
```

### 2. Install Frontend (Node.js 18+)
```bash
cd frontend
npm install
npm run build
cd ..
```

### 3. Run Both Servers
**Windows 1-Click**: Double-click `start_proteinlens.bat` or run `.\start_proteinlens.ps1`

**Manual (Any OS)**:
```bash
# Terminal 1 (Backend on :8000)
cd backend
uvicorn app.main:app --host 127.0.0.1 --port 8000

# Terminal 2 (Frontend on :3000)
cd frontend
npm run start
```
- **Web Application**: `http://localhost:3000`
- **FastAPI Swagger Docs**: `http://localhost:8000/docs`

### 4. Configure Gemini or xAI Grok API Key (Inside the App)
1. Open `http://localhost:3000/settings`.
2. Paste your **Google Gemini (`AIza...`)**, **xAI Grok (`xai-...`)**, or **Groq (`gsk_...`)** API key.
3. Click **Fetch Models** (or click **Auto-Detect, Verify & Save AI Provider**) to live-discover the models enabled on your key and activate grounded Explainable AI synthesis.

---

## Testing & Reproducible Paper Benchmarks
```bash
# Backend & Scientific ML test suite
cd backend && pytest tests/test_api.py -v

# Reproducible research benchmarks & 300-DPI plots
python benchmarks/run_paper_benchmarks.py
```

---

## License & Clinical Notice
Released under the **MIT License**. Designed for **Research, Academic Teaching, and Clinical Decision Support Only** — not a standalone regulatory-cleared clinical diagnostic.
