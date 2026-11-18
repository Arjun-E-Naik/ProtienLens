"use client";

import React, { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  BookmarkPlus,
  Check,
  Dna,
  GitBranch,
  Loader2,
  Pill,
  Search,
} from "lucide-react";
import {
  Area,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useWorkspace } from "@/context/WorkspaceContext";
import { api } from "@/lib/api";
import { ProteinViewer3D } from "@/components/ProteinViewer3D";
import { CopilotPanel } from "@/components/CopilotPanel";

export default function StudioPage() {
  const { activeProtein, setActiveProtein, presets, runQuickProtein, isLoadingProtein } =
    useWorkspace();
  const [aspectTab, setAspectTab] = useState<"MF" | "BP" | "CC">("MF");
  const [searchQuery, setSearchQuery] = useState("");
  const [minConf, setMinConf] = useState(0.2);
  const [savedNotice, setSavedNotice] = useState<string | null>(null);

  // Auto-load p53 if user lands directly on /studio
  useEffect(() => {
    if (!activeProtein && !isLoadingProtein && presets.length > 0) {
      const p53 = presets[0];
      runQuickProtein({
        uniprot_id: p53.uniprot_id,
        sequence: p53.sequence,
        protein_name: p53.name,
      }).catch(() => {});
    }
  }, [activeProtein, isLoadingProtein, presets, runQuickProtein]);

  const filteredTerms = useMemo(() => {
    if (!activeProtein) return [];
    const list = activeProtein.categorized[aspectTab] || [];
    const q = searchQuery.trim().toLowerCase();
    return list.filter(
      (item) =>
        item.score >= minConf &&
        (!q ||
          item.name.toLowerCase().includes(q) ||
          item.term.toLowerCase().includes(q))
    );
  }, [activeProtein, aspectTab, searchQuery, minConf]);

  const chartData = useMemo(() => {
    if (!activeProtein) return [];
    const prof = activeProtein.xai.residue_profile;
    // Downsample slightly only if >250 aa for super snappy chart rendering
    const step = prof.length > 260 ? 2 : 1;
    return prof
      .filter((_, i) => i % step === 0)
      .map((pt) => ({
        pos: pt.position,
        label: `${pt.aa}${pt.position}`,
        saliency: Number((pt.saliency * 100).toFixed(1)),
        plddt: pt.plddt,
      }));
  }, [activeProtein]);

  const handleSaveCase = async () => {
    if (!activeProtein) return;
    try {
      const res = await api.saveCase({
        title: `${activeProtein.protein_name} — Function & 3D Profile`,
        protein_name: activeProtein.protein_name,
        uniprot_id: activeProtein.uniprot_id,
        gene_symbol: activeProtein.bio_evidence?.uniprot?.gene_symbol || null,
        sequence_sha256: activeProtein.sequence_sha256,
        mode: "research",
        payload: activeProtein as any,
      });
      setSavedNotice(`Saved ${res.case_code}`);
      setTimeout(() => setSavedNotice(null), 3500);
    } catch {
      setSavedNotice("Save failed");
    }
  };

  if (isLoadingProtein || !activeProtein) {
    return (
      <div className="p-16 flex flex-col items-center justify-center gap-3 text-slate-500">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        <p className="text-sm font-medium">
          Running ESM2 Attention Rollout, Multi-Label MLP + kNN, and True Path DAG Propagation...
        </p>
      </div>
    );
  }

  const drugs = activeProtein.bio_evidence?.open_targets?.drugs || [];
  const diseases = activeProtein.bio_evidence?.uniprot?.diseases || [];

  const copilotPacket = {
    protein_name: activeProtein.protein_name,
    uniprot_id: activeProtein.uniprot_id,
    sequence_length: activeProtein.sequence_length,
    mean_plddt: activeProtein.structure.mean_plddt,
    top_mf: activeProtein.categorized.MF.slice(0, 5),
    top_bp: activeProtein.categorized.BP.slice(0, 5),
    top_cc: activeProtein.categorized.CC.slice(0, 4),
    dag_audit: {
      violations_before: activeProtein.dag_audit.violations_before,
      violations_after: activeProtein.dag_audit.violations_after,
      terms_repaired: activeProtein.dag_audit.terms_repaired,
    },
    drugs: drugs.slice(0, 5),
  };

  return (
    <div className="space-y-6">
      {/* Top Bar with Preset Switcher & Actions */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white">
              {activeProtein.protein_name}
            </h1>
            {activeProtein.uniprot_id && (
              <span className="font-mono text-xs px-2.5 py-0.5 rounded-full bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-cyan-300 font-semibold">
                {activeProtein.uniprot_id}
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500 mt-0.5 font-mono">
            SHA-256: {activeProtein.sequence_sha256.slice(0, 14)} · Backbone:{" "}
            {activeProtein.model_metadata.backbone} ·{" "}
            {activeProtein.cached ? "Cached 0 ms" : `${activeProtein.latency_ms} ms`}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <select
            value={activeProtein.uniprot_id || ""}
            onChange={(e) => {
              const found = presets.find((p) => p.uniprot_id === e.target.value);
              if (found) {
                runQuickProtein({
                  uniprot_id: found.uniprot_id,
                  sequence: found.sequence,
                  protein_name: found.name,
                });
              }
            }}
            className="px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs font-medium text-slate-800 dark:text-slate-100"
          >
            <option value="">Switch Benchmark Protein...</option>
            {presets.map((p) => (
              <option key={p.uniprot_id} value={p.uniprot_id}>
                {p.uniprot_id} — {p.name}
              </option>
            ))}
          </select>

          <button
            onClick={handleSaveCase}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 hover:bg-slate-50 text-xs font-semibold"
          >
            {savedNotice ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <BookmarkPlus className="w-3.5 h-3.5" />}
            {savedNotice || "Save Case"}
          </button>

          <Link
            href="/variants"
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold"
          >
            <Dna className="w-3.5 h-3.5" /> Mutate &amp; Scan 3D Pocket
          </Link>
        </div>
      </div>

      {/* 4 Responsive Non-Truncating Clinical KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
          <div className="text-xs text-slate-500">Sequence &amp; Molecular Mass</div>
          <div className="font-mono text-xl font-extrabold text-slate-900 dark:text-white mt-1 tabular-nums">
            {activeProtein.sequence_length} aa
          </div>
          <div className="text-[11px] text-slate-500 mt-0.5">
            Est. {activeProtein.est_mass_kda} kDa
          </div>
        </div>
        <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
          <div className="text-xs text-slate-500">Active GO Annotations</div>
          <div className="font-mono text-xl font-extrabold text-blue-700 dark:text-cyan-400 mt-1 tabular-nums">
            {activeProtein.summary_counts.total_active} terms
          </div>
          <div className="text-[11px] text-slate-500 mt-0.5 font-mono">
            MF {activeProtein.summary_counts.MF} · BP {activeProtein.summary_counts.BP} · CC{" "}
            {activeProtein.summary_counts.CC}
          </div>
        </div>
        <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
          <div className="text-xs text-slate-500">AlphaFold Mean pLDDT</div>
          <div className="font-mono text-xl font-extrabold text-emerald-700 dark:text-emerald-400 mt-1 tabular-nums">
            {activeProtein.structure.mean_plddt != null
              ? `${activeProtein.structure.mean_plddt.toFixed(1)} / 100`
              : "Sequence Only"}
          </div>
          <div className="text-[11px] text-slate-500 mt-0.5">
            XAI Hotspots: {activeProtein.xai.hotspot_count} sites
          </div>
        </div>
        <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
          <div className="text-xs text-slate-500">True Path DAG Integrity</div>
          <div className="font-mono text-xl font-extrabold text-amber-600 dark:text-amber-400 mt-1 tabular-nums">
            {activeProtein.dag_audit.violations_before} &rarr; 0
          </div>
          <div className="text-[11px] text-slate-500 mt-0.5">
            {activeProtein.dag_audit.terms_repaired} ancestor nodes repaired
          </div>
        </div>
      </div>

      {/* Main Split: 3D Viewer + GO Predictions */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
        <div className="xl:col-span-7 space-y-4">
          <ProteinViewer3D
            pdbContent={activeProtein.structure.pdb_content}
            alphafoldId={activeProtein.structure.alphafold_id}
            hotspotIndices={activeProtein.xai.hotspot_indices}
            height={440}
          />

          {/* Dual-Track Attention Rollout Saliency + AlphaFold pLDDT Chart */}
          <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4">
            <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
              <div>
                <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                  Residue-Level XAI Attention Rollout vs. AlphaFold pLDDT Confidence
                </h3>
                <p className="text-[11px] text-slate-500">
                  {activeProtein.xai.method}
                </p>
              </div>
              <div className="flex items-center gap-3 text-[11px]">
                <span className="inline-flex items-center gap-1 text-amber-600 font-semibold">
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-500" /> XAI Saliency (%)
                </span>
                <span className="inline-flex items-center gap-1 text-blue-600 font-semibold">
                  <span className="w-2.5 h-2.5 rounded-full bg-blue-600" /> pLDDT Confidence
                </span>
              </div>
            </div>
            <div className="h-52 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={chartData}>
                  <XAxis dataKey="pos" tick={{ fontSize: 10 }} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 10 }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#0f172a",
                      borderColor: "#334155",
                      color: "#f8fafc",
                      fontSize: 12,
                      borderRadius: 8,
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="saliency"
                    name="XAI Saliency %"
                    fill="#f59e0b"
                    fillOpacity={0.22}
                    stroke="#d97706"
                    strokeWidth={1.8}
                  />
                  <Line
                    type="monotone"
                    dataKey="plddt"
                    name="AlphaFold pLDDT"
                    stroke="#2563eb"
                    strokeWidth={1.8}
                    dot={false}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Right: Categorized GO Terms + Live OpenTargets Drugs */}
        <div className="xl:col-span-5 space-y-4">
          <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 space-y-3">
            <div className="flex items-center justify-between gap-2">
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                Predicted Gene Ontology Functions
              </h3>
              <Link
                href="/dag"
                className="text-xs font-semibold text-blue-600 dark:text-cyan-400 hover:underline inline-flex items-center gap-1"
              >
                <GitBranch className="w-3.5 h-3.5" /> Interactive DAG
              </Link>
            </div>

            {/* Aspect Tabs */}
            <div className="grid grid-cols-3 gap-1.5 bg-slate-100 dark:bg-slate-800 p-1 rounded-lg text-xs font-semibold">
              {(
                [
                  ["MF", "Molecular (MF)"],
                  ["BP", "Biological (BP)"],
                  ["CC", "Cellular (CC)"],
                ] as const
              ).map(([asp, lbl]) => (
                <button
                  key={asp}
                  onClick={() => setAspectTab(asp)}
                  className={`py-1.5 rounded-md transition-colors ${
                    aspectTab === asp
                      ? "bg-white dark:bg-slate-700 text-blue-700 dark:text-cyan-300 shadow-sm"
                      : "text-slate-600 dark:text-slate-400"
                  }`}
                >
                  {lbl} ({activeProtein.categorized[asp].filter((x) => x.score >= minConf).length})
                </button>
              ))}
            </div>

            {/* Search & Threshold */}
            <div className="flex items-center gap-2">
              <div className="relative flex-1">
                <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Filter GO name or ID..."
                  className="w-full pl-8 pr-3 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950"
                />
              </div>
              <div className="flex items-center gap-1.5 text-[11px] font-mono text-slate-500">
                <span>&ge;{(minConf * 100).toFixed(0)}%</span>
                <input
                  type="range"
                  min={0.05}
                  max={0.85}
                  step={0.05}
                  value={minConf}
                  onChange={(e) => setMinConf(Number(e.target.value))}
                  className="w-20"
                />
              </div>
            </div>

            {/* GO List */}
            <div className="max-h-[380px] overflow-y-auto space-y-2 pr-1">
              {filteredTerms.slice(0, 25).map((item) => (
                <div
                  key={item.term}
                  className="p-2.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-800/40"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-bold text-slate-900 dark:text-white truncate">
                      {item.name}
                    </span>
                    <span className="font-mono text-xs font-bold text-blue-700 dark:text-cyan-400 tabular-nums shrink-0">
                      {(item.score * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full h-1.5 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden mt-1.5">
                    <div
                      className={`h-full rounded-full ${
                        item.repaired ? "bg-amber-500" : "bg-blue-600"
                      }`}
                      style={{ width: `${Math.min(100, item.score * 100)}%` }}
                    />
                  </div>
                  <div className="flex items-center justify-between text-[10px] font-mono text-slate-500 mt-1">
                    <span>
                      {item.term} · IA {item.ia.toFixed(2)}
                    </span>
                    {item.repaired && (
                      <span className="text-amber-600 dark:text-amber-400 font-semibold">
                        DAG Repaired +{(item.repair_delta * 100).toFixed(1)}%
                      </span>
                    )}
                  </div>
                </div>
              ))}
              {filteredTerms.length === 0 && (
                <p className="text-xs text-slate-500 text-center py-6">
                  No terms match the current filter / threshold.
                </p>
              )}
            </div>
          </div>

          {/* Live Federated Biomedical Evidence (Open Targets & UniProt) */}
          <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 space-y-3">
            <div className="flex items-center gap-2">
              <Pill className="w-4 h-4 text-emerald-600" />
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                Federated Therapeutics &amp; Disease Grounding
              </h3>
            </div>
            {drugs.length > 0 ? (
              <div className="space-y-1.5">
                <div className="text-[11px] font-semibold text-slate-500 uppercase">
                  Open Targets Clinical Drugs
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {drugs.slice(0, 6).map((d: any) => (
                    <span
                      key={d.name}
                      className="text-[11px] px-2.5 py-1 rounded-md bg-emerald-50 dark:bg-emerald-950/50 text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 font-medium"
                    >
                      {d.name} (Ph {d.phase})
                    </span>
                  ))}
                </div>
              </div>
            ) : (
              <p className="text-xs text-slate-500">
                No direct Open Targets drugs cataloged for this accession (or offline mode).
              </p>
            )}
            {diseases.length > 0 && (
              <div className="space-y-1">
                <div className="text-[11px] font-semibold text-slate-500 uppercase">
                  UniProt Disease Associations
                </div>
                <ul className="text-xs text-slate-600 dark:text-slate-300 space-y-1">
                  {diseases.slice(0, 3).map((dis: any, idx: number) => (
                    <li key={idx} className="truncate">
                      • <strong>{dis.name}</strong> {dis.acronym ? `(${dis.acronym})` : ""}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Grounded XAI Co-Pilot */}
      <CopilotPanel evidencePacket={copilotPacket} />
    </div>
  );
}
