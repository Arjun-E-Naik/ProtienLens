"use client";

import React, { useEffect, useState } from "react";
import { CheckCircle2, GitBranch, Loader2 } from "lucide-react";
import { useWorkspace } from "@/context/WorkspaceContext";
import { InteractiveDAG } from "@/components/InteractiveDAG";

export default function DAGPage() {
  const { activeProtein, presets, runQuickProtein, isLoadingProtein } = useWorkspace();
  const [aspect, setAspect] = useState<"MF" | "BP" | "CC">("MF");

  useEffect(() => {
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
        <p className="text-sm">Building Transitive-Reduced Gene Ontology DAG...</p>
      </div>
    );
  }

  const currentDag = activeProtein.dags[aspect];
  const audit = activeProtein.dag_audit;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white flex items-center gap-2">
            <GitBranch className="w-6 h-6 text-amber-600" />
            Interactive True Path Rule DAG Explorer
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Protein: <strong>{activeProtein.protein_name}</strong> · Pan, zoom, and click any node to inspect mathematical monotonicity propagation.
          </p>
        </div>

        <div className="flex items-center gap-2 bg-white dark:bg-slate-900 p-1 rounded-xl border border-slate-200 dark:border-slate-800 text-xs font-semibold">
          {(["MF", "BP", "CC"] as const).map((asp) => (
            <button
              key={asp}
              onClick={() => setAspect(asp)}
              className={`px-3.5 py-1.5 rounded-lg ${
                aspect === asp
                  ? "bg-blue-600 text-white"
                  : "text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"
              }`}
            >
              {asp} ({activeProtein.dags[asp].node_count} nodes)
            </button>
          ))}
        </div>
      </div>

      {/* Audit Metrics Strip */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
          <div className="text-xs text-slate-500">Raw Contradictions Detected</div>
          <div className="font-mono text-xl font-extrabold text-rose-600 mt-1 tabular-nums">
            {audit.violations_before} pairs
          </div>
        </div>
        <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
          <div className="text-xs text-slate-500">Post-Repair Violations</div>
          <div className="font-mono text-xl font-extrabold text-emerald-600 mt-1 flex items-center gap-1.5 tabular-nums">
            <CheckCircle2 className="w-5 h-5" /> {audit.violations_after} (0.00%)
          </div>
        </div>
        <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
          <div className="text-xs text-slate-500">Ancestor Terms Repaired</div>
          <div className="font-mono text-xl font-extrabold text-amber-600 mt-1 tabular-nums">
            {audit.terms_repaired} terms
          </div>
        </div>
        <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
          <div className="text-xs text-slate-500">Fixed-Point Convergence</div>
          <div className="font-mono text-xl font-extrabold text-slate-900 dark:text-white mt-1 tabular-nums">
            {audit.convergence_iterations} passes
          </div>
        </div>
      </div>

      {/* Interactive React Flow Graph */}
      <InteractiveDAG key={`${activeProtein.sequence_sha256}-${aspect}`} dag={currentDag} />

      {/* True Path Repair Audit Log Table */}
      <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5">
        <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-3">
          True Path Rule Monotonicity Repair Audit Log (Top Elevated Ancestors)
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-500">
                <th className="py-2 pr-4">GO Term</th>
                <th className="py-2 pr-4">Name</th>
                <th className="py-2 pr-4">Aspect</th>
                <th className="py-2 pr-4 text-right">Raw Ensemble</th>
                <th className="py-2 pr-4 text-right">True-Path Final</th>
                <th className="py-2 text-right">Repair Delta</th>
              </tr>
            </thead>
            <tbody>
              {audit.repair_log.slice(0, 15).map((r) => (
                <tr key={r.term} className="border-b border-slate-100 dark:border-slate-800/60">
                  <td className="py-2 pr-4 font-mono text-blue-700 dark:text-cyan-400">{r.term}</td>
                  <td className="py-2 pr-4 font-medium text-slate-900 dark:text-white">{r.name}</td>
                  <td className="py-2 pr-4 font-mono">{r.aspect}</td>
                  <td className="py-2 pr-4 text-right font-mono tabular-nums">
                    {(r.raw_score * 100).toFixed(1)}%
                  </td>
                  <td className="py-2 pr-4 text-right font-mono font-bold tabular-nums">
                    {(r.propagated_score * 100).toFixed(1)}%
                  </td>
                  <td className="py-2 text-right font-mono font-bold text-amber-600 dark:text-amber-400 tabular-nums">
                    +{(r.delta * 100).toFixed(1)}%
                  </td>
                </tr>
              ))}
              {audit.repair_log.length === 0 && (
                <tr>
                  <td colSpan={6} className="py-6 text-center text-slate-500">
                    All predicted probabilities were already monotonically consistent.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
