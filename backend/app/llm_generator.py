"""
The ONLY place the LLM is called. Two jobs, both constrained:
  1. extract_structured_fields — free text -> EnvironmentalInput fields, null if absent
  2. render_recommendation_prose — turn an already-fully-formed Recommendation
     (facts, figures, sources already decided by rule_graph.py + vector_store.py)
     into natural language.

The LLM is NEVER asked to invent a number, a study, or a causal claim.
If ANTHROPIC_API_KEY is not set, deterministic template fallbacks are used
so the whole pipeline still runs end-to-end without a key during setup.
"""
from __future__ import annotations
import json
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

try:
    import openai
    _client = anthropic.Anthropic() if os.getenv("ANTHROPIC_API_KEY") else None
except Exception:
    _client = None

EXTRACTION_FIELDS = [
    "soil_organic_carbon_pct", "soil_ph", "soil_moisture_pct", "land_use",
    "rainfall_pattern", "region_biome", "pollution_index",
    "deforestation_rate_pct_per_yr", "species_richness_index",
]


def extract_structured_fields(user_text: str) -> dict:
    if _client is None:
        return _naive_extract(user_text)

    prompt = f"""Extract ONLY the following fields from the user's message if explicitly
stated or clearly implied. Use null for anything not stated — never guess or infer
a number that wasn't given. Return ONLY valid JSON, no other text.

Fields: {EXTRACTION_FIELDS}
Allowed land_use values: monoculture, polyculture, agroforestry, fallow, grassland, forest, urban, wetland
Allowed rainfall_pattern values: low, moderate, high, erratic
Allowed region_biome values: semi-arid, arid, tropical, temperate, mediterranean

User message: "{user_text}"

JSON:"""
    resp = _client.messages.create(
        model="",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = "".join(b.text for b in resp.content if b.type == "text")
    raw = raw.strip().strip("```json").strip("```").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return _naive_extract(user_text)


def _naive_extract(text: str) -> dict:
    """Fallback keyword-based extraction so the pipeline runs with no API key."""
    t = text.lower()
    out = {f: None for f in EXTRACTION_FIELDS}
    for lu in ["monoculture", "polyculture", "agroforestry", "fallow", "grassland", "forest", "urban", "wetland"]:
        if lu in t:
            out["land_use"] = lu
    for rf in ["low", "moderate", "high", "erratic"]:
        if f"{rf} rainfall" in t or f"rainfall is {rf}" in t or f"rainfall: {rf}" in t:
            out["rainfall_pattern"] = rf
    for biome in ["semi-arid", "arid", "tropical", "temperate", "mediterranean"]:
        if biome in t and out["region_biome"] is None:
            out["region_biome"] = biome
    import re
    m = re.search(r"(soil organic carbon|soc)[^\d]*(\d+\.?\d*)\s*%", t)
    if m:
        out["soil_organic_carbon_pct"] = float(m.group(2))
    m = re.search(r"ph[^\d]*(\d+\.?\d*)", t)
    if m:
        out["soil_ph"] = float(m.group(1))
    return out


def render_recommendation_prose(recommendation_json: dict) -> str:
    """Turns an already-fully-decided recommendation dict into a natural
    paragraph. Explicitly instructed not to add facts beyond what's given."""
    if _client is None:
        return _template_render(recommendation_json)

    prompt = f"""Rewrite the following structured recommendation as a clear,
natural-sounding paragraph for a farmer/land manager. Do NOT add any new
facts, numbers, or claims beyond what is given below — only rephrase for
clarity and warmth.

{json.dumps(recommendation_json, indent=2)}
"""
    resp = _client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(b.text for b in resp.content if b.type == "text").strip()


def _template_render(rec: dict) -> str:
    metrics_line = "; ".join(
        f"{m['metric']} ({m['expected_change']})" for m in rec["impacted_metrics"]
    )
    tradeoff = f" Note: {rec['trade_offs']}" if rec.get("trade_offs") else ""
    return (
        f"{rec['recommendation']}. {rec['reasoning']} "
        f"Expected effects: {metrics_line}.{tradeoff} "
        f"Time horizon: {rec['time_horizon']}. Confidence: {rec['confidence']}."
    )
