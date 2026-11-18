"use client";

import React, { useState } from "react";
import type { PocketDMSRow } from "@/lib/types";

interface PocketDMSHeatmapProps {
  aminoAcids: string[];
  rows: PocketDMSRow[];
  selectedPosition: number;
  selectedMutAA: string;
  onSelectCell?: (position: number, aa: string) => void;
}

function getLLRCellStyle(llr: number, isWT: boolean): { bg: string; text: string } {
  if (isWT) {
    return { bg: "#1e293b", text: "#f8fafc" };
  }
  if (llr <= -5.5) return { bg: "#991b1b", text: "#ffffff" };
  if (llr <= -4.0) return { bg: "#dc2626", text: "#ffffff" };
  if (llr <= -2.5) return { bg: "#f87171", text: "#450a0a" };
  if (llr <= -1.2) return { bg: "#fecaca", text: "#7f1d1d" };
  if (llr < 0.15) return { bg: "#f1f5f9", text: "#334155" };
  if (llr < 1.0) return { bg: "#bbf7d0", text: "#14532d" };
  return { bg: "#16a34a", text: "#ffffff" };
}

export function PocketDMSHeatmap({
  aminoAcids,
  rows,
  selectedPosition,
  selectedMutAA,
  onSelectCell,
}: PocketDMSHeatmapProps) {
  const [hovered, setHovered] = useState<{
    pos: number;
    wt: string;
    mut: string;
    llr: number;
    dist: number | null;
    plddt: number | null;
  } | null>(null);

  if (!rows.length) {
    return (
      <div className="p-6 text-center text-sm text-slate-500 border border-dashed rounded-xl">
        Run a variant simulation to generate the 3D-Pocket Zero-Shot Deep Mutational Scan.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Live Hover Readout Bar */}
      <div className="flex flex-wrap items-center justify-between gap-2 px-3 py-2 rounded-lg bg-slate-100 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 text-xs">
        {hovered ? (
          <div className="flex flex-wrap items-center gap-4 font-mono">
            <span className="font-bold text-slate-900 dark:text-white">
              {hovered.wt}
              {hovered.pos}
              {hovered.mut}
            </span>
            <span>
              ESM2 LLR:{" "}
              <strong
                className={
                  hovered.llr <= -3
                    ? "text-rose-600 dark:text-rose-400"
                    : hovered.llr >= 0
                    ? "text-emerald-600 dark:text-emerald-400"
                    : "text-slate-700 dark:text-slate-200"
                }
              >
                {hovered.llr.toFixed(2)}
              </strong>
            </span>
            {hovered.dist !== null && <span>3D Dist: {hovered.dist.toFixed(2)} Å</span>}
            {hovered.plddt !== null && <span>pLDDT: {hovered.plddt.toFixed(1)}</span>}
          </div>
        ) : (
          <span className="text-slate-600 dark:text-slate-300">
            Hover any cell to inspect evolutionary LLR · Click a cell to test that substitution
          </span>
        )}

        <div className="flex items-center gap-2 text-[11px]">
          <span className="inline-flex items-center gap-1">
            <span className="w-3 h-3 rounded bg-[#991b1b]" /> Damaging (&le; -4)
          </span>
          <span className="inline-flex items-center gap-1">
            <span className="w-3 h-3 rounded bg-[#f1f5f9] border border-slate-300" /> Neutral (~0)
          </span>
          <span className="inline-flex items-center gap-1">
            <span className="w-3 h-3 rounded bg-[#16a34a]" /> Tolerated / Stabilizing (&gt; 0)
          </span>
        </div>
      </div>

      {/* Heatmap Matrix Table */}
      <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
        <table className="w-full border-collapse text-xs">
          <thead>
            <tr className="border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/60">
              <th className="py-2 px-3 text-left font-semibold text-slate-700 dark:text-slate-200 sticky left-0 bg-slate-50 dark:bg-slate-800 z-10 min-w-[140px]">
                3D Pocket Site
              </th>
              <th className="py-2 px-2 text-center font-mono text-[11px] text-slate-500">Dist</th>
              <th className="py-2 px-2 text-center font-mono text-[11px] text-slate-500">Cons.</th>
              {aminoAcids.map((aa) => (
                <th
                  key={aa}
                  className="py-2 px-1 text-center font-mono font-bold text-slate-700 dark:text-slate-200 min-w-[30px]"
                >
                  {aa}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr
                key={row.position}
                className={`border-b border-slate-100 dark:border-slate-800/70 ${
                  row.is_target ? "bg-blue-50/40 dark:bg-blue-950/20" : ""
                }`}
              >
                <td className="py-1.5 px-3 font-mono whitespace-nowrap sticky left-0 bg-white dark:bg-slate-900 z-10 border-r border-slate-100 dark:border-slate-800">
                  <span className="font-bold text-slate-900 dark:text-white">
                    {row.wt_aa}
                    {row.position}
                  </span>
                  {row.is_target && (
                    <span className="ml-1.5 px-1.5 py-0.5 text-[10px] rounded bg-rose-100 text-rose-700 dark:bg-rose-900/50 dark:text-rose-300 font-sans font-semibold">
                      Target
                    </span>
                  )}
                </td>
                <td className="py-1.5 px-2 text-center font-mono text-[11px] text-slate-500 tabular-nums">
                  {row.is_target
                    ? "0.0 Å"
                    : row.distance_angstrom !== null
                    ? `${row.distance_angstrom.toFixed(1)} Å`
                    : "—"}
                </td>
                <td className="py-1.5 px-2 text-center font-mono text-[11px] text-slate-600 dark:text-slate-300 tabular-nums">
                  {(row.conservation * 100).toFixed(0)}%
                </td>
                {aminoAcids.map((aa) => {
                  const isWT = aa === row.wt_aa;
                  const llr = row.scores[aa] ?? 0;
                  const { bg, text } = getLLRCellStyle(llr, isWT);
                  const isSelected =
                    row.position === selectedPosition && aa === selectedMutAA;
                  return (
                    <td key={aa} className="p-0.5 text-center">
                      <button
                        type="button"
                        onClick={() => onSelectCell?.(row.position, aa)}
                        onMouseEnter={() =>
                          setHovered({
                            pos: row.position,
                            wt: row.wt_aa,
                            mut: aa,
                            llr,
                            dist: row.distance_angstrom,
                            plddt: row.plddt,
                          })
                        }
                        onMouseLeave={() => setHovered(null)}
                        style={{ backgroundColor: bg, color: text }}
                        className={`w-full h-7 rounded font-mono text-[10px] font-semibold tabular-nums transition-transform hover:scale-110 ${
                          isSelected ? "ring-2 ring-blue-600 ring-offset-1 z-10 relative" : ""
                        }`}
                      >
                        {isWT ? "WT" : llr.toFixed(1)}
                      </button>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
