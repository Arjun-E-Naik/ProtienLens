"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowRight,
  BookOpen,
  Box,
  CheckCircle2,
  Cpu,
  Dna,
  GitBranch,
  Loader2,
  Play,
  Settings,
  Shield,
  Sparkles,
} from "lucide-react";
import { useWorkspace } from "@/context/WorkspaceContext";
import { api } from "@/lib/api";
import type { SavedCaseSummary } from "@/lib/types";

export default function HomePage() {
  const router = useRouter();
  const {
    institution,
    aiStatus,
    backendOnline,
    presets,
    clinicalVariants,
    runQuickProtein,
    isLoadingProtein,
  } = useWorkspace();

  const [uniprotInput, setUniprotInput] = useState("P04637");
  const [customFasta, setCustomFasta] = useState("");
  const [inputMode, setInputMode] = useState<"uniprot" | "fasta">("uniprot");
  const [error, setError] = useState<string | null>(null);
  const [recentCases, setRecentCases] = useState<SavedCaseSummary[]>([]);

  useEffect(() => {
    api.listCases().then((rows) => setRecentCases(rows.slice(0, 4))).catch(() => {});
  }, []);

  const handleLaunchProtein = async (override?: { uniprot_id?: string; sequence?: string; protein_name?: string }) => {
    setError(null);
    try {
      const payload = override
        ? override
        : inputMode === "uniprot"
        ? { uniprot_id: uniprotInput.trim() }
        : { sequence: customFasta.trim(), protein_name: "Custom FASTA Sequence" };

      await runQuickProtein(payload);
      router.push("/studio");
    } catch (e: any) {
      setError(e?.message || "Analysis failed. Check backend connection.");
    }
  };

  return (
    <div className="space-y-6">
      {/* Institutional Hero Header */}
      <section className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-gradient-to-br from-white via-blue-50/40 to-cyan-50/40 dark:from-slate-900 dark:via-slate-900 dark:to-blue-950/30 p-6 md:p-8 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="max-w-3xl space-y-2.5">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-blue-100/80 text-blue-800 dark:bg-blue-950 dark:text-cyan-300 border border-blue-200 dark:border-blue-800">
              <Shield className="w-3.5 h-3.5" />
              <span>Open-Source Local-First Clinical Genomics &amp; Research Platform</span>
            </div>
            <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white">
              ProteinLens-OS: 3D-Pocket Deep Mutational Scanning &amp; True-Path GO Studio
            </h1>
            <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
              Deployed for <strong>{institution.institution_name}</strong>. Unifies zero-shot{" "}
              <span className="font-mono text-xs px-1.5 py-0.5 rounded bg-slate-200/70 dark:bg-slate-800">
                ESM2 Masked-Marginal LLR
              </span>
              , batched <strong>5 Å 3D-Pocket 20-AA DMS</strong>, exact{" "}
              <strong>True-Path Gene Ontology DAG propagation</strong>, live ClinVar / UniProt / Open Targets evidence, and auto-configuring{" "}
              <strong>Gemini / xAI Grok Explainable AI</strong>.
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            <Link
              href="/variants"
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold shadow-sm"
            >
              <Dna className="w-4 h-4" />
              Launch 3D Pocket DMS
            </Link>
            <Link
              href="/settings"
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-100 border border-slate-200 dark:border-slate-700 text-sm font-semibold"
            >
              <Settings className="w-4 h-4" />
              {aiStatus?.is_llm_connected ? "Manage AI Key" : "Add Gemini / Grok Key"}
            </Link>
          </div>
        </div>

        {/* Status Strip */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-6">
          <div className="p-3 rounded-xl bg-white/90 dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800">
            <div className="text-[11px] font-medium text-slate-500">Inference Engine</div>
            <div className="mt-1 flex items-center gap-1.5 text-sm font-bold text-slate-900 dark:text-white">
              <CheckCircle2 className={`w-4 h-4 ${backendOnline ? "text-emerald-500" : "text-rose-500"}`} />
              <span>{backendOnline ? "ESM2-MLM + Real 3-mer" : "Connecting..."}</span>
            </div>
          </div>
          <div className="p-3 rounded-xl bg-white/90 dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800">
            <div className="text-[11px] font-medium text-slate-500">Explainable AI Router</div>
            <div className="mt-1 flex items-center gap-1.5 text-sm font-bold text-slate-900 dark:text-white">
              <Sparkles className="w-4 h-4 text-blue-600 dark:text-cyan-400" />
              <span className="truncate">
                {aiStatus?.is_llm_connected ? `${aiStatus.active_provider.toUpperCase()} Live` : "Local Cited Engine"}
              </span>
            </div>
          </div>
          <div className="p-3 rounded-xl bg-white/90 dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800">
            <div className="text-[11px] font-medium text-slate-500">GO Ontology Coverage</div>
            <div className="mt-1 font-mono text-sm font-bold text-slate-900 dark:text-white tabular-nums">
              500 Terms · 0% Violations
            </div>
          </div>
          <div className="p-3 rounded-xl bg-white/90 dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800">
            <div className="text-[11px] font-medium text-slate-500">Deployment Privacy</div>
            <div className="mt-1 flex items-center gap-1.5 text-sm font-bold text-emerald-700 dark:text-emerald-400">
              <Cpu className="w-4 h-4" />
              <span>Local CPU · SQLite DB</span>
            </div>
          </div>
        </div>
      </section>

      {/* Quick Protein Analyzer + Clinical Variant Launchers */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Instant Protein Launch */}
        <div className="lg:col-span-7 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 space-y-4">
          <div className="flex items-center justify-between gap-2">
            <div>
              <h2 className="text-base font-bold text-slate-900 dark:text-white">
                Instant Protein Function &amp; 3D Structure Analysis
              </h2>
              <p className="text-xs text-slate-500">
                Enter any UniProt ID (live UniProt + AlphaFold resolution) or paste a custom FASTA sequence.
              </p>
            </div>
            <div className="flex rounded-lg bg-slate-100 dark:bg-slate-800 p-0.5 text-xs">
              <button
                onClick={() => setInputMode("uniprot")}
                className={`px-3 py-1 rounded-md font-medium ${
                  inputMode === "uniprot"
                    ? "bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-sm"
                    : "text-slate-600 dark:text-slate-400"
                }`}
              >
                UniProt ID
              </button>
              <button
                onClick={() => setInputMode("fasta")}
                className={`px-3 py-1 rounded-md font-medium ${
                  inputMode === "fasta"
                    ? "bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-sm"
                    : "text-slate-600 dark:text-slate-400"
                }`}
              >
                Custom FASTA
              </button>
            </div>
          </div>

          {inputMode === "uniprot" ? (
            <div className="flex gap-2">
              <input
                type="text"
                value={uniprotInput}
                onChange={(e) => setUniprotInput(e.target.value)}
                placeholder="e.g., P04637 (TP53), P68871 (HBB), P01308 (Insulin)"
                className="flex-1 px-3.5 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 text-slate-900 dark:text-white font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                onClick={() => handleLaunchProtein()}
                disabled={isLoadingProtein || !uniprotInput.trim()}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-semibold"
              >
                {isLoadingProtein ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                Analyze
              </button>
            </div>
          ) : (
            <div className="space-y-2.5">
              <textarea
                rows={4}
                value={customFasta}
                onChange={(e) => setCustomFasta(e.target.value)}
                placeholder=">novel_protein&#10;MVHLTPEEKSAVTALWGKVNVDEVGGEALGRLLVVYPWTQRFFESFGDLSTPDAVMGNPKVKAHGKKVLGAFSDGLAHLDNLKGTFATLSELHCDKLHVDPENFRLLGNVLVCVLAHHFGKEFTPPVQAAYQKVVAGVANALAHKYH"
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 text-slate-900 dark:text-white font-mono text-xs focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                onClick={() => handleLaunchProtein()}
                disabled={isLoadingProtein || !customFasta.trim()}
                className="inline-flex items-center gap-2 px-5 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-semibold"
              >
                {isLoadingProtein ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                Run De Novo ESM2 Inference
              </button>
            </div>
          )}

          {error && (
            <div className="p-3 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-xs text-rose-700 dark:text-rose-300">
              {error}
            </div>
          )}

          {/* Curated One-Click Benchmarks */}
          <div className="pt-2">
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
              Curated Benchmark Proteins (Instant Local 3D PDB Cache)
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {presets.map((p) => (
                <button
                  key={p.uniprot_id}
                  onClick={() =>
                    handleLaunchProtein({
                      uniprot_id: p.uniprot_id,
                      sequence: p.sequence,
                      protein_name: p.name,
                    })
                  }
                  disabled={isLoadingProtein}
                  className="text-left p-3 rounded-xl border border-slate-200 dark:border-slate-800 hover:border-blue-400 dark:hover:border-cyan-500 bg-slate-50/70 dark:bg-slate-800/50 transition-colors"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-mono text-xs font-bold text-blue-700 dark:text-cyan-400">
                      {p.uniprot_id}
                    </span>
                    <span className="text-[11px] font-mono text-slate-500">
                      {p.sequence.length} aa
                    </span>
                  </div>
                  <div className="text-xs font-bold text-slate-900 dark:text-white mt-1 truncate">
                    {p.name}
                  </div>
                  <div className="text-[11px] text-slate-500 dark:text-slate-400 truncate mt-0.5">
                    {p.organism}
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Right: Clinical Variant Triage Shortcuts */}
        <div className="lg:col-span-5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-slate-900 dark:text-white">
                Clinical VUS &amp; 3D-Pocket DMS Cases
              </h2>
              <p className="text-xs text-slate-500">
                Real disease drivers vs. benign controls ready for 20-AA pocket scanning.
              </p>
            </div>
            <Link
              href="/variants"
              className="text-xs font-semibold text-blue-600 dark:text-cyan-400 hover:underline inline-flex items-center gap-1"
            >
              Open Lab <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="space-y-2.5">
            {clinicalVariants.slice(0, 5).map((v) => (
              <Link
                key={v.id}
                href={`/variants?preset=${v.id}`}
                className="block p-3 rounded-xl border border-slate-200 dark:border-slate-800 hover:border-blue-400 dark:hover:border-cyan-500 bg-slate-50/70 dark:bg-slate-800/40 transition-colors"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-mono text-xs font-bold text-slate-900 dark:text-white">
                    {v.gene_symbol} p.{v.wt_aa}
                    {v.position}
                    {v.mut_aa}
                  </span>
                  <span
                    className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                      v.expected_category.includes("Benign")
                        ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                        : "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300"
                    }`}
                  >
                    {v.expected_category}
                  </span>
                </div>
                <p className="text-[11px] text-slate-600 dark:text-slate-400 mt-1 line-clamp-2">
                  {v.clinical_context}
                </p>
              </Link>
            ))}
          </div>
        </div>
      </div>

      {/* Platform Feature Cards & Recent Cases */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Link
          href="/dag"
          className="p-5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-blue-400 transition-colors"
        >
          <GitBranch className="w-6 h-6 text-amber-600 mb-2" />
          <h3 className="text-sm font-bold text-slate-900 dark:text-white">
            Interactive True Path DAG Explorer
          </h3>
          <p className="text-xs text-slate-500 mt-1">
            Pan, zoom, and audit fixed-point ancestor repairs guaranteeing 0.0% ontology contradictions.
          </p>
        </Link>
        <Link
          href="/labs"
          className="p-5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-blue-400 transition-colors"
        >
          <BookOpen className="w-6 h-6 text-emerald-600 mb-2" />
          <h3 className="text-sm font-bold text-slate-900 dark:text-white">
            College Teaching Lab Modules
          </h3>
          <p className="text-xs text-slate-500 mt-1">
            4 ready-to-assign B.Tech / M.Sc / MBBS computational biology labs with printable white-label PDF reports.
          </p>
        </Link>
        <Link
          href="/arena"
          className="p-5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-blue-400 transition-colors"
        >
          <Box className="w-6 h-6 text-blue-600 mb-2" />
          <h3 className="text-sm font-bold text-slate-900 dark:text-white">
            Model Arena &amp; Research Benchmarks
          </h3>
          <p className="text-xs text-slate-500 mt-1">
            Compare Real 3-mer kNN, ESM2 kNN, PyTorch MLP, and Ensemble + publishable ClinVar AUROC experiments.
          </p>
        </Link>
      </div>

      {recentCases.length > 0 && (
        <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">
              Recent Saved Cases (SQLite Institutional Workspace)
            </h3>
            <Link href="/cases" className="text-xs font-semibold text-blue-600 hover:underline">
              View All Cases
            </Link>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
            {recentCases.map((c) => (
              <Link
                key={c.id}
                href={`/cases?open=${c.id}`}
                className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 hover:border-blue-400"
              >
                <div className="font-mono text-[11px] text-blue-600 dark:text-cyan-400 font-semibold">
                  {c.case_code}
                </div>
                <div className="text-xs font-bold text-slate-900 dark:text-white mt-0.5 truncate">
                  {c.title}
                </div>
                <div className="text-[11px] text-slate-500 mt-1 font-mono">
                  {c.mutation ? `Mut: ${c.mutation}` : "Wild-Type"} ·{" "}
                  {c.composite_risk_score != null ? `Risk ${c.composite_risk_score}` : c.uniprot_id || "Custom"}
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
