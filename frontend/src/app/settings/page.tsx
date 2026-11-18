"use client";

import React, { useEffect, useState } from "react";
import {
  Activity,
  Building2,
  CheckCircle2,
  KeyRound,
  Loader2,
  Save,
  ShieldCheck,
  Sparkles,
  XCircle,
} from "lucide-react";
import { api } from "@/lib/api";
import { useWorkspace } from "@/context/WorkspaceContext";
import type { InstitutionConfig } from "@/lib/types";

export default function SettingsPage() {
  const { institution, aiStatus, refreshSystemState } = useWorkspace();

  // AI Auto-Config State
  const [provider, setProvider] = useState("auto");
  const [apiKey, setApiKey] = useState("");
  const [modelName, setModelName] = useState("");
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const [discoveringModels, setDiscoveringModels] = useState(false);
  const [ollamaUrl, setOllamaUrl] = useState("http://localhost:11434");
  const [aiTesting, setAiTesting] = useState(false);
  const [aiResult, setAiResult] = useState<{ ok: boolean; msg: string } | null>(null);

  // Institutional White-Label State
  const [instForm, setInstForm] = useState<InstitutionConfig>(institution);
  const [instSaving, setInstSaving] = useState(false);
  const [instSaved, setInstSaved] = useState(false);

  // Admin Telemetry
  const [telemetry, setTelemetry] = useState<Record<string, any> | null>(null);

  useEffect(() => {
    setInstForm(institution);
  }, [institution]);

  useEffect(() => {
    if (aiStatus?.available_models && aiStatus.available_models.length > 0) {
      setAvailableModels(aiStatus.available_models);
    }
  }, [aiStatus]);

  useEffect(() => {
    api.getTelemetry().then(setTelemetry).catch(() => {});
  }, []);

  const detectedHint = (() => {
    const k = apiKey.trim();
    if (!k) return null;
    if (k.startsWith("AIza")) return "Auto-detected: Google Gemini Key";
    if (k.startsWith("xai-")) return "Auto-detected: xAI Grok Key";
    if (k.startsWith("gsk_")) return "Auto-detected: Groq Cloud Key";
    return "Will verify against selected provider";
  })();

  const handleDiscoverModels = async () => {
    setDiscoveringModels(true);
    setAiResult(null);
    try {
      const res = await api.discoverAIModels({
        provider,
        api_key: apiKey.trim() || undefined,
        ollama_url: ollamaUrl.trim() || undefined,
      });
      if (res.ok && res.models.length > 0) {
        setAvailableModels(res.models);
        setModelName(res.recommended || res.models[0]);
        setAiResult({
          ok: true,
          msg: `Found ${res.models.length} live ${res.provider.toUpperCase()} model(s) for this key. Selected '${res.recommended || res.models[0]}'. Click Verify & Save to activate.`,
        });
      } else {
        setAiResult({
          ok: false,
          msg: res.error || "Could not list models for this key.",
        });
      }
    } catch (err: any) {
      setAiResult({ ok: false, msg: err?.message || "Model discovery failed." });
    } finally {
      setDiscoveringModels(false);
    }
  };

  const handleConfigureAI = async (e: React.FormEvent) => {
    e.preventDefault();
    setAiTesting(true);
    setAiResult(null);
    try {
      const res = await api.configureAI({
        provider,
        api_key: apiKey.trim() || undefined,
        model_name: modelName.trim() || undefined,
        ollama_url: ollamaUrl.trim() || undefined,
      });
      if (res.available_models && res.available_models.length > 0) {
        setAvailableModels(res.available_models);
      }
      if (res.model_name && res.verified) {
        setModelName(res.model_name);
      }
      setAiResult({ ok: res.verified, msg: res.message });
      if (res.verified) {
        setApiKey("");
        await refreshSystemState();
      }
    } catch (err: any) {
      setAiResult({ ok: false, msg: err?.message || "Configuration request failed." });
    } finally {
      setAiTesting(false);
    }
  };

  const handleSaveInstitution = async (e: React.FormEvent) => {
    e.preventDefault();
    setInstSaving(true);
    setInstSaved(false);
    try {
      await api.updateInstitution(instForm);
      await refreshSystemState();
      setInstSaved(true);
      setTimeout(() => setInstSaved(false), 3000);
    } finally {
      setInstSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white">
          Auto-Configuring AI Providers, Institutional Branding &amp; Admin Console
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Paste a <strong>Google Gemini</strong>, <strong>xAI Grok</strong>, or <strong>Groq</strong> API key to automatically verify and enable live Explainable AI synthesis—or customize white-label institutional branding for any college or lab.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Auto-Configure Gemini / Grok / Ollama Wizard */}
        <form
          onSubmit={handleConfigureAI}
          className="lg:col-span-6 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 space-y-4"
        >
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <KeyRound className="w-5 h-5 text-blue-600" />
              <h2 className="text-base font-bold text-slate-900 dark:text-white">
                Explainable AI Provider Auto-Setup
              </h2>
            </div>
            <span
              className={`text-[11px] font-semibold px-2.5 py-0.5 rounded-full ${
                aiStatus?.is_llm_connected
                  ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                  : "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300"
              }`}
            >
              Active: {aiStatus?.active_provider?.toUpperCase() || "DETERMINISTIC"}
            </span>
          </div>

          <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 text-xs space-y-1">
            <div className="flex justify-between">
              <span className="text-slate-500">Current Model</span>
              <span className="font-mono font-semibold">{aiStatus?.model_name || "evidence-cited-local"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Stored Key</span>
              <span className="font-mono">{aiStatus?.masked_key || "None (Offline Evidence Engine)"}</span>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">
              Provider Selection
            </label>
            <select
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 text-xs font-medium"
            >
              <option value="auto">Auto-Detect from API Key Prefix (Recommended)</option>
              <option value="gemini">Google Gemini (AIza... · Auto-Discover Models)</option>
              <option value="grok">xAI Grok (xai-... · Auto-Discover Models)</option>
              <option value="groq">Groq Cloud (gsk_... · Auto-Discover Models)</option>
              <option value="ollama">Local Ollama (Air-Gapped College / Hospital LAN)</option>
              <option value="deterministic">Zero-Key Local Evidence-Cited Engine</option>
            </select>
          </div>

          {provider !== "ollama" && provider !== "deterministic" && (
            <div>
              <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">
                API Key (Stored Locally in <span className="font-mono">backend/.env</span>)
              </label>
              <div className="flex gap-2">
                <input
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="Paste Gemini (AIza...), xAI Grok (xai-...), or Groq (gsk_...) key"
                  className="flex-1 px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 font-mono text-xs"
                />
                <button
                  type="button"
                  onClick={handleDiscoverModels}
                  disabled={discoveringModels}
                  className="px-3 py-2 rounded-lg border border-blue-300 dark:border-blue-700 bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-cyan-300 hover:bg-blue-100 dark:hover:bg-blue-900/60 text-xs font-semibold whitespace-nowrap inline-flex items-center gap-1.5"
                >
                  {discoveringModels ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : null}
                  Fetch Models
                </button>
              </div>
              {detectedHint && (
                <p className="text-[11px] font-semibold text-blue-600 dark:text-cyan-400 mt-1">
                  {detectedHint}
                </p>
              )}
            </div>
          )}

          {provider === "ollama" && (
            <div>
              <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">
                Local Ollama Base URL
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={ollamaUrl}
                  onChange={(e) => setOllamaUrl(e.target.value)}
                  className="flex-1 px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 font-mono text-xs"
                />
                <button
                  type="button"
                  onClick={handleDiscoverModels}
                  disabled={discoveringModels}
                  className="px-3 py-2 rounded-lg border border-blue-300 dark:border-blue-700 bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-cyan-300 text-xs font-semibold"
                >
                  Fetch Models
                </button>
              </div>
            </div>
          )}

          {provider !== "deterministic" && (
            <div className="space-y-2">
              {availableModels.length > 0 && (
                <div>
                  <label className="block text-xs font-semibold text-emerald-700 dark:text-emerald-400 mb-1">
                    Available Models for Your API Key ({availableModels.length} discovered)
                  </label>
                  <select
                    value={modelName}
                    onChange={(e) => setModelName(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-emerald-400 dark:border-emerald-700 bg-white dark:bg-slate-950 font-mono text-xs font-semibold"
                  >
                    <option value="">Auto-Select Best Working Model</option>
                    {availableModels.map((m) => (
                      <option key={m} value={m}>
                        {m}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">
                  {availableModels.length > 0
                    ? "Or Type Custom Model ID"
                    : "Model Selection (Leave Blank to Auto-Discover Best Available Model on Your Key)"}
                </label>
                <input
                  type="text"
                  value={modelName}
                  onChange={(e) => setModelName(e.target.value)}
                  placeholder="Auto-discover (e.g., gemini-3.8-flash, gemini-2.5-flash, grok-3-mini)"
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 font-mono text-xs"
                />
              </div>
            </div>
          )}

          {aiResult && (
            <div
              className={`p-3 rounded-lg border text-xs flex items-start gap-2 ${
                aiResult.ok
                  ? "bg-emerald-50 border-emerald-200 text-emerald-800 dark:bg-emerald-950/40 dark:border-emerald-800 dark:text-emerald-300"
                  : "bg-rose-50 border-rose-200 text-rose-800 dark:bg-rose-950/40 dark:border-rose-800 dark:text-rose-300"
              }`}
            >
              {aiResult.ok ? (
                <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" />
              ) : (
                <XCircle className="w-4 h-4 shrink-0 mt-0.5" />
              )}
              <span>{aiResult.msg}</span>
            </div>
          )}

          <button
            type="submit"
            disabled={aiTesting}
            className="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-bold"
          >
            {aiTesting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
            Auto-Detect, Verify &amp; Save AI Provider
          </button>

          <p className="text-[11px] text-slate-500 flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
            Keys remain strictly on your local machine; never exposed to browser localStorage or external telemetry.
          </p>
        </form>

        {/* Right: White-Label Institutional Deployment Settings */}
        <form
          onSubmit={handleSaveInstitution}
          className="lg:col-span-6 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 space-y-4"
        >
          <div className="flex items-center gap-2">
            <Building2 className="w-5 h-5 text-emerald-600" />
            <h2 className="text-base font-bold text-slate-900 dark:text-white">
              White-Label Institutional &amp; College Branding
            </h2>
          </div>
          <p className="text-xs text-slate-500">
            Deploy ProteinLens-OS at any university, hospital, or research lab. Changes update the sidebar and all exported PDF/JSON clinical dossiers immediately.
          </p>

          <div>
            <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">
              Institution / Organization Name
            </label>
            <input
              type="text"
              value={instForm.institution_name}
              onChange={(e) => setInstForm({ ...instForm, institution_name: e.target.value })}
              className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 text-xs font-semibold"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">
                Department / Lab Unit
              </label>
              <input
                type="text"
                value={instForm.department}
                onChange={(e) => setInstForm({ ...instForm, department: e.target.value })}
                className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 text-xs"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">
                Location
              </label>
              <input
                type="text"
                value={instForm.location}
                onChange={(e) => setInstForm({ ...instForm, location: e.target.value })}
                className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 text-xs"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">
              Clinical / Academic Report Disclaimer Footer
            </label>
            <textarea
              rows={3}
              value={instForm.report_disclaimer}
              onChange={(e) => setInstForm({ ...instForm, report_disclaimer: e.target.value })}
              className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 text-xs"
            />
          </div>

          <button
            type="submit"
            disabled={instSaving}
            className="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-slate-900 dark:bg-emerald-600 hover:opacity-90 text-white text-xs font-bold"
          >
            {instSaved ? <CheckCircle2 className="w-4 h-4 text-emerald-400" /> : <Save className="w-4 h-4" />}
            {instSaved ? "Institutional Branding Saved!" : "Save Institutional Branding"}
          </button>
        </form>
      </div>

      {/* Live Institutional Telemetry Panel */}
      {telemetry && (
        <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 space-y-3">
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-blue-600" />
            <h2 className="text-sm font-bold text-slate-900 dark:text-white">
              Live Institutional Deployment Telemetry
            </h2>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/70">
              <div className="text-[11px] text-slate-500">Protein Runs</div>
              <div className="font-mono text-lg font-extrabold">{telemetry.engine_metrics?.protein_runs ?? 0}</div>
            </div>
            <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/70">
              <div className="text-[11px] text-slate-500">Variant / DMS Runs</div>
              <div className="font-mono text-lg font-extrabold">
                {telemetry.engine_metrics?.variant_runs ?? 0} / {telemetry.engine_metrics?.dms_runs ?? 0}
              </div>
            </div>
            <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/70">
              <div className="text-[11px] text-slate-500">Cache Hit Ratio</div>
              <div className="font-mono text-lg font-extrabold text-emerald-600">
                {telemetry.engine_metrics?.cache_hit_rate_pct ?? 0}%
              </div>
            </div>
            <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/70">
              <div className="text-[11px] text-slate-500">Saved SQLite Cases</div>
              <div className="font-mono text-lg font-extrabold">{telemetry.saved_cases ?? 0}</div>
            </div>
            <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/70">
              <div className="text-[11px] text-slate-500">Server Uptime</div>
              <div className="font-mono text-lg font-extrabold">{telemetry.uptime_seconds}s</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
