import type {
  AIRouterStatus,
  ClinicalVariantPreset,
  CopilotSynthesisResponse,
  HealthResponse,
  InstitutionConfig,
  ProteinAnalysisResponse,
  ProteinPreset,
  SavedCaseSummary,
  TeachingLab,
  VariantAnalysisResponse,
} from "./types";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
  });
  if (!resp.ok) {
    let detail = `HTTP ${resp.status}`;
    try {
      const err = await resp.json();
      detail = err.detail || err.message || detail;
    } catch {
      // ignore json parse error
    }
    throw new Error(detail);
  }
  return resp.json() as Promise<T>;
}

export const api = {
  health: () => apiFetch<HealthResponse>("/api/health"),

  presets: () =>
    apiFetch<{
      proteins: ProteinPreset[];
      clinical_variants: ClinicalVariantPreset[];
      teaching_labs: TeachingLab[];
    }>("/api/presets"),

  analyzeProtein: (body: {
    sequence?: string;
    uniprot_id?: string;
    protein_name?: string;
    min_confidence?: number;
    include_bio_evidence?: boolean;
  }) =>
    apiFetch<ProteinAnalysisResponse>("/api/analyze/protein", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  analyzeVariant: (body: {
    sequence?: string;
    uniprot_id?: string;
    gene_symbol?: string;
    protein_name?: string;
    position: number;
    mut_aa: string;
    run_pocket_dms?: boolean;
    max_pocket_residues?: number;
    include_bio_evidence?: boolean;
  }) =>
    apiFetch<VariantAnalysisResponse>("/api/analyze/variant", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  startBatch: (body: {
    title: string;
    items: Array<{
      label?: string;
      uniprot_id?: string;
      gene_symbol?: string;
      sequence?: string;
      position: number;
      mut_aa: string;
    }>;
  }) =>
    apiFetch<{ job_uid: string; status: string; total_items: number }>(
      "/api/analyze/batch",
      { method: "POST", body: JSON.stringify(body) }
    ),

  getBatchJob: (jobUid: string) =>
    apiFetch<{
      job_uid: string;
      title: string;
      status: string;
      total_items: number;
      completed_items: number;
      results: Array<Record<string, any>>;
      error_message: string | null;
    }>(`/api/jobs/${jobUid}`),

  getAISettings: () => apiFetch<AIRouterStatus>("/api/settings/ai"),

  discoverAIModels: (body: {
    provider: string;
    api_key?: string;
    ollama_url?: string;
  }) =>
    apiFetch<{
      ok: boolean;
      provider: string;
      models: string[];
      recommended?: string;
      error?: string;
    }>("/api/settings/ai/models", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  configureAI: (body: {
    provider: string;
    api_key?: string;
    model_name?: string;
    ollama_url?: string;
  }) =>
    apiFetch<AIRouterStatus & { verified: boolean; message: string; detected_provider?: string }>(
      "/api/settings/ai",
      { method: "POST", body: JSON.stringify(body) }
    ),

  getInstitution: () => apiFetch<InstitutionConfig>("/api/settings/institution"),

  updateInstitution: (body: InstitutionConfig) =>
    apiFetch<InstitutionConfig>("/api/settings/institution", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  synthesizeCopilot: (body: {
    evidence_packet: Record<string, any>;
    audience_mode: "clinical" | "research" | "student";
  }) =>
    apiFetch<CopilotSynthesisResponse>("/api/copilot/synthesize", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  listCases: () => apiFetch<SavedCaseSummary[]>("/api/cases"),

  getCaseDetail: (id: number) =>
    apiFetch<SavedCaseSummary & { payload: Record<string, any> }>(
      `/api/cases/${id}`
    ),

  saveCase: (body: {
    title: string;
    protein_name: string;
    uniprot_id?: string | null;
    gene_symbol?: string | null;
    mutation?: string | null;
    composite_risk_score?: number | null;
    evolutionary_llr?: number | null;
    risk_tier?: string | null;
    sequence_sha256: string;
    clinician_notes?: string;
    mode?: string;
    payload: Record<string, any>;
  }) =>
    apiFetch<{ id: number; case_code: string; created_at: string }>(
      "/api/cases",
      { method: "POST", body: JSON.stringify(body) }
    ),

  updateCaseNotes: (id: number, clinician_notes: string) =>
    apiFetch<{ id: number; clinician_notes: string }>(`/api/cases/${id}/notes`, {
      method: "PATCH",
      body: JSON.stringify({ clinician_notes }),
    }),

  deleteCase: (id: number) =>
    apiFetch<{ deleted: boolean; id: number }>(`/api/cases/${id}`, {
      method: "DELETE",
    }),

  getTelemetry: () => apiFetch<Record<string, any>>("/api/admin/telemetry"),
};
