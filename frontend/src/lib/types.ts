export interface InstitutionConfig {
  id?: number;
  institution_name: string;
  department: string;
  location: string;
  report_disclaimer: string;
  default_audience_mode: string;
  updated_at?: string;
}

export interface AIProviderOption {
  id: string;
  label: string;
  default_model: string;
  key_prefix: string;
}

export interface AIRouterStatus {
  active_provider: string;
  model_name: string;
  is_llm_connected: boolean;
  masked_key: string | null;
  status: string;
  last_error: string | null;
  available_models?: string[];
  supported_providers: AIProviderOption[];
}

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  uptime_seconds: number;
  ml_engine: {
    backbone: string;
    go_terms: number;
    training_proteins: number;
    real_3mer_trained: boolean;
  };
  ai_router: AIRouterStatus;
  institution: InstitutionConfig;
}

export interface ProteinPreset {
  name: string;
  uniprot_id: string;
  organism: string;
  af_id: string;
  description: string;
  sequence: string;
}

export interface ClinicalVariantPreset {
  id: string;
  title: string;
  gene_symbol: string;
  uniprot_id: string;
  protein_name: string;
  position: number;
  wt_aa: string;
  mut_aa: string;
  clinical_context: string;
  expected_category: string;
}

export interface TeachingLab {
  lab_id: string;
  code: string;
  title: string;
  difficulty: string;
  duration_min: number;
  target_courses: string[];
  uniprot_id: string;
  gene_symbol: string;
  position: number;
  mut_aa: string;
  objectives: string[];
  viva_questions: string[];
}

export interface GOTermPrediction {
  term: string;
  name: string;
  aspect: string;
  score: number;
  raw_score: number;
  repaired: boolean;
  repair_delta: number;
  ia: number;
  definition: string;
}

export interface DAGNodePayload {
  id: string;
  label: string;
  aspect: string;
  raw_score: number;
  propagated_score: number;
  repaired: boolean;
  repair_delta: number;
  ia_weight: number;
  definition: string;
}

export interface DAGEdgePayload {
  id: string;
  source: string;
  target: string;
  repaired_flow: boolean;
}

export interface ReactFlowDAGPayload {
  aspect: string;
  node_count: number;
  edge_count: number;
  repaired_node_count: number;
  nodes: DAGNodePayload[];
  edges: DAGEdgePayload[];
}

export interface ResidueProfilePoint {
  position: number;
  aa: string;
  saliency: number;
  plddt: number | null;
  is_hotspot: boolean;
}

export interface ModelArenaRow {
  term: string;
  name: string;
  aspect: string;
  ia_weight: number;
  prior: number;
  kmer_3: number;
  esm2_knn: number;
  esm2_mlp: number;
  ensemble_raw: number;
  true_path_final: number;
}

export interface ProteinAnalysisResponse {
  protein_name: string;
  sequence: string;
  sequence_length: number;
  est_mass_kda: number;
  sequence_sha256: string;
  uniprot_id: string | null;
  cached: boolean;
  latency_ms: number;
  model_metadata: {
    backbone: string;
    real_3mer_trained: boolean;
    num_go_terms: number;
    training_proteins: number;
  };
  categorized: {
    MF: GOTermPrediction[];
    BP: GOTermPrediction[];
    CC: GOTermPrediction[];
  };
  summary_counts: {
    MF: number;
    BP: number;
    CC: number;
    total_active: number;
  };
  dag_audit: {
    violations_before: number;
    violations_after: number;
    convergence_iterations: number;
    terms_repaired: number;
    max_repair_delta: number;
    repair_log: Array<{
      term: string;
      name: string;
      aspect: string;
      raw_score: number;
      propagated_score: number;
      delta: number;
      ia_weight: number;
    }>;
  };
  dags: {
    MF: ReactFlowDAGPayload;
    BP: ReactFlowDAGPayload;
    CC: ReactFlowDAGPayload;
  };
  xai: {
    method: string;
    mean_saliency: number;
    hotspot_count: number;
    hotspot_indices: number[];
    top_hotspots: Array<{ position: number; residue: string; saliency: number }>;
    residue_profile: ResidueProfilePoint[];
  };
  model_arena: {
    rows: ModelArenaRow[];
    timings_ms: {
      kmer_3: number;
      esm2_knn: number;
      esm2_mlp: number;
      dag_propagation: number;
    };
  };
  structure: {
    available: boolean;
    alphafold_id: string | null;
    is_exact_match: boolean;
    mean_plddt: number | null;
    num_residues_3d?: number;
    confidence_bands: {
      very_high: number;
      confident: number;
      low: number;
      very_low_disordered: number;
    } | null;
    plddt_profile: Array<{ position: number; aa: string; plddt: number }>;
    pdb_content: string | null;
  };
  bio_evidence?: {
    uniprot?: Record<string, any>;
    open_targets?: Record<string, any>;
  };
}

