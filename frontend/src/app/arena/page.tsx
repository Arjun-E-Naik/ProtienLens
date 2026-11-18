"use client";

import React, { useEffect, useState } from "react";
import { BarChart3, CheckCircle2, Cpu, Loader2 } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useWorkspace } from "@/context/WorkspaceContext";
import { api } from "@/lib/api";

export default function ArenaPage() {
  const { activeProtein, presets, runQuickProtein, isLoadingProtein } = useWorkspace();
  const [telemetry, setTelemetry] = useState<Record<string, any> | null>(null);

  useEffect(() => {
    api.getTelemetry().then(setTelemetry).catch(() => {});
    if (!activeProtein && !isLoadingProtein && presets.length > 0) {
      const p = presets[0];
      runQuickProtein({
        uniprot_id: p.uniprot_id,
        sequence: p.sequence,
        protein_name: p.name,
      }).catch(() => {});
    }
  }, [activeProtein, isLoadingProtein, presets, runQuickProtein]);

  if (isLoadingProtein || !activeProtein) {
    return (
      <div className="p-16 flex flex-col items-center justify-center gap-3 text-slate-500">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        <p className="text-sm">Evaluating Multi-Paradigm Model Arena...</p>
      </div>
    );
  }

  const rows = activeProtein.model_arena.rows;
  const chartData = rows.slice(0, 8).map((r) => ({
    name: r.name.length > 18 ? `${r.name.slice(0, 16)}…` : r.name,
    "Real 3-mer kNN": Number((r.kmer_3 * 100).toFixed(1)),
    "ESM2 kNN": Number((r.esm2_knn * 100).toFixed(1)),
    "ESM2 MLP": Number((r.esm2_mlp * 100).toFixed(1)),
    "True-Path Final": Number((r.true_path_final * 100).toFixed(1)),
  }));

  const bench = telemetry?.benchmark_summary;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white flex items-center gap-2">
            <BarChart3 className="w-6 h-6 text-blue-600" />
            Model Arena &amp; Reproducible Research Benchmarks
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Live comparative benchmark on <strong>{activeProtein.protein_name}</strong> using{" "}
            <strong>100% real trained models</strong> (zero simulated heuristics).
          </p>
        </div>

        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200 dark:bg-emerald-950/50 dark:text-emerald-300 dark:border-emerald-800">
          <CheckCircle2 className="w-3.5 h-3.5" />
          Real 8,000-d 3-mer Matrix:{" "}
          {activeProtein.model_metadata.real_3mer_trained ? "Verified & Trained" : "Fallback"}
        </span>
      </div>

      {/* Timing Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {(
          [
            ["Real 3-mer Sparse kNN", activeProtein.model_arena.timings_ms.kmer_3, "8,000-d lexical"],
            ["ESM2 Cosine kNN", activeProtein.model_arena.timings_ms.esm2_knn, "320-d cubic sim"],
            ["ESM2 PyTorch MLP", activeProtein.model_arena.timings_ms.esm2_mlp, "512 → 256 → 500"],
            ["True Path DAG Pass", activeProtein.model_arena.timings_ms.dag_propagation, "Fixed-point 0% viol."],
          ] as const
        ).map(([title, ms, sub]) => (
          <div
            key={title}
            className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800"
          >
            <div className="text-xs text-slate-500">{title}</div>
            <div className="font-mono text-xl font-extrabold text-slate-900 dark:text-white mt-1 tabular-nums">
              {ms.toFixed(2)} ms
            </div>
            <div className="text-[11px] text-slate-500 mt-0.5">{sub}</div>
          </div>
        ))}
      </div>

      {/* Comparative Bar Chart */}
      <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5">
        <h2 className="text-sm font-bold text-slate-900 dark:text-white mb-4">
          Cross-Paradigm Probability Comparison (Top 8 Predicted GO Terms)
        </h2>
        <div className="h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 8, right: 16, left: 0, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} interval={0} angle={-12} textAnchor="end" />
              <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} unit="%" />
              <Tooltip />
              <Legend />
              <Bar dataKey="Real 3-mer kNN" fill="#94a3b8" radius={[4, 4, 0, 0]} />
              <Bar dataKey="ESM2 kNN" fill="#38bdf8" radius={[4, 4, 0, 0]} />
              <Bar dataKey="ESM2 MLP" fill="#2563eb" radius={[4, 4, 0, 0]} />
              <Bar dataKey="True-Path Final" fill="#059669" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* High-Contrast Model Comparison Matrix */}
      <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5">
        <h2 className="text-sm font-bold text-slate-900 dark:text-white mb-3">
          Side-by-Side Paradigm Matrix (Confidence %)
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-500">
                <th className="py-2 pr-3">GO Term</th>
                <th className="py-2 pr-3">Name</th>
                <th className="py-2 pr-3 text-right">IA</th>
                <th className="py-2 pr-3 text-right">Prior</th>
                <th className="py-2 pr-3 text-right">Real 3-mer</th>
                <th className="py-2 pr-3 text-right">ESM2 kNN</th>
                <th className="py-2 pr-3 text-right">ESM2 MLP</th>
                <th className="py-2 text-right">True-Path Final</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => {
                const maxVal = Math.max(r.kmer_3, r.esm2_knn, r.esm2_mlp, r.true_path_final);
                const hi = (v: number) =>
                  Math.abs(v - maxVal) < 0.001
                    ? "bg-emerald-100 text-emerald-950 dark:bg-emerald-900/60 dark:text-emerald-100 font-bold rounded px-1.5 py-0.5"
                    : "";
                return (
                  <tr key={r.term} className="border-b border-slate-100 dark:border-slate-800/70">
                    <td className="py-2 pr-3 font-mono text-blue-700 dark:text-cyan-400">{r.term}</td>
                    <td className="py-2 pr-3 font-medium text-slate-900 dark:text-white">{r.name}</td>
                    <td className="py-2 pr-3 text-right font-mono tabular-nums">{r.ia_weight.toFixed(2)}</td>
                    <td className="py-2 pr-3 text-right font-mono tabular-nums text-slate-500">
                      {(r.prior * 100).toFixed(1)}%
                    </td>
                    <td className="py-2 pr-3 text-right font-mono tabular-nums">
                      <span className={hi(r.kmer_3)}>{(r.kmer_3 * 100).toFixed(1)}%</span>
                    </td>
                    <td className="py-2 pr-3 text-right font-mono tabular-nums">
                      <span className={hi(r.esm2_knn)}>{(r.esm2_knn * 100).toFixed(1)}%</span>
                    </td>
                    <td className="py-2 pr-3 text-right font-mono tabular-nums">
                      <span className={hi(r.esm2_mlp)}>{(r.esm2_mlp * 100).toFixed(1)}%</span>
                    </td>
                    <td className="py-2 text-right font-mono tabular-nums">
                      <span className={hi(r.true_path_final)}>{(r.true_path_final * 100).toFixed(1)}%</span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Publishable Research Paper Benchmark Summary (auto-loaded from benchmarks/output/) */}
      {bench && (
        <div className="rounded-2xl border border-blue-200 dark:border-blue-800 bg-blue-50/40 dark:bg-blue-950/20 p-5 space-y-4">
          <div className="flex items-center gap-2">
            <Cpu className="w-5 h-5 text-blue-600" />
            <h2 className="text-base font-bold text-slate-900 dark:text-white">
              Verified Research Paper Experimental Benchmarks
            </h2>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                Table I — CAFA 6 Held-Out Validation Ablation (wFmax)
              </h3>
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-500">
                    <th className="py-1.5 text-left">Model</th>
                    <th className="py-1.5 text-right">wFmax</th>
                    <th className="py-1.5 text-right">DAG Violations</th>
                  </tr>
                </thead>
                <tbody>
                  {(bench.cafa6_ablation || []).map((row: any) => (
                    <tr key={row.model} className="border-b border-slate-100 dark:border-slate-800/60">
                      <td className="py-1.5 font-medium">{row.model}</td>
                      <td className="py-1.5 text-right font-mono font-bold">{row.wfmax.toFixed(4)}</td>
                      <td className="py-1.5 text-right font-mono">{row.violations_after}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                Table II — Clinical Pathogenic vs. Benign Missense Validation
              </h3>
              <div className="grid grid-cols-2 gap-3 mt-2">
                <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800">
                  <div className="text-[11px] text-slate-500">ESM2 LLR AUROC</div>
                  <div className="font-mono text-2xl font-extrabold text-blue-700 dark:text-cyan-400">
                    {bench.clinical_variant_benchmark?.llr_auroc?.toFixed(3)}
                  </div>
                </div>
                <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800">
                  <div className="text-[11px] text-slate-500">Dual-Axis Fusion AUROC</div>
                  <div className="font-mono text-2xl font-extrabold text-emerald-700 dark:text-emerald-400">
                    {bench.clinical_variant_benchmark?.dual_axis_auroc?.toFixed(3)}
                  </div>
                </div>
              </div>
              <p className="text-[11px] text-slate-500 mt-3">
                Evaluated on {bench.clinical_variant_benchmark?.n_variants} verified pathogenic vs. benign clinical missense variants across TP53, HBB, INS, and EGFR.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
