"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  BarChart3,
  BookOpen,
  Box,
  Cpu,
  Dna,
  FileSpreadsheet,
  FolderKanban,
  GitBranch,
  Moon,
  Settings,
  ShieldCheck,
  Sun,
} from "lucide-react";
import { useWorkspace } from "@/context/WorkspaceContext";

const NAV_ITEMS = [
  { href: "/", label: "Workspace Overview", icon: Activity },
  { href: "/studio", label: "3D Structure & Function", icon: Box },
  { href: "/variants", label: "Variant & 3D Pocket DMS", icon: Dna },
  { href: "/dag", label: "True Path DAG Explorer", icon: GitBranch },
  { href: "/batch", label: "Batch Cohort Triage", icon: FileSpreadsheet },
  { href: "/arena", label: "Model Arena & Benchmarks", icon: BarChart3 },
  { href: "/labs", label: "College Teaching Labs", icon: BookOpen },
  { href: "/cases", label: "Saved Cases & Dossiers", icon: FolderKanban },
  { href: "/settings", label: "AI Keys & Institution", icon: Settings },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { darkMode, toggleDarkMode, institution, aiStatus, backendOnline } = useWorkspace();

  const providerBadge = (() => {
    if (!backendOnline) {
      return {
        label: "Backend Offline",
        dot: "bg-rose-500",
        cls: "bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950/50 dark:text-rose-300 dark:border-rose-800",
      };
    }
    if (aiStatus?.is_llm_connected) {
      const name =
        aiStatus.active_provider === "gemini"
          ? "Gemini Live"
          : aiStatus.active_provider === "grok"
          ? "xAI Grok Live"
          : aiStatus.active_provider === "groq"
          ? "Groq Live"
          : "Ollama Local";
      return {
        label: `${name} · ${aiStatus.model_name}`,
        dot: "bg-emerald-500",
        cls: "bg-emerald-50 text-emerald-800 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800",
      };
    }
    return {
      label: "Local Evidence XAI (Add Gemini/Grok Key)",
      dot: "bg-amber-500",
      cls: "bg-amber-50 text-amber-800 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-800",
    };
  })();

  return (
    <div className="min-h-screen flex bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      {/* Persistent Left Clinical Sidebar */}
      <aside className="no-print w-64 shrink-0 border-r border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900 flex flex-col justify-between sticky top-0 h-screen">
        <div>
          {/* Brand Logo */}
          <div className="px-5 py-4 border-b border-slate-200 dark:border-slate-800 flex items-center gap-3">
            <svg width="34" height="34" viewBox="0 0 40 40" fill="none" aria-label="ProteinLens-OS Logo">
              <defs>
                <linearGradient id="plosGrad" x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse">
                  <stop offset="0%" stopColor="#2563eb" />
                  <stop offset="55%" stopColor="#06b6d4" />
                  <stop offset="100%" stopColor="#10b981" />
                </linearGradient>
              </defs>
              <rect width="40" height="40" rx="10" fill="url(#plosGrad)" />
              <path d="M13 10C19 15 21 25 27 30" stroke="#ffffff" strokeWidth="2.5" strokeLinecap="round" />
              <path d="M27 10C21 15 19 25 13 30" stroke="#e0f2fe" strokeWidth="2.5" strokeLinecap="round" />
              <line x1="15.5" y1="14" x2="24.5" y2="14" stroke="#ffffff" strokeWidth="1.8" strokeLinecap="round" />
              <line x1="17" y1="20" x2="23" y2="20" stroke="#ffffff" strokeWidth="1.8" strokeLinecap="round" />
              <line x1="15.5" y1="26" x2="24.5" y2="26" stroke="#ffffff" strokeWidth="1.8" strokeLinecap="round" />
            </svg>
            <div className="min-w-0">
              <div className="font-bold text-base tracking-tight leading-tight text-slate-900 dark:text-white">
                ProteinLens-OS
              </div>
              <div className="text-[11px] font-medium text-blue-600 dark:text-cyan-400 truncate">
                Clinical &amp; 3D DMS BioStudio
              </div>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="p-3 space-y-1">
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              const active = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    active
                      ? "bg-blue-50 text-blue-700 border border-blue-200/80 dark:bg-blue-950/60 dark:text-blue-300 dark:border-blue-800/70"
                      : "text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-100"
                  }`}
                >
                  <Icon className="w-4 h-4 shrink-0" />
                  <span className="truncate">{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Institutional Footer Card */}
        <div className="p-3 border-t border-slate-200 dark:border-slate-800 space-y-2">
          <div className="rounded-lg bg-slate-50 dark:bg-slate-800/70 border border-slate-200 dark:border-slate-700 p-2.5">
            <div className="flex items-center gap-1.5 text-[11px] font-semibold text-emerald-700 dark:text-emerald-400 mb-1">
              <ShieldCheck className="w-3.5 h-3.5 shrink-0" />
              <span>Local-First Privacy Mode</span>
            </div>
            <p className="text-[11px] font-medium text-slate-700 dark:text-slate-200 leading-snug line-clamp-2">
              {institution.institution_name}
            </p>
            <p className="text-[10px] text-slate-500 dark:text-slate-400 truncate mt-0.5">
              {institution.department}
            </p>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Command Header */}
        <header className="no-print h-14 border-b border-slate-200 bg-white/90 backdrop-blur dark:border-slate-800 dark:bg-slate-900/90 px-6 flex items-center justify-between sticky top-0 z-30">
          <div className="flex items-center gap-2.5 text-xs text-slate-600 dark:text-slate-300 min-w-0">
            <Cpu className="w-4 h-4 text-blue-600 dark:text-cyan-400 shrink-0" />
            <span className="font-semibold text-slate-900 dark:text-white truncate">
              {institution.institution_name}
            </span>
            <span className="hidden md:inline text-slate-400">|</span>
            <span className="hidden md:inline font-mono text-[11px] text-slate-500 dark:text-slate-400">
              ESM2-MLM + 3D Pocket DMS + True-Path DAG
            </span>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            <Link
              href="/settings"
              className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium border transition-opacity hover:opacity-90 ${providerBadge.cls}`}
            >
              <span className={`w-2 h-2 rounded-full ${providerBadge.dot}`} />
              <span>{providerBadge.label}</span>
            </Link>

            <button
              onClick={toggleDarkMode}
              title="Toggle Light / Dark Theme"
              className="p-2 rounded-lg border border-slate-200 bg-white text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
            >
              {darkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>
          </div>
        </header>

        <main className="flex-1 p-6 max-w-[1600px] w-full mx-auto">{children}</main>
      </div>
    </div>
  );
}
