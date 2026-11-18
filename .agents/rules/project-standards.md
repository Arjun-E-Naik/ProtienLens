# ProteinLens-OS Engineering & Design Standards

1. **Full-Stack Architecture**:
   - Backend: FastAPI (Python 3.11 using workspace `.venv`), SQLModel + SQLite (`proteinlens.db`), port `8000`.
   - Frontend: Next.js 15 (App Router, TypeScript strict mode, Tailwind CSS), port `3000`.
   - Zero Docker required; must run natively on Windows/Linux/macOS consumer CPUs.

2. **Zero Hardcoded Predictions**:
   - All GO function predictions, ESM2 Masked-Marginal LLR scores, 3D-Pocket 20-AA DMS matrices, Attention-Rollout residue saliency, 3-mer baseline predictions, True Path DAG graphs, and UniProt/AlphaFold/ClinVar/OpenTargets evidence MUST be computed or fetched dynamically by the backend.
   - Never fabricate or hardcode ML metrics.

3. **Auto-Configuring Multi-Provider XAI**:
   - Automatically detect `GEMINI_API_KEY`, `GOOGLE_API_KEY`, `XAI_API_KEY`, `GROK_API_KEY`, `GROQ_API_KEY`, or local Ollama.
   - Support live API key entry, auto-prefix detection, live verification, and persistence directly inside `/settings`.
   - Always maintain a deterministic evidence-cited scientific fallback when offline or unconfigured.

4. **Institutional & Clinical UI Standards**:
   - Default Institution Name: `IIIT Nagpur — Computational Biology & AI Lab` (white-label editable in `/settings`).
   - Aesthetic: Precision Clinical Bio-Lab (crisp high-contrast WCAG AA light mode default with optional dark mode toggle; `Inter` UI typography + `JetBrains Mono` with `tabular-nums` for sequences, GO IDs, LLR, and pLDDT values).
   - No student mini-project watermarks.

5. **Verification Gates**:
   - Backend changes must pass `pytest`.
   - Frontend changes must pass `npm run build` and live browser inspection with zero console or network errors.
