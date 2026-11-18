"""
ProteinLens-OS Auto-Configuring Multi-Provider Explainable AI (XAI) Router
Automatically detects, discovers LIVE available models for the user's API key,
verifies, persists, and routes grounded XAI synthesis across:
1. Google Gemini (GEMINI_API_KEY / GOOGLE_API_KEY, prefix 'AIza...')
2. xAI Grok (XAI_API_KEY / GROK_API_KEY, prefix 'xai-...')
3. Groq Fast Inference (GROQ_API_KEY, prefix 'gsk_...')
4. Local Ollama (http://localhost:11434) for 100% air-gapped institutional labs
5. Deterministic Evidence-Cited Scientific Fallback (zero-key offline guarantee)
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import httpx


DEFAULT_MODELS = {
    "gemini": "gemini-3.8-flash",
    "grok": "grok-3-mini",
    "groq": "llama-3.3-70b-versatile",
    "ollama": "llama3.2",
}


def detect_provider_from_key(api_key: str) -> str:
    key = api_key.strip()
    if key.startswith("AIza"):
        return "gemini"
    if key.startswith("xai-"):
        return "grok"
    if key.startswith("gsk_"):
        return "groq"
    return "gemini"


def mask_key(api_key: Optional[str]) -> Optional[str]:
    if not api_key or len(api_key) < 8:
        return None
    return f"{api_key[:6]}...{api_key[-4:]}"


def _rank_gemini_model(model_id: str) -> Tuple[int, float, int]:
    """
    Higher tuple = higher preference for interactive XAI synthesis.
    Prefers latest Flash models (e.g., gemini-3.8-flash, gemini-3-flash, gemini-2.5-flash,
    gemini-2.0-flash) over older/experimental/lite models, while excluding non-chat models.
    """
    m = model_id.lower()
    # Extract numeric version like 3.8, 3.0, 2.5, 2.0, 1.5
    ver_match = re.search(r"gemini-(\d+(?:\.\d+)?)", m)
    version = float(ver_match.group(1)) if ver_match else 0.0

    is_flash = 1 if "flash" in m else 0
    is_lite = -1 if "lite" in m else 0
    is_exp = -1 if ("exp" in m or "preview" in m or "thinking" in m) else 0
    is_pro = 1 if "pro" in m else 0

    # Primary tier: stable flash > preview flash > pro > other
    tier = 0
    if is_flash and not is_lite and is_exp == 0:
        tier = 4
    elif is_flash and not is_lite:
        tier = 3
    elif is_pro and is_exp == 0:
        tier = 2
    elif is_flash:
        tier = 1
    return (tier, version, is_exp)


def _is_usable_gemini_chat_model(model_id: str, methods: List[str]) -> bool:
    if "generateContent" not in methods:
        return False
    m = model_id.lower()
    blocked_substrings = (
        "embedding",
        "imagen",
        "veo",
        "aqa",
        "tts",
        "audio",
        "robotics",
        "computer-use",
        "deep-research",
        "gemma",
        "learnlm",
        "vision",
    )
    if any(b in m for b in blocked_substrings):
        return False
    return "gemini" in m


class AutoConfigAIRouter:
    def __init__(self, env_file: Path):
        self.env_file = env_file
        self.provider: str = "deterministic"
        self.model_name: str = "evidence-cited-local"
        self.api_key: Optional[str] = None
        self.ollama_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.last_status: str = "ready"
        self.last_error: Optional[str] = None
        self.available_models: List[str] = []
        self.auto_discover()

    def _load_env_file(self) -> Dict[str, str]:
        vals: Dict[str, str] = {}
        if self.env_file.exists():
            for line in self.env_file.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                vals[k.strip()] = v.strip().strip('"').strip("'")
        return vals

    def _save_env_key(self, env_var: str, value: str) -> None:
        existing = self._load_env_file()
        existing[env_var] = value
        lines = [f"{k}={v}" for k, v in existing.items()]
        self.env_file.parent.mkdir(parents=True, exist_ok=True)
        self.env_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
        os.environ[env_var] = value

    def auto_discover(self) -> Dict[str, Any]:
        """Scan OS environment and local .env in priority order to auto-configure XAI."""
        file_env = self._load_env_file()

        def _get(name: str) -> Optional[str]:
            return os.getenv(name) or file_env.get(name)

        preferred = (_get("PROTEINLENS_AI_PROVIDER") or "").lower().strip()

        candidates: List[Tuple[str, Optional[str], str]] = [
            ("gemini", _get("GEMINI_API_KEY") or _get("GOOGLE_API_KEY"), _get("GEMINI_MODEL") or DEFAULT_MODELS["gemini"]),
            ("grok", _get("XAI_API_KEY") or _get("GROK_API_KEY"), _get("GROK_MODEL") or DEFAULT_MODELS["grok"]),
            ("groq", _get("GROQ_API_KEY"), _get("GROQ_MODEL") or DEFAULT_MODELS["groq"]),
        ]

        if preferred in ("gemini", "grok", "groq"):
            candidates.sort(key=lambda c: 0 if c[0] == preferred else 1)

        for prov, key, mdl in candidates:
            if key and len(key.strip()) >= 10:
                self.provider = prov
                self.api_key = key.strip()
                self.model_name = mdl
                self.last_status = "configured"
                self.last_error = None
                return self.get_status()

        self.provider = "deterministic"
        self.api_key = None
        self.model_name = "evidence-cited-local"
        self.last_status = "offline_fallback"
        return self.get_status()

    def get_status(self) -> Dict[str, Any]:
        return {
            "active_provider": self.provider,
            "model_name": self.model_name,
            "is_llm_connected": self.provider in ("gemini", "grok", "groq", "ollama"),
            "masked_key": mask_key(self.api_key),
            "status": self.last_status,
            "last_error": self.last_error,
            "available_models": self.available_models,
            "supported_providers": [
                {"id": "gemini", "label": "Google Gemini (Auto-Discover Models)", "default_model": DEFAULT_MODELS["gemini"], "key_prefix": "AIza..."},
                {"id": "grok", "label": "xAI Grok (Auto-Discover Models)", "default_model": DEFAULT_MODELS["grok"], "key_prefix": "xai-..."},
                {"id": "groq", "label": "Groq Cloud (Auto-Discover Models)", "default_model": DEFAULT_MODELS["groq"], "key_prefix": "gsk_..."},
                {"id": "ollama", "label": "Local Ollama (Air-Gapped)", "default_model": DEFAULT_MODELS["ollama"], "key_prefix": "Local URL"},
                {"id": "deterministic", "label": "Local Evidence-Cited Engine (Zero-Key)", "default_model": "evidence-cited-local", "key_prefix": "None"},
            ],
        }

    async def discover_models(
        self,
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
        ollama_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Query the live provider API using the supplied (or stored) key and return all
        usable chat/generation models sorted by capability & recency.
        """
        clean_key = (api_key or "").strip() or (self.api_key or "")
        prov = (provider or "auto").lower().strip()
        if prov in ("", "auto"):
            if clean_key:
                prov = detect_provider_from_key(clean_key)
            elif self.provider in ("gemini", "grok", "groq", "ollama"):
                prov = self.provider
            else:
                return {"ok": False, "provider": "deterministic", "models": [], "error": "Enter an API key first to discover available models."}

        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                if prov == "gemini":
                    if not clean_key:
                        return {"ok": False, "provider": prov, "models": [], "error": "Gemini API key required."}
                    resp = await client.get(
                        f"https://generativelanguage.googleapis.com/v1beta/models?key={clean_key}&pageSize=100"
                    )
                    if resp.status_code != 200:
                        return {"ok": False, "provider": prov, "models": [], "error": f"HTTP {resp.status_code}: {resp.text[:220]}"}
                    raw_models = resp.json().get("models", [])
                    usable: List[str] = []
                    for m in raw_models:
                        full_name = str(m.get("name", ""))
                        short_id = full_name.replace("models/", "").strip()
                        methods = m.get("supportedGenerationMethods", [])
                        if short_id and _is_usable_gemini_chat_model(short_id, methods):
                            usable.append(short_id)
                    usable = sorted(set(usable), key=_rank_gemini_model, reverse=True)
                    return {
                        "ok": True,
                        "provider": "gemini",
                        "models": usable,
                        "recommended": usable[0] if usable else DEFAULT_MODELS["gemini"],
                    }

                if prov == "grok":
                    if not clean_key:
                        return {"ok": False, "provider": prov, "models": [], "error": "xAI Grok API key required."}
                    resp = await client.get(
                        "https://api.x.ai/v1/models",
                        headers={"Authorization": f"Bearer {clean_key}"},
                    )
                    if resp.status_code != 200:
                        return {"ok": False, "provider": prov, "models": [], "error": f"HTTP {resp.status_code}: {resp.text[:220]}"}
                    raw = [str(m.get("id", "")) for m in resp.json().get("data", []) if m.get("id")]
                    usable = [m for m in raw if "image" not in m.lower() and "embed" not in m.lower()]
                    usable.sort(key=lambda s: ("grok-3" in s, "mini" in s, s), reverse=True)
                    return {
                        "ok": True,
                        "provider": "grok",
                        "models": usable,
                        "recommended": usable[0] if usable else DEFAULT_MODELS["grok"],
                    }

                if prov == "groq":
                    if not clean_key:
                        return {"ok": False, "provider": prov, "models": [], "error": "Groq API key required."}
                    resp = await client.get(
                        "https://api.groq.com/openai/v1/models",
                        headers={"Authorization": f"Bearer {clean_key}"},
                    )
                    if resp.status_code != 200:
                        return {"ok": False, "provider": prov, "models": [], "error": f"HTTP {resp.status_code}: {resp.text[:220]}"}
                    raw = [str(m.get("id", "")) for m in resp.json().get("data", []) if m.get("id")]
                    usable = [
                        m for m in raw
                        if not any(b in m.lower() for b in ("whisper", "guard", "tts", "embed"))
                    ]
                    usable.sort(key=lambda s: ("llama-3.3" in s, "70b" in s, s), reverse=True)
                    return {
                        "ok": True,
                        "provider": "groq",
                        "models": usable,
                        "recommended": usable[0] if usable else DEFAULT_MODELS["groq"],
                    }

                if prov == "ollama":
                    base = (ollama_url or self.ollama_url).rstrip("/")
                    resp = await client.get(f"{base}/api/tags")
                    resp.raise_for_status()
                    usable = [str(m.get("name", "")) for m in resp.json().get("models", []) if m.get("name")]
                    return {
                        "ok": True,
                        "provider": "ollama",
                        "models": usable,
                        "recommended": usable[0] if usable else DEFAULT_MODELS["ollama"],
                    }

            return {"ok": False, "provider": prov, "models": [], "error": f"Unsupported provider {prov}"}
        except Exception as exc:
            return {"ok": False, "provider": prov, "models": [], "error": str(exc)}

    async def configure_and_verify(
        self,
        api_key: Optional[str] = None,
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        ollama_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        1. Auto-detect provider from key prefix if provider=='auto' or omitted.
        2. Query the provider's LIVE model list for this API key!
        3. If user didn't pick a specific model (or picked one unavailable), automatically
           test & select the highest-ranked working model available on that key!
        4. Persist verified provider + model + key into local backend/.env.
        """
        prov = (provider or "auto").lower().strip()
        clean_key = (api_key or "").strip()

        # Allow switching model on already-configured provider without re-pasting key
        if not clean_key and self.api_key and prov in ("auto", "", self.provider):
            clean_key = self.api_key
            if prov in ("auto", ""):
                prov = self.provider

        if prov == "deterministic":
            self.provider = "deterministic"
            self.api_key = None
            self.model_name = "evidence-cited-local"
            self.available_models = []
            self.last_status = "offline_fallback"
            self.last_error = None
            self._save_env_key("PROTEINLENS_AI_PROVIDER", "deterministic")
            return {"verified": True, "message": "Switched to Zero-Key Local Evidence-Cited Engine.", **self.get_status()}

        if prov == "ollama":
            base = (ollama_url or self.ollama_url).rstrip("/")
            disc = await self.discover_models("ollama", ollama_url=base)
            if not disc["ok"]:
                self.last_error = disc.get("error")
                return {"verified": False, "message": f"Ollama not reachable at {base}: {disc.get('error')}", **self.get_status()}
            models = disc["models"]
            mdl = (model_name or "").strip() or (models[0] if models else DEFAULT_MODELS["ollama"])
            self.provider = "ollama"
            self.ollama_url = base
            self.model_name = mdl
            self.api_key = None
            self.available_models = models
            self.last_status = "verified"
            self.last_error = None
            self._save_env_key("PROTEINLENS_AI_PROVIDER", "ollama")
            self._save_env_key("OLLAMA_BASE_URL", base)
            return {"verified": True, "message": f"Connected to local Ollama ({mdl}). Found {len(models)} local model(s).", **self.get_status()}

        if not clean_key:
            return {"verified": False, "message": "Please enter an API key (Gemini AIza..., xAI Grok xai-..., or Groq gsk_...).", **self.get_status()}

        if prov in ("", "auto"):
            prov = detect_provider_from_key(clean_key)

        # Step 1: Discover LIVE models available to this API key
        disc = await self.discover_models(prov, api_key=clean_key)
        discovered_models: List[str] = disc.get("models", []) if disc.get("ok") else []

        # Build prioritized candidate list to verify
        requested_model = (model_name or "").strip()
        candidates: List[str] = []
        if requested_model:
            candidates.append(requested_model)
        # Add top discovered models from this exact API key
        for m in discovered_models[:6]:
            if m not in candidates:
                candidates.append(m)
        # Fallback defaults if model list endpoint was restricted
        if not candidates:
            candidates.append(DEFAULT_MODELS.get(prov, DEFAULT_MODELS["gemini"]))

        # Step 2: Live ping candidates in priority order until one works
        chosen_model: Optional[str] = None
        last_err = ""
        for cand in candidates:
            ok, detail = await self._ping_provider(prov, clean_key, cand)
            if ok:
                chosen_model = cand
                break
            last_err = f"{cand}: {detail}"

        if not chosen_model:
            self.last_error = last_err
            self.available_models = discovered_models
            return {
                "verified": False,
                "detected_provider": prov,
                "available_models": discovered_models,
                "message": f"Verification failed for {prov.upper()}. Last error: {last_err}",
                **self.get_status(),
            }

        # Step 3: Persist verified config
        env_map = {"gemini": "GEMINI_API_KEY", "grok": "XAI_API_KEY", "groq": "GROQ_API_KEY"}
        model_env_map = {"gemini": "GEMINI_MODEL", "grok": "GROK_MODEL", "groq": "GROQ_MODEL"}
        self._save_env_key(env_map[prov], clean_key)
        self._save_env_key(model_env_map[prov], chosen_model)
        self._save_env_key("PROTEINLENS_AI_PROVIDER", prov)

        self.provider = prov
        self.api_key = clean_key
        self.model_name = chosen_model
        self.available_models = discovered_models or [chosen_model]
        self.last_status = "verified"
        self.last_error = None

        note = ""
        if requested_model and requested_model != chosen_model:
            note = f" (Requested '{requested_model}' was unavailable on this key; automatically selected working model '{chosen_model}'.)"

        return {
            "verified": True,
            "detected_provider": prov,
            "message": f"Auto-configured & verified {prov.upper()} using '{chosen_model}' ({len(self.available_models)} available models discovered).{note}",
            **self.get_status(),
        }

    async def _ping_provider(self, prov: str, key: str, model: str) -> Tuple[bool, str]:
        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                if prov == "gemini":
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
                    resp = await client.post(
                        url,
                        json={"contents": [{"parts": [{"text": "Reply OK"}]}], "generationConfig": {"maxOutputTokens": 8}},
                    )
                    if resp.status_code == 200:
                        return True, "OK"
                    return False, f"HTTP {resp.status_code}: {resp.text[:180]}"

                elif prov == "grok":
                    resp = await client.post(
                        "https://api.x.ai/v1/chat/completions",
                        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                        json={"model": model, "messages": [{"role": "user", "content": "Reply OK"}], "max_tokens": 8},
                    )
                    if resp.status_code == 200:
                        return True, "OK"
                    return False, f"HTTP {resp.status_code}: {resp.text[:180]}"

                elif prov == "groq":
                    resp = await client.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                        json={"model": model, "messages": [{"role": "user", "content": "Reply OK"}], "max_tokens": 8},
                    )
                    if resp.status_code == 200:
                        return True, "OK"
                    return False, f"HTTP {resp.status_code}: {resp.text[:180]}"

            return False, f"Unsupported provider {prov}"
        except Exception as exc:
            return False, str(exc)

    async def synthesize_xai_explanation(
        self,
        evidence_packet: Dict[str, Any],
        audience_mode: str = "clinical",
        institution_name: str = "IIIT Nagpur — Computational Biology & AI Lab",
    ) -> Dict[str, Any]:
        """
        Generate a strictly evidence-grounded Explainable AI (XAI) briefing.
        Uses active configured LLM (Gemini / Grok / Groq / Ollama) and falls back cleanly
        to the deterministic citation-anchored scientific synthesizer if offline or unconfigured.
        """
        mode = audience_mode.lower().strip()
        if mode not in ("clinical", "research", "student"):
            mode = "clinical"

        if self.provider in ("gemini", "grok", "groq", "ollama"):
            llm_out = await self._call_active_llm(evidence_packet, mode, institution_name)
            if llm_out:
                return {
                    "provider_used": self.provider,
                    "model_used": self.model_name,
                    "audience_mode": mode,
                    "is_live_llm": True,
                    **llm_out,
                }

        det = self._deterministic_synthesis(evidence_packet, mode, institution_name)
        return {
            "provider_used": "deterministic",
            "model_used": "evidence-cited-local",
            "audience_mode": mode,
            "is_live_llm": False,
            **det,
        }

    async def _call_active_llm(
        self,
        evidence_packet: Dict[str, Any],
        mode: str,
        institution_name: str,
    ) -> Optional[Dict[str, Any]]:
        role_instructions = {
            "clinical": "Write for a Clinical Geneticist & Molecular Pathologist. Focus on ACMG computational evidence (PP3/BP4), VUS triage priority, 3D structural pocket impact, ClinVar concordance, and known Open Targets therapeutics. Include a Research-Use-Only clinical disclaimer.",
            "research": "Write for a Computational Structural Biologist. Focus on ESM2 Masked-Marginal LLR biophysics, 5 A spatial pocket contacts, AlphaFold pLDDT order/disorder, True Path Rule DAG propagation deltas, and candidate compensatory/tolerated mutations from the DMS scan.",
            "student": "Write for a B.Tech / M.Sc Bioinformatics & Biotechnology student. Explain clearly what the amino acid substitution does chemically, how ESM2 LLR and Gene Ontology True Path DAG propagation work, and include 2 short self-check viva questions based on these exact results.",
        }[mode]

        system_prompt = (
            f"You are the Explainable AI (XAI) Scientific Co-Pilot for ProteinLens-OS deployed at {institution_name}. "
            f"{role_instructions} "
            "STRICT GROUNDING RULE: Cite ONLY the exact numbers, GO terms, LLR values, pLDDT scores, ClinVar statuses, and drug names present in the provided JSON evidence packet. Do NOT invent scores, citations, or clinical claims. "
            "Respond strictly as a JSON object with keys: "
            "'headline' (string), 'executive_summary' (string), 'structural_mechanism' (string), "
            "'functional_ontology_impact' (string), 'therapeutic_and_actionable_next_steps' (string), "
            "'key_citations' (list of short evidence strings)."
        )
        user_content = f"Grounded Evidence Packet:\n{json.dumps(evidence_packet, indent=2)[:7000]}"

        try:
            async with httpx.AsyncClient(timeout=28.0) as client:
                raw_text = ""
                if self.provider == "gemini" and self.api_key:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
                    resp = await client.post(
                        url,
                        json={
                            "systemInstruction": {"parts": [{"text": system_prompt}]},
                            "contents": [{"parts": [{"text": user_content}]}],
                            "generationConfig": {"responseMimeType": "application/json", "temperature": 0.2},
                        },
                    )
                    resp.raise_for_status()
                    raw_text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]

                elif self.provider == "grok" and self.api_key:
                    resp = await client.post(
                        "https://api.x.ai/v1/chat/completions",
                        headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                        json={
                            "model": self.model_name,
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_content},
                            ],
                            "temperature": 0.2,
                            "response_format": {"type": "json_object"},
                        },
                    )
                    resp.raise_for_status()
                    raw_text = resp.json()["choices"][0]["message"]["content"]

                elif self.provider == "groq" and self.api_key:
                    resp = await client.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                        json={
                            "model": self.model_name,
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_content},
                            ],
                            "temperature": 0.2,
                            "response_format": {"type": "json_object"},
                        },
                    )
                    resp.raise_for_status()
                    raw_text = resp.json()["choices"][0]["message"]["content"]

                elif self.provider == "ollama":
                    resp = await client.post(
                        f"{self.ollama_url}/api/chat",
                        json={
                            "model": self.model_name,
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_content},
                            ],
                            "format": "json",
                            "stream": False,
                        },
                    )
                    resp.raise_for_status()
                    raw_text = resp.json()["message"]["content"]

                if raw_text:
                    cleaned = raw_text.strip()
                    if cleaned.startswith("```"):
                        cleaned = cleaned.strip("`")
                        if cleaned.startswith("json"):
                            cleaned = cleaned[4:]
                    parsed = json.loads(cleaned.strip())
                    return {
                        "headline": str(parsed.get("headline", "Grounded Explainable AI Briefing")),
                        "executive_summary": str(parsed.get("executive_summary", "")),
                        "structural_mechanism": str(parsed.get("structural_mechanism", "")),
                        "functional_ontology_impact": str(parsed.get("functional_ontology_impact", "")),
                        "therapeutic_and_actionable_next_steps": str(parsed.get("therapeutic_and_actionable_next_steps", "")),
                        "key_citations": list(parsed.get("key_citations", [])),
                    }
        except Exception as exc:
            self.last_error = f"LLM synthesis fallback triggered: {exc}"
            return None
        return None

    @staticmethod
    def _deterministic_synthesis(
        evidence: Dict[str, Any],
        mode: str,
        institution_name: str,
    ) -> Dict[str, Any]:
        protein = evidence.get("protein_name") or evidence.get("uniprot_id") or "Target Protein"
        seq_len = evidence.get("sequence_length", 0)
        mf = evidence.get("top_mf", [])
        bp = evidence.get("top_bp", [])
        cc = evidence.get("top_cc", [])
        dag_audit = evidence.get("dag_audit", {})
        variant = evidence.get("variant")
        clinvar = evidence.get("clinvar", {})
        drugs = evidence.get("drugs", [])

        mf_str = ", ".join(f"{x['name']} ({x['score']*100:.1f}%)" for x in mf[:3]) or "broad molecular binding"
        bp_str = ", ".join(f"{x['name']} ({x['score']*100:.1f}%)" for x in bp[:3]) or "cellular homeostasis"
        cc_str = ", ".join(f"{x['name']} ({x['score']*100:.1f}%)" for x in cc[:2]) or "intracellular space"

        citations = [
            f"ProteinLens-OS ESM2 Backbone ({seq_len} aa) — {institution_name}",
            f"True Path DAG Audit: {dag_audit.get('violations_before', 0)} raw violations -> {dag_audit.get('violations_after', 0)} post-repair ({dag_audit.get('terms_repaired', 0)} ancestor terms elevated)",
        ]

        if variant:
            mut = variant.get("mutation", "Variant")
            da = variant.get("dual_axis_assessment", {})
            pocket = variant.get("structural_pocket", {})
            llr = da.get("evolutionary_llr", 0.0)
            comp = da.get("composite_risk_score", 0.0)
            tier = da.get("risk_tier", "Evaluated")
            plddt = pocket.get("target_plddt")
            n_5a = pocket.get("all_5A_contact_count", 0)
            citations.append(f"ESM2 Masked-Marginal LLR({mut}) = {llr:.2f}; Dual-Axis Risk = {comp:.1f}/100")
            if plddt is not None:
                citations.append(f"AlphaFold 3D Microenvironment: pLDDT = {plddt:.1f}, {n_5a} heavy-atom contacts within 5.0 A")
            if clinvar.get("matched"):
                citations.append(f"NCBI ClinVar Concordance: {clinvar.get('summary_classification')}")

            headline = f"{protein} ({mut}): {tier} [Composite Risk {comp:.1f}/100]"
            exec_sum = (
                f"Dual-axis computational triage of {protein} variant {mut} yields a Composite Risk Score of {comp:.1f}/100 "
                f"({tier}; {da.get('acmg_computational_cue', '')}). Zero-shot ESM2 Masked-Marginal evolutionary log-likelihood ratio "
                f"is {llr:.2f} (conservation index {da.get('conservation_index', 0):.2f}), paired with an Information-Accretion weighted "
                f"GO Functional Disruption Index (FDI) of {da.get('fdi_score', 0):.2f}."
            )
            struct_mech = (
                f"In the AlphaFold 3D tertiary scaffold, residue {variant.get('position')} ({variant.get('wt_aa')}) sits in a "
                f"{pocket.get('structural_region', 'structural region')} with pLDDT={plddt if plddt is not None else 'N/A'} and "
                f"{n_5a} direct heavy-atom contacting neighbors within 5.0 A ({pocket.get('burial_contacts_8A', 0)} CA contacts within 8.0 A). "
                "The batched 3D-pocket Deep Mutational Scan maps tolerance vs. deleterious sensitivity across all 20 canonical amino acids."
            )
        else:
            headline = f"{protein}: Multi-Modal Functional & Structural Profile ({seq_len} aa)"
            exec_sum = (
                f"Evolutionary language model analysis of {protein} ({seq_len} aa, ~{seq_len*0.11:.1f} kDa) identifies primary "
                f"molecular functions in {mf_str}, orchestrating biological processes including {bp_str}."
            )
            struct_mech = (
                f"Subcellular localization is predominantly mapped to {cc_str}. Multi-layer ESM2 Attention Rollout isolates peak "
                "structural/catalytic hotspot residues overlaid directly onto the AlphaFold 3D coordinate scaffold."
            )

        func_impact = (
            f"Top Gene Ontology annotations span Molecular Function ({mf_str}), Biological Process ({bp_str}), and Cellular Component ({cc_str}). "
            f"Fixed-point True Path Rule propagation repaired {dag_audit.get('terms_repaired', 0)} ancestral probabilities, reducing ontology "
            f"monotonicity contradictions from {dag_audit.get('violations_before', 0)} to 0."
        )

        if drugs:
            drug_names = ", ".join(f"{d['name']} (Phase {d['phase']})" for d in drugs[:4])
            citations.append(f"Open Targets Therapeutics: {drug_names}")
            action_text = (
                f"Open Targets identifies active therapeutic modalities targeting this protein: {drug_names}. "
                + (
                    "For educational/lab use: compare the wild-type vs. mutated 5 A pocket heatmap and verify how True Path DAG propagation enforces monotonic parent scores."
                    if mode == "student"
                    else "Recommended next step: prioritize high-risk VUS candidates for targeted functional assay validation. (Research Use Only — not a standalone clinical diagnostic.)"
                )
            )
        else:
            action_text = (
                "Configure a Gemini or xAI Grok API key in Settings for live natural-language Q&A synthesis. "
                + (
                    "Viva Tip: Explain why ESM2 Masked-Marginal LLR captures evolutionary constraint without requiring MSA alignments."
                    if mode == "student"
                    else "Recommended next step: export the SHA-256 JSON Audit Dossier or run Batch Cohort Triage across patient variants. (Research Use Only.)"
                )
            )

        return {
            "headline": headline,
            "executive_summary": exec_sum,
            "structural_mechanism": struct_mech,
            "functional_ontology_impact": func_impact,
            "therapeutic_and_actionable_next_steps": action_text,
            "key_citations": citations,
        }
