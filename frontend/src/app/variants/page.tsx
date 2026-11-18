"use client";

import React, { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import {
  AlertTriangle,
  BookmarkPlus,
  Check,
  CheckCircle2,
  Dna,
  ExternalLink,
  Flame,
  Loader2,
  Play,
  ShieldAlert,
  Sparkles,
} from "lucide-react";
import { useWorkspace } from "@/context/WorkspaceContext";
import { api } from "@/lib/api";
import { ProteinViewer3D } from "@/components/ProteinViewer3D";
import { PocketDMSHeatmap } from "@/components/PocketDMSHeatmap";
import { CopilotPanel } from "@/components/CopilotPanel";

const AMINO_ACIDS = "ACDEFGHIKLMNPQRSTVWY".split("");

function VariantsWorkspaceInner() {
  const searchParams = useSearchParams();
  const {
    presets,
    clinicalVariants,
    activeVariant,
    setActiveVariant,
  } = useWorkspace();

  const [uniprotId, setUniprotId] = useState("P04637");
  const [geneSymbol, setGeneSymbol] = useState("TP53");
  const [proteinName, setProteinName] = useState("Tumor Protein p53");
  const [position, setPosition] = useState(273);
  const [mutAA, setMutAA] = useState("H");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savedCode, setSavedCode] = useState<string | null>(null);

  const runSimulation = async (opts?: {
    uniprot_id?: string;
    gene_symbol?: string;
    protein_name?: string;
    position?: number;
    mut_aa?: string;
  }) => {
    const uid = opts?.uniprot_id ?? uniprotId;
    const gs = opts?.gene_symbol ?? geneSymbol;
    const pname = opts?.protein_name ?? proteinName;
    const pos = opts?.position ?? position;
    const aa = opts?.mut_aa ?? mutAA;

    setUniprotId(uid);
    setGeneSymbol(gs);
    setProteinName(pname);
    setPosition(pos);
    setMutAA(aa);
    setLoading(true);
    setError(null);
    setSavedCode(null);

    try {
      const preset = presets.find((p) => p.uniprot_id === uid);
      const res = await api.analyzeVariant({
        uniprot_id: uid,
        gene_symbol: gs,
        protein_name: pname,
        sequence: preset?.sequence,
        position: pos,
        mut_aa: aa,
        run_pocket_dms: true,
        max_pocket_residues: 8,
        include_bio_evidence: true,
      });
      setActiveVariant(res);
    } catch (e: any) {
      setError(e?.message || "Variant simulation failed.");
    } finally {
      setLoading(false);
    }
  };

  // Auto-run preset from query string or default TP53 R273H on initial mount
  useEffect(() => {
    const presetParam = searchParams.get("preset");
    if (presetParam && clinicalVariants.length > 0) {
      const found = clinicalVariants.find((v) => v.id === presetParam);
      if (found) {
        runSimulation({
          uniprot_id: found.uniprot_id,
          gene_symbol: found.gene_symbol,
          protein_name: found.protein_name,
          position: found.position,
          mut_aa: found.mut_aa,
        });
        return;
      }
    }
    if (!activeVariant && presets.length > 0 && !loading) {
      runSimulation({
        uniprot_id: "P04637",
        gene_symbol: "TP53",
        protein_name: "Tumor Protein p53",
        position: 273,
        mut_aa: "H",
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams, clinicalVariants.length, presets.length]);

  const handleSaveVariantCase = async () => {
    if (!activeVariant) return;
    try {
      const da = activeVariant.dual_axis_assessment;
      const res = await api.saveCase({
        title: `${activeVariant.gene_symbol || activeVariant.uniprot_id} p.${activeVariant.mutation} — 3D Pocket DMS Triage`,
        protein_name: activeVariant.protein_name,
        uniprot_id: activeVariant.uniprot_id,
        gene_symbol: activeVariant.gene_symbol,
        mutation: activeVariant.mutation,
        composite_risk_score: da.composite_risk_score,
        evolutionary_llr: da.evolutionary_llr,
        risk_tier: da.risk_tier,
        sequence_sha256: activeVariant.sequence_sha256,
        clinician_notes: `ACMG Cue: ${da.acmg_computational_cue}. LLR=${da.evolutionary_llr}, FDI=${da.fdi_score}.`,
        mode: "clinical",
        payload: activeVariant as any,
      });
      setSavedCode(res.case_code);
    } catch {
      setError("Could not save case to SQLite.");
    }
  };

  const severityStyles = (sev?: string) => {
    if (sev === "pathogenic")
      return "bg-rose-50 border-rose-300 text-rose-900 dark:bg-rose-950/50 dark:border-rose-700 dark:text-rose-200";
    if (sev === "likely_pathogenic")
      return "bg-amber-50 border-amber-300 text-amber-900 dark:bg-amber-950/50 dark:border-amber-700 dark:text-amber-200";
    if (sev === "vus")
      return "bg-sky-50 border-sky-300 text-sky-900 dark:bg-sky-950/50 dark:border-sky-700 dark:text-sky-200";
    return "bg-emerald-50 border-emerald-300 text-emerald-900 dark:bg-emerald-950/50 dark:border-emerald-700 dark:text-emerald-200";
  };

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 text-xs font-semibold text-blue-600 dark:text-cyan-400">
            <Dna className="w-4 h-4" />
            <span>Flagship Differentiator — Zero-Shot 3D-Pocket DMS + Dual-Axis VUS Triage</span>
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white mt-0.5">
            Clinical Variant Impact &amp; 3D-Pocket Deep Mutational Scanning
          </h1>
        </div>
        {activeVariant && (
          <button
            onClick={handleSaveVariantCase}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-slate-900 dark:bg-blue-600 hover:opacity-90 text-white text-xs font-semibold"
          >
            {savedCode ? <Check className="w-4 h-4 text-emerald-400" /> : <BookmarkPlus className="w-4 h-4" />}
            {savedCode ? `Saved ${savedCode}` : "Save Clinical Case to SQLite"}
          </button>
        )}
      </div>

      {/* Control Deck: Presets + Custom Mutagenesis */}
      <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 space-y-4">
        <div className="flex flex-wrap gap-2">
          {clinicalVariants.map((cv) => (
            <button
              key={cv.id}
              onClick={() =>
                runSimulation({
                  uniprot_id: cv.uniprot_id,
                  gene_symbol: cv.gene_symbol,
                  protein_name: cv.protein_name,
                  position: cv.position,
                  mut_aa: cv.mut_aa,
                })
              }
              disabled={loading}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono font-semibold border transition-colors ${
                uniprotId === cv.uniprot_id && position === cv.position && mutAA === cv.mut_aa
                  ? "bg-blue-600 text-white border-blue-600"
                  : "bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-slate-200 border-slate-200 dark:border-slate-700 hover:border-blue-400"
              }`}
            >
              {cv.gene_symbol} {cv.wt_aa}
              {cv.position}
              {cv.mut_aa}
            </button>
          ))}
        </div>

        <div className="grid grid-cols-2 md:grid-cols-5 gap-3 items-end">
          <div>
            <label className="block text-[11px] font-semibold text-slate-500 mb-1">UniProt ID</label>
            <input
              type="text"
              value={uniprotId}
              onChange={(e) => setUniprotId(e.target.value.toUpperCase())}
              className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 font-mono text-xs"
            />
          </div>
          <div>
            <label className="block text-[11px] font-semibold text-slate-500 mb-1">Gene Symbol</label>
            <input
              type="text"
              value={geneSymbol}
              onChange={(e) => setGeneSymbol(e.target.value.toUpperCase())}
              className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 font-mono text-xs"
            />
          </div>
          <div>
            <label className="block text-[11px] font-semibold text-slate-500 mb-1">Residue Position (1-based)</label>
            <input
              type="number"
              min={1}
              max={512}
              value={position}
              onChange={(e) => setPosition(Number(e.target.value))}
              className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 font-mono text-xs"
            />
          </div>
          <div>
            <label className="block text-[11px] font-semibold text-slate-500 mb-1">Mutant Amino Acid</label>
            <select
              value={mutAA}
              onChange={(e) => setMutAA(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 font-mono text-xs"
            >
              {AMINO_ACIDS.map((aa) => (
                <option key={aa} value={aa}>
                  {aa}
                </option>
              ))}
            </select>
          </div>
          <button
            onClick={() => runSimulation()}
            disabled={loading}
            className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-bold h-[36px]"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            Run Dual-Axis + Pocket DMS
          </button>
        </div>

        {error && (
          <div className="p-3 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 text-xs text-rose-700 dark:text-rose-300">
            {error}
          </div>
        )}
      </div>

      {loading && (
        <div className="p-12 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex flex-col items-center justify-center gap-3 text-slate-500">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
          <p className="text-sm font-medium">
            Computing ESM2 Masked-Marginal LLR, 5.0 Å AlphaFold Pocket Geometry, Batched 20-AA DMS Heatmap, and ClinVar Concordance...
          </p>
        </div>
      )}

      {activeVariant && !loading && (
        <>
          {/* Clinical Risk Assessment Banner */}
          <div
            className={`p-5 rounded-2xl border flex flex-wrap items-center justify-between gap-4 ${severityStyles(
              activeVariant.dual_axis_assessment.severity
            )}`}
          >
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                {activeVariant.dual_axis_assessment.severity === "benign" ? (
                  <CheckCircle2 className="w-5 h-5" />
                ) : activeVariant.dual_axis_assessment.severity === "vus" ? (
                  <AlertTriangle className="w-5 h-5" />
                ) : (
                  <ShieldAlert className="w-5 h-5" />
                )}
                <span className="font-mono text-sm font-bold">
                  {activeVariant.gene_symbol || activeVariant.uniprot_id} p.{activeVariant.mutation}
                </span>
                <span className="text-xs px-2 py-0.5 rounded-full bg-white/70 dark:bg-black/30 font-semibold">
                  {activeVariant.dual_axis_assessment.acmg_computational_cue}
                </span>
              </div>
              <div className="text-lg font-extrabold">
                {activeVariant.dual_axis_assessment.risk_tier}
              </div>
              <div className="text-xs opacity-90">
                NCBI ClinVar Status:{" "}
                <strong>
                  {activeVariant.bio_evidence?.clinvar?.summary_classification || "Offline / Querying"}
                </strong>
                {activeVariant.bio_evidence?.clinvar?.records?.[0]?.url && (
                  <a
                    href={activeVariant.bio_evidence.clinvar.records[0].url}
                    target="_blank"
                    rel="noreferrer"
                    className="ml-2 inline-flex items-center gap-0.5 underline"
                  >
                    ClinVar Record <ExternalLink className="w-3 h-3" />
                  </a>
                )}
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div className="text-right">
                <div className="text-[11px] font-semibold uppercase opacity-80">
                  Dual-Axis Risk Score
                </div>
                <div className="font-mono text-3xl font-black tabular-nums">
                  {activeVariant.dual_axis_assessment.composite_risk_score.toFixed(1)}
                  <span className="text-base font-normal opacity-75"> / 100</span>
                </div>
              </div>
            </div>
          </div>

          {/* 4 Transparent Auditable Score Components */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
              <div className="text-xs text-slate-500">ESM2 Masked-Marginal LLR</div>
              <div className="font-mono text-xl font-extrabold text-slate-900 dark:text-white mt-1 tabular-nums">
                {activeVariant.dual_axis_assessment.evolutionary_llr.toFixed(2)}
              </div>
              <div className="text-[11px] text-slate-500 mt-0.5">
                Conservation: {(activeVariant.dual_axis_assessment.conservation_index * 100).toFixed(0)}%
              </div>
            </div>
            <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
              <div className="text-xs text-slate-500">GO Functional Disruption (FDI)</div>
              <div className="font-mono text-xl font-extrabold text-blue-700 dark:text-cyan-400 mt-1 tabular-nums">
                {activeVariant.dual_axis_assessment.fdi_score.toFixed(2)}
              </div>
              <div className="text-[11px] text-slate-500 mt-0.5 font-mono">
                ΔEmb: {activeVariant.dual_axis_assessment.embedding_cosine_shift.toFixed(4)}
              </div>
            </div>
            <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
              <div className="text-xs text-slate-500">3D Site pLDDT Confidence</div>
              <div className="font-mono text-xl font-extrabold text-emerald-700 dark:text-emerald-400 mt-1 tabular-nums">
                {activeVariant.structural_pocket.target_plddt != null
                  ? activeVariant.structural_pocket.target_plddt.toFixed(1)
                  : "N/A"}
              </div>
              <div className="text-[11px] text-slate-500 mt-0.5 truncate">
                {activeVariant.structural_pocket.structural_region}
              </div>
            </div>
            <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
              <div className="text-xs text-slate-500">3D Microenvironment Shell</div>
              <div className="font-mono text-xl font-extrabold text-amber-600 dark:text-amber-400 mt-1 tabular-nums">
                {activeVariant.structural_pocket.all_5A_contact_count ?? 0} contacts
              </div>
              <div className="text-[11px] text-slate-500 mt-0.5">
                Within 5.0 Å · 8 Å burial: {activeVariant.structural_pocket.burial_contacts_8A}
              </div>
            </div>
          </div>

          {/* Flagship Section: Interactive 20-AA 3D-Pocket DMS Heatmap */}
          <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <h2 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <Flame className="w-4 h-4 text-rose-500" />
                  3D-Pocket Zero-Shot Deep Mutational Scanning (DMS) Landscape
                </h2>
                <p className="text-xs text-slate-500">
                  All {activeVariant.pocket_dms.rows.length} spatial pocket positions (&le;5.0 Å in AlphaFold 3D) × 20 canonical amino acids computed in a single batched ESM2 masked pass. Click any cell to simulate it.
                </p>
              </div>
              <span className="font-mono text-xs text-slate-500">
                Latency: {activeVariant.latency_ms} ms
              </span>
            </div>

            <PocketDMSHeatmap
              aminoAcids={activeVariant.pocket_dms.amino_acids}
              rows={activeVariant.pocket_dms.rows}
              selectedPosition={activeVariant.position}
              selectedMutAA={activeVariant.mut_aa}
              onSelectCell={(pos, aa) => runSimulation({ position: pos, mut_aa: aa })}
            />

            {/* Stabilizing/Tolerated vs. Fragile Insights */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
              <div className="p-3.5 rounded-xl bg-emerald-50/60 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800">
                <div className="text-xs font-bold text-emerald-800 dark:text-emerald-300 flex items-center gap-1.5 mb-2">
                  <Sparkles className="w-3.5 h-3.5" /> Top Tolerated / Candidate Stabilizing Substitutions in Pocket
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {activeVariant.pocket_dms.rescue_or_tolerated_candidates.length > 0 ? (
                    activeVariant.pocket_dms.rescue_or_tolerated_candidates.map((c) => (
                      <button
                        key={c.mutation}
                        onClick={() => runSimulation({ position: c.position, mut_aa: c.alt_aa })}
                        className="font-mono text-[11px] px-2 py-1 rounded-md bg-white dark:bg-slate-900 border border-emerald-300 dark:border-emerald-700 text-emerald-800 dark:text-emerald-300 hover:bg-emerald-100"
                      >
                        {c.mutation} (LLR {c.llr > 0 ? `+${c.llr.toFixed(2)}` : c.llr.toFixed(2)})
                      </button>
                    ))
                  ) : (
                    <span className="text-xs text-slate-500">
                      Pocket is strictly conserved; no high-LLR stabilizing substitutions found.
                    </span>
                  )}
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-rose-50/60 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-800">
                <div className="text-xs font-bold text-rose-800 dark:text-rose-300 flex items-center gap-1.5 mb-2">
                  <ShieldAlert className="w-3.5 h-3.5" /> Most Fragile / Pathogenic Pocket Hotspots
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {activeVariant.pocket_dms.most_fragile_pocket_mutations.map((f) => (
                    <span
                      key={f.mutation}
                      className="font-mono text-[11px] px-2 py-1 rounded-md bg-white dark:bg-slate-900 border border-rose-300 dark:border-rose-700 text-rose-800 dark:text-rose-300"
                    >
                      {f.mutation} (LLR {f.llr.toFixed(2)})
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* 3D Pocket Viewer + Differential GO Loss/Gain */}
          <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
            <div className="xl:col-span-6">
              <ProteinViewer3D
                pdbContent={activeVariant.pdb_content}
                alphafoldId={`AF-${activeVariant.uniprot_id || "MODEL"}-F1`}
                targetPosition={activeVariant.position}
                pocketPositions={activeVariant.structural_pocket.pocket_positions}
                height={420}
              />
            </div>

            <div className="xl:col-span-6 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 space-y-4">
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                Hierarchical Gene Ontology Shift (ΔGO_IA · True-Path Verified)
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <div className="text-xs font-bold text-rose-600 dark:text-rose-400 mb-2">
                    Attenuated / Disrupted Functions
                  </div>
                  <div className="space-y-1.5 max-h-80 overflow-y-auto">
                    {activeVariant.go_disruption.lost_functions.length > 0 ? (
                      activeVariant.go_disruption.lost_functions.map((item) => (
                        <div
                          key={item.term}
                          className="p-2 rounded-lg bg-rose-50/50 dark:bg-rose-950/30 border border-rose-200/70 dark:border-rose-900 text-xs"
                        >
                          <div className="font-semibold text-slate-900 dark:text-white truncate">
                            {item.name}
                          </div>
                          <div className="font-mono text-[11px] text-rose-700 dark:text-rose-300 flex justify-between mt-0.5">
                            <span>{item.term} ({item.aspect})</span>
                            <span>{(item.delta * 100).toFixed(2)}%</span>
                          </div>
                        </div>
                      ))
                    ) : (
                      <p className="text-xs text-slate-500">Minimal GO probability attenuation detected.</p>
                    )}
                  </div>
                </div>
                <div>
                  <div className="text-xs font-bold text-emerald-600 dark:text-emerald-400 mb-2">
                    Elevated / Shifted Functions
                  </div>
                  <div className="space-y-1.5 max-h-80 overflow-y-auto">
                    {activeVariant.go_disruption.gained_functions.length > 0 ? (
                      activeVariant.go_disruption.gained_functions.map((item) => (
                        <div
                          key={item.term}
                          className="p-2 rounded-lg bg-emerald-50/50 dark:bg-emerald-950/30 border border-emerald-200/70 dark:border-emerald-900 text-xs"
                        >
                          <div className="font-semibold text-slate-900 dark:text-white truncate">
                            {item.name}
                          </div>
                          <div className="font-mono text-[11px] text-emerald-700 dark:text-emerald-300 flex justify-between mt-0.5">
                            <span>{item.term} ({item.aspect})</span>
                            <span>+{(item.delta * 100).toFixed(2)}%</span>
                          </div>
                        </div>
                      ))
                    ) : (
                      <p className="text-xs text-slate-500">No elevated GO terms detected.</p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Grounded XAI Co-Pilot */}
          <CopilotPanel
            evidencePacket={{
              protein_name: activeVariant.protein_name,
              uniprot_id: activeVariant.uniprot_id,
              sequence_length: activeVariant.wt_summary.sequence_length,
              variant: {
                mutation: activeVariant.mutation,
                position: activeVariant.position,
                wt_aa: activeVariant.wt_aa,
                mut_aa: activeVariant.mut_aa,
                dual_axis_assessment: activeVariant.dual_axis_assessment,
                structural_pocket: {
                  target_plddt: activeVariant.structural_pocket.target_plddt,
                  structural_region: activeVariant.structural_pocket.structural_region,
                  all_5A_contact_count: activeVariant.structural_pocket.all_5A_contact_count,
                  burial_contacts_8A: activeVariant.structural_pocket.burial_contacts_8A,
                },
              },
              clinvar: activeVariant.bio_evidence?.clinvar || {},
              drugs: activeVariant.bio_evidence?.open_targets?.drugs || [],
              dag_audit: { violations_before: 0, violations_after: 0, terms_repaired: 0 },
            }}
          />
        </>
      )}
    </div>
  );
}

export default function VariantsPage() {
  return (
    <Suspense fallback={<div className="p-10 text-sm text-slate-500">Loading Variant Studio...</div>}>
      <VariantsWorkspaceInner />
    </Suspense>
  );
}
