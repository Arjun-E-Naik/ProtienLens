"use client";

import React, { useEffect, useState } from "react";
import {
  Download,
  FileJson,
  FileSpreadsheet,
  FolderKanban,
  Printer,
  Save,
  Trash2,
} from "lucide-react";
import { api, API_BASE } from "@/lib/api";
import type { SavedCaseSummary } from "@/lib/types";
import { useWorkspace } from "@/context/WorkspaceContext";

export default function CasesPage() {
  const { institution } = useWorkspace();
  const [cases, setCases] = useState<SavedCaseSummary[]>([]);
  const [selected, setSelected] = useState<(SavedCaseSummary & { payload: Record<string, any> }) | null>(null);
  const [notes, setNotes] = useState("");
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  const loadList = async () => {
    try {
      const list = await api.listCases();
      setCases(list);
      if (list.length > 0 && !selected) {
        const det = await api.getCaseDetail(list[0].id);
        setSelected(det);
        setNotes(det.clinician_notes || "");
      }
    } catch {
      // ignore
    }
  };

  useEffect(() => {
    loadList();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const openCase = async (id: number) => {
    const det = await api.getCaseDetail(id);
    setSelected(det);
    setNotes(det.clinician_notes || "");
  };

  const handleSaveNotes = async () => {
    if (!selected) return;
    await api.updateCaseNotes(selected.id, notes);
    setStatusMsg("Notes updated in SQLite.");
    setTimeout(() => setStatusMsg(null), 2500);
    loadList();
  };

  const handleDelete = async (id: number) => {
    await api.deleteCase(id);
    if (selected?.id === id) setSelected(null);
    loadList();
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4 no-print">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white flex items-center gap-2">
            <FolderKanban className="w-6 h-6 text-blue-600" />
            Saved Clinical &amp; Research Cases (SQLite Vault)
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Persistent local institutional workspace with SHA-256 provenance export and printable white-label dossiers.
          </p>
        </div>
        {selected && (
          <div className="flex items-center gap-2">
            <a
              href={`${API_BASE}/api/export/${selected.id}?fmt=json`}
              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs font-semibold hover:bg-slate-50"
            >
              <FileJson className="w-3.5 h-3.5 text-blue-600" /> JSON Dossier (SHA-256)
            </a>
            <a
              href={`${API_BASE}/api/export/${selected.id}?fmt=csv`}
              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs font-semibold hover:bg-slate-50"
            >
              <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-600" /> CSV Matrix
            </a>
            <button
              onClick={() => window.print()}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold"
            >
              <Printer className="w-3.5 h-3.5" /> Print PDF Report
            </button>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Case List */}
        <div className="no-print lg:col-span-4 space-y-2.5">
          {cases.length === 0 ? (
            <div className="p-6 rounded-2xl border border-dashed border-slate-300 dark:border-slate-700 text-center text-xs text-slate-500">
              No saved cases yet. Click <strong>Save Case</strong> in the 3D Studio or Variant DMS tab to persist analyses here.
            </div>
          ) : (
            cases.map((c) => (
              <div
                key={c.id}
                onClick={() => openCase(c.id)}
                className={`cursor-pointer p-3.5 rounded-xl border transition-colors bg-white dark:bg-slate-900 ${
                  selected?.id === c.id
                    ? "border-blue-500 ring-2 ring-blue-500/20"
                    : "border-slate-200 dark:border-slate-800 hover:border-blue-300"
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-mono text-[11px] font-bold text-blue-600 dark:text-cyan-400">
                    {c.case_code}
                  </span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(c.id);
                    }}
                    className="p-1 text-slate-400 hover:text-rose-600"
                    title="Delete Case"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
                <div className="text-xs font-bold text-slate-900 dark:text-white mt-1">
                  {c.title}
                </div>
                <div className="text-[11px] font-mono text-slate-500 mt-1">
                  {c.mutation ? `Variant ${c.mutation}` : "Wild-Type"} ·{" "}
                  {c.composite_risk_score != null ? `Risk ${c.composite_risk_score}/100` : c.uniprot_id || "Custom"}
                </div>
              </div>
            ))
          )}
        </div>

        {/* Printable White-Label Dossier View */}
        <div className="lg:col-span-8">
          {selected ? (
            <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 space-y-5">
              {/* Institutional White-Label Letterhead */}
              <div className="pb-4 border-b border-slate-200 dark:border-slate-800 flex flex-wrap items-start justify-between gap-4">
                <div>
                  <div className="text-xs font-bold uppercase tracking-wider text-blue-700 dark:text-cyan-400">
                    {institution.institution_name}
                  </div>
                  <div className="text-[11px] text-slate-500">
                    {institution.department} · {institution.location}
                  </div>
                  <h2 className="text-xl font-extrabold text-slate-900 dark:text-white mt-2">
                    {selected.title}
                  </h2>
                </div>
                <div className="text-right font-mono text-[11px] text-slate-500">
                  <div className="font-bold text-slate-800 dark:text-slate-200">{selected.case_code}</div>
                  <div>{new Date(selected.created_at).toLocaleString()}</div>
                  <div>SHA-256: {selected.sequence_sha256.slice(0, 12)}</div>
                </div>
              </div>

              {/* Key Quantitative Summary */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                  <div className="text-[11px] text-slate-500">Protein / Accession</div>
                  <div className="font-mono text-xs font-bold mt-0.5 truncate">
                    {selected.uniprot_id || selected.protein_name}
                  </div>
                </div>
                <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                  <div className="text-[11px] text-slate-500">Mutation</div>
                  <div className="font-mono text-xs font-bold mt-0.5">
                    {selected.mutation || "Wild-Type"}
                  </div>
                </div>
                <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                  <div className="text-[11px] text-slate-500">Dual-Axis Risk</div>
                  <div className="font-mono text-xs font-bold mt-0.5">
                    {selected.composite_risk_score != null
                      ? `${selected.composite_risk_score.toFixed(1)} / 100`
                      : "Function Profile"}
                  </div>
                </div>
                <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                  <div className="text-[11px] text-slate-500">ESM2 LLR</div>
                  <div className="font-mono text-xs font-bold mt-0.5">
                    {selected.evolutionary_llr != null ? selected.evolutionary_llr.toFixed(2) : "—"}
                  </div>
                </div>
              </div>

              {/* Clinician / Researcher Notes */}
              <div className="space-y-2">
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-200">
                  Clinician / Researcher Review Notes
                </label>
                <textarea
                  rows={4}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 text-xs"
                />
                <div className="flex items-center justify-between no-print">
                  <span className="text-xs text-emerald-600">{statusMsg}</span>
                  <button
                    onClick={handleSaveNotes}
                    className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-slate-900 dark:bg-blue-600 text-white text-xs font-semibold"
                  >
                    <Save className="w-3.5 h-3.5" /> Save Notes
                  </button>
                </div>
              </div>

              {/* Disclaimer Footer */}
              <div className="pt-4 border-t border-slate-200 dark:border-slate-800 text-[11px] text-slate-500 leading-relaxed flex items-center justify-between gap-2">
                <span>{institution.report_disclaimer}</span>
                <Download className="w-4 h-4 shrink-0 no-print text-slate-400" />
              </div>
            </div>
          ) : (
            <div className="p-12 rounded-2xl border border-dashed border-slate-300 dark:border-slate-700 text-center text-sm text-slate-500">
              Select a saved case to inspect its institutional audit dossier.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
