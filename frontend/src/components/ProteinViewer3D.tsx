"use client";

import React, { useEffect, useRef, useState } from "react";
import { Crosshair, Eye, Layers, RotateCw, Sparkles } from "lucide-react";

declare global {
  interface Window {
    $3Dmol?: any;
  }
}

interface ProteinViewer3DProps {
  pdbContent: string | null;
  alphafoldId?: string | null;
  hotspotIndices?: number[];
  targetPosition?: number | null;
  pocketPositions?: number[];
  height?: number;
}

export function ProteinViewer3D({
  pdbContent,
  alphafoldId,
  hotspotIndices = [],
  targetPosition = null,
  pocketPositions = [],
  height = 460,
}: ProteinViewer3DProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const viewerRef = useRef<any>(null);
  const [scriptLoaded, setScriptLoaded] = useState(false);
  const [styleMode, setStyleMode] = useState<"cartoon" | "surface" | "stick">("cartoon");
  const [colorMode, setColorMode] = useState<"plddt" | "spectrum" | "ss">("plddt");
  const [showHotspots, setShowHotspots] = useState(true);
  const [showPocket, setShowPocket] = useState(true);
  const [spinning, setSpinning] = useState(false);

  // Load 3Dmol.js script dynamically once
  useEffect(() => {
    if (typeof window === "undefined") return;
    if (window.$3Dmol) {
      setScriptLoaded(true);
      return;
    }
    const existing = document.getElementById("script-3dmol");
    if (existing) {
      existing.addEventListener("load", () => setScriptLoaded(true));
      return;
    }
    const script = document.createElement("script");
    script.id = "script-3dmol";
    script.src = "https://cdnjs.cloudflare.com/ajax/libs/3Dmol/2.0.4/3Dmol-min.js";
    script.async = true;
    script.onload = () => setScriptLoaded(true);
    document.head.appendChild(script);
  }, []);

  useEffect(() => {
    if (!scriptLoaded || !pdbContent || !containerRef.current || !window.$3Dmol) return;

    const el = containerRef.current;
    el.innerHTML = "";
    const viewer = window.$3Dmol.createViewer(el, { backgroundColor: "#0b1120" });
    viewerRef.current = viewer;

    viewer.addModel(pdbContent, "pdb");

    // Color function for AlphaFold pLDDT (stored in PDB B-factor column)
    const plddtColorFunc = (atom: any) => {
      const b = atom.b ?? 70;
      if (b >= 90) return "#1d4ed8"; // Very high
      if (b >= 70) return "#38bdf8"; // Confident
      if (b >= 50) return "#facc15"; // Low
      return "#f97316"; // Very low / disordered
    };

    const baseStyle: Record<string, any> = {};
    if (colorMode === "plddt") {
      baseStyle.colorfunc = plddtColorFunc;
    } else if (colorMode === "ss") {
      baseStyle.colorscheme = "ssPyMOL";
    } else {
      baseStyle.color = "spectrum";
    }

    if (styleMode === "cartoon") {
      viewer.setStyle({}, { cartoon: baseStyle });
    } else if (styleMode === "stick") {
      viewer.setStyle({}, { stick: { ...baseStyle, radius: 0.16 } });
    } else {
      viewer.setStyle({}, { cartoon: { ...baseStyle, opacity: 0.85 } });
      viewer.addSurface(window.$3Dmol.SurfaceType.VDW, {
        opacity: 0.55,
        color: "#38bdf8",
      });
    }

    // Highlight XAI Attention Hotspots
    if (showHotspots && hotspotIndices.length > 0 && !targetPosition) {
      viewer.addStyle(
        { resi: hotspotIndices },
        { stick: { color: "#f59e0b", radius: 0.22 }, cartoon: { color: "#ef4444" } }
      );
    }

    // Highlight 5 A Structural Pocket & Target Mutated Residue
    if (showPocket && targetPosition) {
      const neighbors = pocketPositions.filter((p) => p !== targetPosition);
      if (neighbors.length > 0) {
        viewer.addStyle(
          { resi: neighbors },
          { stick: { color: "#fbbf24", radius: 0.22 } }
        );
      }
      viewer.addStyle(
        { resi: [targetPosition] },
        {
          sphere: { color: "#f43f5e", radius: 1.15 },
          stick: { color: "#f43f5e", radius: 0.3 },
        }
      );
      viewer.addLabel(`Site ${targetPosition}`, {
        position: { resi: targetPosition, atom: "CA" },
        backgroundColor: "#be123c",
        fontColor: "#ffffff",
        fontSize: 12,
        backgroundOpacity: 0.88,
      });
    }

    viewer.zoomTo();
    if (spinning) viewer.spin("y", 0.5);
    viewer.render();

    return () => {
      try {
        viewer.clear();
      } catch {
        // ignore cleanup errors
      }
    };
  }, [scriptLoaded, pdbContent, styleMode, colorMode, showHotspots, showPocket, targetPosition, pocketPositions, hotspotIndices, spinning]);

  const zoomToPocket = () => {
    if (!viewerRef.current || !targetPosition) return;
    const focusRes = pocketPositions.length > 0 ? pocketPositions : [targetPosition];
    viewerRef.current.zoomTo({ resi: focusRes }, 450);
    viewerRef.current.render();
  };

  const resetZoom = () => {
    if (!viewerRef.current) return;
    viewerRef.current.zoomTo({}, 400);
    viewerRef.current.render();
  };

  if (!pdbContent) {
    return (
      <div
        style={{ height }}
        className="rounded-xl border border-dashed border-slate-300 dark:border-slate-700 bg-slate-100/70 dark:bg-slate-900/50 flex flex-col items-center justify-center text-center p-6"
      >
        <Layers className="w-8 h-8 text-slate-400 mb-2" />
        <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">
          No AlphaFold 3D Structure Loaded
        </p>
        <p className="text-xs text-slate-500 mt-1 max-w-sm">
          Provide a UniProt ID (e.g. P04637, P68871, P01308) to resolve atomic coordinates and 5 Å pocket geometry.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden bg-slate-950 shadow-sm">
      {/* Toolbar */}
      <div className="px-3 py-2 bg-slate-900 border-b border-slate-800 flex flex-wrap items-center justify-between gap-2 text-xs text-slate-200">
        <div className="flex items-center gap-2">
          <span className="font-mono font-semibold text-cyan-400">
            {alphafoldId || "AlphaFold 3D"}
          </span>
          <div className="flex items-center rounded-md bg-slate-800 p-0.5">
            {(["cartoon", "stick", "surface"] as const).map((m) => (
              <button
                key={m}
                onClick={() => setStyleMode(m)}
                className={`px-2 py-0.5 rounded capitalize ${
                  styleMode === m ? "bg-blue-600 text-white" : "text-slate-300 hover:text-white"
                }`}
              >
                {m}
              </button>
            ))}
          </div>
          <div className="flex items-center rounded-md bg-slate-800 p-0.5">
            {(
              [
                ["plddt", "pLDDT"],
                ["spectrum", "Rainbow"],
                ["ss", "Helix/Sheet"],
              ] as const
            ).map(([k, lbl]) => (
              <button
                key={k}
                onClick={() => setColorMode(k)}
                className={`px-2 py-0.5 rounded ${
                  colorMode === k ? "bg-cyan-600 text-white" : "text-slate-300 hover:text-white"
                }`}
              >
                {lbl}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-1.5">
          {targetPosition ? (
            <>
              <button
                onClick={() => setShowPocket((v) => !v)}
                className={`inline-flex items-center gap-1 px-2 py-1 rounded border text-[11px] ${
                  showPocket
                    ? "bg-rose-950/70 border-rose-500/60 text-rose-200"
                    : "bg-slate-800 border-slate-700 text-slate-400"
                }`}
              >
                <Eye className="w-3 h-3" /> 5 Å Pocket
              </button>
              <button
                onClick={zoomToPocket}
                className="inline-flex items-center gap-1 px-2 py-1 rounded bg-blue-600 hover:bg-blue-500 text-white text-[11px]"
              >
                <Crosshair className="w-3 h-3" /> Focus Site {targetPosition}
              </button>
            </>
          ) : (
            <button
              onClick={() => setShowHotspots((v) => !v)}
              className={`inline-flex items-center gap-1 px-2 py-1 rounded border text-[11px] ${
                showHotspots
                  ? "bg-amber-950/70 border-amber-500/60 text-amber-200"
                  : "bg-slate-800 border-slate-700 text-slate-400"
              }`}
            >
              <Sparkles className="w-3 h-3" /> XAI Hotspots ({hotspotIndices.length})
            </button>
          )}
          <button
            onClick={() => setSpinning((s) => !s)}
            className={`p-1 rounded border ${
              spinning
                ? "bg-cyan-900/60 border-cyan-500 text-cyan-200"
                : "bg-slate-800 border-slate-700 text-slate-300"
            }`}
            title="Toggle Auto-Rotate"
          >
            <RotateCw className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={resetZoom}
            className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 border border-slate-700 text-[11px]"
          >
            Reset
          </button>
        </div>
      </div>

      {/* 3Dmol WebGL Canvas */}
      <div ref={containerRef} style={{ width: "100%", height, position: "relative" }} />

      {/* AlphaFold pLDDT Legend */}
      <div className="px-3 py-1.5 bg-slate-900 border-t border-slate-800 flex flex-wrap items-center justify-between gap-2 text-[11px] text-slate-400">
        <div className="flex items-center gap-3">
          <span className="inline-flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-sm bg-[#1d4ed8]" /> pLDDT ≥ 90 (Very High)
          </span>
          <span className="inline-flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-sm bg-[#38bdf8]" /> 70–90 (Confident)
          </span>
          <span className="inline-flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-sm bg-[#facc15]" /> 50–70 (Low)
          </span>
          <span className="inline-flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-sm bg-[#f97316]" /> &lt; 50 (Disordered)
          </span>
        </div>
        <span>Drag to rotate · Scroll to zoom</span>
      </div>
    </div>
  );
}