export interface PocketDMSRow {
  position: number;
  wt_aa: string;
  is_target: boolean;
  distance_angstrom: number | null;
  plddt: number | null;
  conservation: number;
  scores: Record<string, number>;
  best_tolerated: Array<{ aa: string; llr: number }>;
  most_damaging: Array<{ aa: string; llr: number }>;
}

export interface VariantAnalysisResponse {
  mutation: string;
  position: number;
  wt_aa: string;
  mut_aa: string;
  uniprot_id: string | null;
  gene_symbol: string | null;
  protein_name: string;
  sequence_sha256: string;
  latency_ms: number;
  pdb_content: string | null;
  dual_axis_assessment: {
    composite_risk_score: number;
    risk_tier: string;
    severity: "pathogenic" | "likely_pathogenic" | "vus" | "benign";
    acmg_computational_cue: string;
    evolutionary_llr: number;
    evolutionary_risk_component: number;
    functional_go_risk_component: number;
    structural_burial_component: number;
    conservation_index: number;
    wt_marginal_prob: number;
    embedding_cosine_shift: number;
    fdi_score: number;
  };
  go_disruption: {
    fdi_score: number;
    fdi_normalized: number;
    ia_weighted_l1: number;
    mut_dag_violations_after: number;
    lost_functions: Array<{
      term: string;
      name: string;
      aspect: string;
      wt_score: number;
      mut_score: number;
      delta: number;
      ia: number;
    }>;
    gained_functions: Array<{
      term: string;
      name: string;
      aspect: string;
      wt_score: number;
      mut_score: number;
      delta: number;
      ia: number;
    }>;
  };
  structural_pocket: {
    available: boolean;
    target_position: number;
    target_aa?: string;
    target_plddt: number | null;
    structural_region: string;
    burial_contacts_8A: number;
    burial_score: number;
    pocket_radius_angstrom: number;
    all_5A_contact_count?: number;
    pocket_residues: Array<{
      position: number;
      aa: string;
      res_name: string;
      distance_angstrom: number;
      ca_distance_angstrom: number;
      plddt: number;
      is_sequence_adjacent: boolean;
    }>;
    pocket_positions: number[];
  };
  pocket_dms: {
    amino_acids: string[];
    rows: PocketDMSRow[];
    rescue_or_tolerated_candidates: Array<{
      mutation: string;
      position: number;
      wt_aa: string;
      alt_aa: string;
      llr: number;
      is_target_site: boolean;
      distance_angstrom: number | null;
    }>;
    most_fragile_pocket_mutations: Array<{
      mutation: string;
      position: number;
      llr: number;
      conservation: number;
    }>;
  };
  wt_summary: {
    sequence_length: number;
    alphafold_id: string | null;
    mean_plddt: number | null;
  };
  bio_evidence?: {
    uniprot?: Record<string, any>;
    clinvar?: Record<string, any>;
    open_targets?: Record<string, any>;
  };
}

export interface CopilotSynthesisResponse {
  provider_used: string;
  model_used: string;
  audience_mode: string;
  is_live_llm: boolean;
  headline: string;
  executive_summary: string;
  structural_mechanism: string;
  functional_ontology_impact: string;
  therapeutic_and_actionable_next_steps: string;
  key_citations: string[];
}

export interface SavedCaseSummary {
  id: number;
  case_code: string;
  title: string;
  protein_name: string;
  uniprot_id: string | null;
  gene_symbol: string | null;
  mutation: string | null;
  composite_risk_score: number | null;
  evolutionary_llr: number | null;
  risk_tier: string | null;
  sequence_sha256: string;
  clinician_notes: string;
  mode: string;
  created_at: string;
}
