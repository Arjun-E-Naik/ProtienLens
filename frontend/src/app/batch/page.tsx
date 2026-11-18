"use client";

import React, { useState } from "react";
import Link from "next/link";
import { ArrowRight, FileSpreadsheet, Loader2, Play, Sparkles } from "lucide-react";
import { api, API_BASE } from "@/lib/api";

const SAMPLE_COHORT_CSV = `TP53,P04637,273,H,Oncology Driver Hotspot
TP53,P04637,175,H,Structural Zinc Pocket
TP53,P04637,72,R,Common Benign Polymorphism
HBB,P68871,7,V,Sickle Cell Variant
INS,P01308,96,Y,Akita Disulfide Disruption
GFP,P42212,66,H,Chromophore Engineering Shift`;

export default function BatchPage() {
  const [title, setTitle] = useState("Clinical Exome VUS Cohort Triage");
  const [csvText, setCsvText] = useState(SAMPLE_COHORT_CSV);
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState({ completed: 0, total: 0, status: "idle" });
  const [rows, setRows] = useState<Array<Record<string, any>>>([]);
  const [error, setError] = useState<string | null>(null);

  const runBatchTriage = async () => {
    setError(null);
    const lines = csvText
      .split(/\r?\n/)
      .map((l) => l.trim())
      .filter((l) => l && !l.startsWith("#") && !l.toLowerCase().startsWith("gene"));

    const items = lines.map((ln) => {
      const parts = ln.split(",").map((p) => p.trim());
      return {
        gene_symbol: parts[0] || undefined,
        uniprot_id: parts[1] || undefined,
        position: Number(parts[2]),
        mut_aa: (parts[3] || "A").toUpperCase(),
        label: parts[4] ? `${parts[0]} ${parts[4]}` : `${parts[0]} pos ${parts[2]}${parts[3]}`,
      };
    });

    if (!items.length || items.some((i) => !i.position || Number.isNaN(i.position))) {
      setError("Format each line as: GENE,UNIPROT_ID,POSITION,MUT_AA,OptionalLabel");
      return;
    }

    setRunning(true);
    setRows([]);
    setProgress({ completed: 0, total: items.length, status: "queued" });

    try {
      const started = await api.startBatch({ title, items });
      const es = new EventSource(`${API_BASE}/api/jobs/${started.job_uid}/stream`);

      es.addEventListener("progress", (ev: MessageEvent) => {
        const data = JSON.parse(ev.data);
        setProgress({
          completed: data.completed_items,
          total: data.total_items,
          status: data.status,
        });
        setRows(data.results || []);
        if (data.status === "completed" || data.status === "failed") {
          es.close();
          setRunning(false);
        }
      });

      es.onerror = () => {
        es.close();
        setRunning(false);
      };
    } catch (e: any) {
      setError(e?.message || "Batch job failed to start.");
      setRunning(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white flex items-center gap-2">
          <FileSpreadsheet className="w-6 h-6 text-blue-600" />
          Batch Patient Variant Cohort Triage (SSE Streaming)
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Screen multiple clinical mutations asynchronously using ESM2 Masked-Marginal LLR, True-Path ΔGO_IA, and AlphaFold 3D pLDDT — automatically ranked highest pathogenicity risk first.
        </p>
      </div>

      <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">
              Cohort Job Title
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 text-sm"
            />
          </div>
          <div className="flex items-end justify-end gap-2">
            <button
              type="button"
              onClick={() => setCsvText(SAMPLE_COHORT_CSV)}
              className="px-3.5 py-2 rounded-lg border border-slate-300 dark:border-slate-700 text-xs font-semibold hover:bg-slate-50 dark:hover:bg-slate-800"
            >
              Load Clinical Demo Cohort
            </button>
            <button
              type="button"
              onClick={runBatchTriage}
              disabled={running}
              className="inline-flex items-center gap-2 px-5 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-bold"
            >
              {running ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
              Run Streaming Triage
            </button>
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">
            Variant List (CSV Format: <span className="font-mono">GENE,UNIPROT_ID,POSITION,MUT_AA,Note</span>)
          </label>
          <textarea
            rows={6}
            value={csvText}
            onChange={(e) => setCsvText(e.target.value)}
            className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 font-mono text-xs"
          />
        </div>

        {error && (
          <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-700">
            {error}
          </div>
        )}

        {/* Real-time SSE Progress Bar */}
        {progress.total > 0 && (
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="font-semibold text-blue-700 dark:text-cyan-400">
                SSE Stream Status: {progress.status.toUpperCase()}
              </span>
              <span>
                {progress.completed} / {progress.total} variants scored
              </span>
            </div>
            <div className="w-full h-2.5 rounded-full bg-slate-200 dark:bg-slate-800 overflow-hidden">
              <div
                className="h-full bg-blue-600 transition-all duration-300"
                style={{ width: `${(progress.completed / Math.max(1, progress.total)) * 100}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Risk-Ranked Triage Table */}
      {rows.length > 0 && (
        <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-amber-500" />
              Risk-Prioritized Clinical Triage Queue
            </h2>
            <span className="text-xs text-slate-500">Sorted by Dual-Axis Composite Risk</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-500">
                  <th className="py-2 pr-3">Rank</th>
                  <th className="py-2 pr-3">Variant / Label</th>
                  <th className="py-2 pr-3 text-right">Composite Risk</th>
                  <th className="py-2 pr-3 text-right">ESM2 LLR</th>
                  <th className="py-2 pr-3 text-right">FDI (ΔGO)</th>
                  <th className="py-2 pr-3 text-right">pLDDT</th>
                  <th className="py-2 pr-3">Assessment</th>
                  <th className="py-2 text-right">3D Pocket</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r, idx) => (
                  <tr key={idx} className="border-b border-slate-100 dark:border-slate-800/70">
                    <td className="py-2.5 pr-3 font-mono font-bold text-slate-400">#{idx + 1}</td>
                    <td className="py-2.5 pr-3">
                      <div className="font-mono font-bold text-slate-900 dark:text-white">
                        {r.gene_symbol || r.uniprot_id} p.{r.mutation}
                      </div>
                      <div className="text-[11px] text-slate-500">{r.label}</div>
                    </td>
                    <td className="py-2.5 pr-3 text-right font-mono font-extrabold tabular-nums">
                      {r.composite_risk_score != null ? `${r.composite_risk_score.toFixed(1)} / 100` : "ERR"}
                    </td>
                    <td className="py-2.5 pr-3 text-right font-mono tabular-nums">
                      {r.evolutionary_llr != null ? r.evolutionary_llr.toFixed(2) : "—"}
                    </td>
                    <td className="py-2.5 pr-3 text-right font-mono tabular-nums">
                      {r.fdi_score != null ? r.fdi_score.toFixed(2) : "—"}
                    </td>
                    <td className="py-2.5 pr-3 text-right font-mono tabular-nums">
                      {r.plddt != null ? r.plddt.toFixed(1) : "—"}
                    </td>
                    <td className="py-2.5 pr-3">
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                          r.severity === "pathogenic"
                            ? "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300"
                            : r.severity === "likely_pathogenic"
                            ? "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300"
                            : r.severity === "vus"
                            ? "bg-sky-100 text-sky-800 dark:bg-sky-950 dark:text-sky-300"
                            : "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                        }`}
                      >
                        {r.acmg_cue || r.error}
                      </span>
                    </td>
                    <td className="py-2.5 text-right">
                      <Link
                        href="/variants"
                        className="inline-flex items-center gap-1 text-blue-600 dark:text-cyan-400 font-semibold hover:underline"
                      >
                        Inspect <ArrowRight className="w-3 h-3" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
