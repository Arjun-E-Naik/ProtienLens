"use client";

import React, { useMemo, useState } from "react";
import {
  Background,
  Controls,
  Edge,
  MarkerType,
  MiniMap,
  Node,
  ReactFlow,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import dagre from "dagre";
import type { DAGNodePayload, ReactFlowDAGPayload } from "@/lib/types";

interface InteractiveDAGProps {
  dag: ReactFlowDAGPayload;
}

const NODE_WIDTH = 220;
const NODE_HEIGHT = 76;

function layoutDAG(dag: ReactFlowDAGPayload): { nodes: Node[]; edges: Edge[] } {
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: "TB", nodesep: 38, ranksep: 65 });

  dag.nodes.forEach((n) => {
    g.setNode(n.id, { width: NODE_WIDTH, height: NODE_HEIGHT });
  });
  dag.edges.forEach((e) => {
    g.setEdge(e.source, e.target);
  });

  dagre.layout(g);

  const aspectPalette: Record<string, { bg: string; border: string; text: string }> = {
    MF: { bg: "#f5f3ff", border: "#7c3aed", text: "#4c1d95" },
    BP: { bg: "#f0f9ff", border: "#0284c7", text: "#0c4a6e" },
    CC: { bg: "#f0fdf4", border: "#16a34a", text: "#14532d" },
  };
  const pal = aspectPalette[dag.aspect] || aspectPalette.MF;

  const nodes: Node[] = dag.nodes.map((n) => {
    const pos = g.node(n.id);
    const shortName = n.label.length > 28 ? `${n.label.slice(0, 26)}...` : n.label;
    return {
      id: n.id,
      position: {
        x: (pos?.x ?? 0) - NODE_WIDTH / 2,
        y: (pos?.y ?? 0) - NODE_HEIGHT / 2,
      },
      data: {
        payload: n,
        label: (
          <div className="text-left leading-tight">
            <div className="font-semibold text-[11px] truncate">{shortName}</div>
            <div className="font-mono text-[10px] opacity-75 mt-0.5">
              {n.id} · IA {n.ia_weight.toFixed(2)}
            </div>
            <div className="font-mono text-[10px] font-bold mt-1">
              {n.repaired
                ? `${(n.raw_score * 100).toFixed(1)}% → ${(n.propagated_score * 100).toFixed(1)}% (+${(n.repair_delta * 100).toFixed(1)}%)`
                : `Confidence: ${(n.propagated_score * 100).toFixed(1)}%`}
            </div>
          </div>
        ),
      },
      style: {
        width: NODE_WIDTH,
        padding: "8px 10px",
        borderRadius: 10,
        backgroundColor: n.repaired ? "#fef3c7" : pal.bg,
        border: n.repaired ? "2px solid #d97706" : `1.5px solid ${pal.border}`,
        color: n.repaired ? "#78350f" : pal.text,
        boxShadow: n.repaired
          ? "0 4px 12px rgba(217, 119, 6, 0.22)"
          : "0 2px 6px rgba(15, 23, 42, 0.06)",
      },
    };
  });

  const edges: Edge[] = dag.edges.map((e) => ({
    id: e.id,
    source: e.source,
    target: e.target,
    animated: e.repaired_flow,
    style: {
      stroke: e.repaired_flow ? "#d97706" : "#64748b",
      strokeWidth: e.repaired_flow ? 2.4 : 1.4,
    },
    markerEnd: {
      type: MarkerType.ArrowClosed,
      color: e.repaired_flow ? "#d97706" : "#64748b",
    },
  }));

  return { nodes, edges };
}

export function InteractiveDAG({ dag }: InteractiveDAGProps) {
  const { nodes, edges } = useMemo(() => layoutDAG(dag), [dag]);
  const [selectedNode, setSelectedNode] = useState<DAGNodePayload | null>(
    dag.nodes.find((n) => n.repaired) || dag.nodes[0] || null
  );

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
      <div className="lg:col-span-2 h-[540px] rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 overflow-hidden">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          fitView
          onNodeClick={(_, node) => {
            const p = (node.data as any)?.payload as DAGNodePayload | undefined;
            if (p) setSelectedNode(p);
          }}
        >
          <Background gap={18} size={1} />
          <Controls />
          <MiniMap pannable zoomable />
        </ReactFlow>
      </div>

      {/* Node Inspector Drawer */}
      <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 flex flex-col justify-between">
        {selectedNode ? (
          <div className="space-y-4">
            <div>
              <div className="flex items-center justify-between gap-2">
                <span className="font-mono text-xs px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200">
                  {selectedNode.id}
                </span>
                {selectedNode.repaired ? (
                  <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 dark:bg-amber-900/50 dark:text-amber-200">
                    True-Path Repaired
                  </span>
                ) : (
                  <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-200">
                    Monotonic
                  </span>
                )}
              </div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white mt-2">
                {selectedNode.label}
              </h3>
            </div>

            <div className="grid grid-cols-2 gap-2.5">
              <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/70 border border-slate-200 dark:border-slate-700">
                <div className="text-[11px] text-slate-500">Raw Ensemble</div>
                <div className="font-mono text-lg font-bold tabular-nums">
                  {(selectedNode.raw_score * 100).toFixed(1)}%
                </div>
              </div>
              <div className="p-2.5 rounded-lg bg-blue-50 dark:bg-blue-950/50 border border-blue-200 dark:border-blue-800">
                <div className="text-[11px] text-blue-700 dark:text-blue-300">True-Path Final</div>
                <div className="font-mono text-lg font-bold text-blue-700 dark:text-blue-300 tabular-nums">
                  {(selectedNode.propagated_score * 100).toFixed(1)}%
                </div>
              </div>
            </div>

            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 text-xs space-y-1.5">
              <div className="flex justify-between">
                <span className="text-slate-500">Sub-Ontology Aspect</span>
                <span className="font-mono font-semibold">{selectedNode.aspect}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Information Accretion (IA)</span>
                <span className="font-mono font-semibold">{selectedNode.ia_weight.toFixed(3)} bits</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Propagation Elevation</span>
                <span className="font-mono font-semibold text-amber-600 dark:text-amber-400">
                  +{(selectedNode.repair_delta * 100).toFixed(2)}%
                </span>
              </div>
            </div>

            <div>
              <div className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Gene Ontology Definition
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                {selectedNode.definition}
              </p>
            </div>
          </div>
        ) : (
          <p className="text-sm text-slate-500">Click any GO node in the graph to inspect details.</p>
        )}

        <div className="pt-3 mt-4 border-t border-slate-200 dark:border-slate-800 text-[11px] text-slate-500">
          Amber nodes and animated edges show ancestral probabilities elevated by fixed-point True Path propagation so{" "}
          <span className="font-mono">Score(Parent) &ge; Score(Child)</span> holds globally.
        </div>
      </div>
    </div>
  );
}
