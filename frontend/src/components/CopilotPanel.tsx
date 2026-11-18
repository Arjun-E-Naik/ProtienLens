"use client";

import React, { useState } from "react";
import Link from "next/link";
import { BookOpen, FlaskConical, Loader2, Settings, Sparkles, Stethoscope } from "lucide-react";
import { api } from "@/lib/api";
import type { CopilotSynthesisResponse } from "@/lib/types";
import { useWorkspace } from "@/context/WorkspaceContext";

interface CopilotPanelProps {
  evidencePacket: Record<string, any>;
}

export function CopilotPanel({ evidencePacket }: CopilotPanelProps) {
  const { aiStatus } = useWorkspace();
  const [audience, setAudience] = useState<"clinical" | "research" | "student">("clinical");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<CopilotSynthesisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const runSynthesis = async (modeOverride?: "clinical" | "research" | "student") => {
    const targetMode = modeOverride || audience;
    setAudience(targetMode);
    setLoading(true);
    setError(null);
    try {
      const res = await api.synthesizeCopilot({
        evidence_packet: evidencePacket,
        audience_mode: targetMode,
      });
      setResult(res);
    } catch (e: any) {
      setError(e?.message || "Failed to synthesize explanation.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-cyan-400">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-900 dark:text-white">
              Evidence-Grounded Explainable AI (XAI) Co-Pilot
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Active Engine:{" "}
              <strong className="text-slate-800 dark:text-slate-200">
                {aiStatus?.is_llm_connected
                  ? `${aiStatus.active_provider.toUpperCase()} (${aiStatus.model_name})`
                  : "Local Deterministic Evidence Engine"}
              </strong>{" "}
              ·{" "}
              <Link href="/settings" className="text-blue-600 dark:text-cyan-400 hover:underline inline-flex items-center gap-1">
                <Settings className="w-3 h-3" /> Configure Gemini / Grok Key
              </Link>
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {(
            [
              ["clinical", "Clinical Geneticist", Stethoscope],
              ["research", "Research Scientist", FlaskConical],
              ["student", "College / Student", BookOpen],
            ] as const
          ).map(([mode, label, Icon]) => (
            <button
              key={mode}
              onClick={() => runSynthesis(mode)}
              disabled={loading}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border transition-colors ${
                audience === mode && result
                  ? "bg-blue-600 text-white border-blue-600"
                  : "bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-slate-200 border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-700"
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              {label}
            </button>
          ))}
        </div>
      </div>

      {!result && !loading && (
        <div className="p-4 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 flex flex-wrap items-center justify-between gap-3">
          <p className="text-xs text-slate-600 dark:text-slate-300">
            Generate a strictly citation-anchored XAI briefing directly from your computed ESM2 LLR, 3D Pocket DMS, True-Path DAG, and live ClinVar/OpenTargets records.
          </p>
          <button
            onClick={() => runSynthesis(audience)}
            className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold"
          >
            Generate Grounded XAI Briefing
          </button>
        </div>
      )}

      {loading && (
        <div className="p-6 flex items-center justify-center gap-2 text-sm text-slate-500">
          <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
          Synthesizing grounded explanation from live ML evidence packet...
        </div>
      )}

      {error && (
        <div className="p-3 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-xs text-rose-700 dark:text-rose-300">
          {error}
        </div>
      )}

      {result && !loading && (
        <div className="space-y-4">
          <div className="p-3.5 rounded-lg bg-blue-50/70 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-800">
            <div className="flex items-center justify-between gap-2 mb-1">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-blue-700 dark:text-cyan-300">
                {result.is_live_llm ? `Live ${result.provider_used.toUpperCase()} Synthesis` : "Deterministic Evidence-Cited Synthesis"} · {result.audience_mode} mode
              </span>
            </div>
            <h4 className="text-sm font-bold text-slate-900 dark:text-white">{result.headline}</h4>
            <p className="text-xs text-slate-700 dark:text-slate-200 mt-1.5 leading-relaxed">
              {result.executive_summary}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div className="p-3.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50/60 dark:bg-slate-800/40">
              <div className="text-xs font-bold text-slate-900 dark:text-white mb-1">
                3D Structural Mechanism
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                {result.structural_mechanism}
              </p>
            </div>
            <div className="p-3.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50/60 dark:bg-slate-800/40">
              <div className="text-xs font-bold text-slate-900 dark:text-white mb-1">
                Gene Ontology &amp; DAG Impact
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                {result.functional_ontology_impact}
              </p>
            </div>
            <div className="p-3.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50/60 dark:bg-slate-800/40">
              <div className="text-xs font-bold text-slate-900 dark:text-white mb-1">
                Actionable Next Steps
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                {result.therapeutic_and_actionable_next_steps}
              </p>
            </div>
          </div>

          {result.key_citations.length > 0 && (
            <div className="pt-2 border-t border-slate-200 dark:border-slate-800">
              <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1.5">
                Verified Quantitative Evidence Citations
              </div>
              <ul className="flex flex-wrap gap-2">
                {result.key_citations.map((c, idx) => (
                  <li
                    key={idx}
                    className="text-[11px] font-mono px-2.5 py-1 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700"
                  >
                    {c}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
