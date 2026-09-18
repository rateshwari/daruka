"""
Builds the Output Contract (Section 7) from a fired rule node + retrieved
evidence. Confidence scoring (Section 4.3 / 10) combines source agreement
count, source recency, and whether biome-specific norms were available.
"""
from __future__ import annotations
from typing import List, Dict, Any
import re
from .vector_store import get_store
from .structured_db import get_norm
from . import llm_generator


def _confidence(sources: List[dict], biome_matched: bool) -> tuple[str, str]:
    n = len(sources)
    years = []
    for s in sources:
        m = re.search(r"\((\d{4})\)", s["source"])
        if m:
            years.append(int(m.group(1)))
    recent = any(y >= 2020 for y in years) if years else False

    score = 0
    score += 2 if n >= 3 else (1 if n >= 1 else 0)
    score += 1 if recent else 0
    score += 1 if biome_matched else 0

    if score >= 4:
        level = "High"
    elif score >= 2:
        level = "Medium"
    else:
        level = "Low"

    breakdown = (
        f"{n} independent source(s) agree" +
        (", at least one recent (2020+)" if recent else ", no recent source confirmed") +
        (", biome-matched norms available" if biome_matched else ", biome norms unavailable/general fallback")
    )
    return level, breakdown


def build_recommendation(node: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
    biome = input_data.get("region_biome")
    primary = node["primary_intervention"]
    effects = node["cross_metric_effects"].get(primary, [])
    relevant_metrics = [e["metric"] for e in effects] or list(node["cross_metric_effects"].keys())

    store = get_store()
    query = f"{node['diagnosis']} intervention: {primary}"
    retrieved = store.retrieve(query, relevant_metrics=relevant_metrics, biome=biome, k=3)

    biome_matched = any(get_norm(m, biome) for m in relevant_metrics)
    confidence, breakdown = _confidence(retrieved, biome_matched)

    rec = {
        "recommendation": primary.replace("_", " ").title(),
        "reasoning": node["diagnosis"],
        "impacted_metrics": effects,
        "time_horizon": node["time_horizon"],
        "confidence": confidence,
        "confidence_breakdown": breakdown,
        "trade_offs": node.get("trade_offs"),
        "rejected_alternatives": node.get("rejected_alternatives") or None,
        "sources": [r["source"] for r in retrieved],
        "rule_node_id": node["id"],
    }
    rec["reply_text"] = llm_generator.render_recommendation_prose(rec)
    return rec
