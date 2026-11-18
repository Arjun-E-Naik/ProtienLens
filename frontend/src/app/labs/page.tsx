"use client";

import React, { useState } from "react";
import Link from "next/link";
import { ArrowRight, BookOpen, CheckCircle2, Clock, GraduationCap, Printer } from "lucide-react";
import { useWorkspace } from "@/context/WorkspaceContext";

export default function LabsPage() {
  const { teachingLabs, institution } = useWorkspace();
  const [studentName, setStudentName] = useState("");
  const [rollNumber, setRollNumber] = useState("");
  const [selectedLabId, setSelectedLabId] = useState<string | null>(null);

  const selectedLab = teachingLabs.find((l) => l.lab_id === selectedLabId) || teachingLabs[0];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4 no-print">
        <div>
          <div className="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-700 dark:text-emerald-400">
            <GraduationCap className="w-4 h-4" />
            <span>Institutional EdTech &amp; University Lab Edition</span>
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white mt-0.5">
            College Teaching Lab Pack — {institution.institution_name}
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Ready-to-assign interactive computational biology &amp; bio-ML lab modules for B.Tech, M.Sc, Biotech, and MBBS cohorts.
          </p>
        </div>

        <button
          onClick={() => window.print()}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-900 dark:bg-blue-600 text-white text-xs font-semibold hover:opacity-90"
        >
          <Printer className="w-4 h-4" /> Print White-Label Lab Sheet / PDF
        </button>
      </div>

      {/* Student Identification Strip for Printable Lab Submissions */}
      <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 grid grid-cols-1 md:grid-cols-3 gap-3">
        <div>
          <label className="block text-[11px] font-semibold text-slate-500 mb-1">
            Institution (White-Label Header)
          </label>
          <div className="text-xs font-bold text-slate-900 dark:text-white py-1.5">
            {institution.institution_name}
          </div>
        </div>
        <div>
          <label className="block text-[11px] font-semibold text-slate-500 mb-1">
            Student / Researcher Name
          </label>
          <input
            type="text"
            value={studentName}
            onChange={(e) => setStudentName(e.target.value)}
            placeholder="Enter your name for PDF submission"
            className="w-full px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 text-xs"
          />
        </div>
        <div>
          <label className="block text-[11px] font-semibold text-slate-500 mb-1">
            Enrollment / Roll Number
          </label>
          <input
            type="text"
            value={rollNumber}
            onChange={(e) => setRollNumber(e.target.value)}
            placeholder="e.g., BT23CSE001"
            className="w-full px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 font-mono text-xs"
          />
        </div>
      </div>

      {/* 4 Interactive Lab Modules Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {teachingLabs.map((lab) => {
          const isSelected = selectedLab?.lab_id === lab.lab_id;
          return (
            <div
              key={lab.lab_id}
              onClick={() => setSelectedLabId(lab.lab_id)}
              className={`cursor-pointer rounded-2xl border p-5 transition-all bg-white dark:bg-slate-900 space-y-3 ${
                isSelected
                  ? "border-blue-500 ring-2 ring-blue-500/20"
                  : "border-slate-200 dark:border-slate-800 hover:border-blue-300"
              }`}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="font-mono text-xs font-bold px-2.5 py-0.5 rounded bg-blue-50 text-blue-700 dark:bg-blue-950 dark:text-cyan-300">
                  {lab.code}
                </span>
                <div className="flex items-center gap-2 text-[11px] text-slate-500">
                  <span className="inline-flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5" /> {lab.duration_min} min
                  </span>
                  <span className="px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 font-semibold">
                    {lab.difficulty}
                  </span>
                </div>
              </div>

              <h2 className="text-base font-bold text-slate-900 dark:text-white leading-snug">
                {lab.title}
              </h2>

              <div className="flex flex-wrap gap-1.5">
                {lab.target_courses.map((c) => (
                  <span
                    key={c}
                    className="text-[10px] px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 font-medium"
                  >
                    {c}
                  </span>
                ))}
              </div>

              <div className="space-y-1.5 pt-1">
                <div className="text-[11px] font-bold text-slate-600 dark:text-slate-300 uppercase">
                  Learning Objectives
                </div>
                {lab.objectives.map((obj, idx) => (
                  <div key={idx} className="flex items-start gap-2 text-xs text-slate-600 dark:text-slate-300">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0 mt-0.5" />
                    <span>{obj}</span>
                  </div>
                ))}
              </div>

              <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 space-y-1">
                <div className="text-[11px] font-bold text-slate-700 dark:text-slate-200 flex items-center gap-1.5">
                  <BookOpen className="w-3.5 h-3.5 text-blue-600" /> Guided Viva / Assessment Prompts
                </div>
                {lab.viva_questions.map((q, idx) => (
                  <p key={idx} className="text-xs text-slate-600 dark:text-slate-300">
                    {idx + 1}. {q}
                  </p>
                ))}
              </div>

              <div className="pt-1 flex items-center justify-between no-print">
                <span className="font-mono text-[11px] text-slate-500">
                  Target: {lab.gene_symbol} ({lab.uniprot_id}) · pos {lab.position}&rarr;{lab.mut_aa}
                </span>
                <Link
                  href={
                    lab.lab_id === "lab-4-dag-arena"
                      ? "/arena"
                      : `/variants?preset=${
                          lab.lab_id === "lab-1-oncology-dms"
                            ? "tp53-r273h"
                            : lab.lab_id === "lab-2-sickle-cell"
                            ? "hbb-e7v"
                            : "ins-c96y"
                        }`
                  }
                  className="inline-flex items-center gap-1 text-xs font-bold text-blue-600 dark:text-cyan-400 hover:underline"
                >
                  Launch Live Lab <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
