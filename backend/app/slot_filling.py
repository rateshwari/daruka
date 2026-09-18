"""
Conversation Layer — slot-filling and clarification, Section 5 of the
architecture doc. The chatbot never free-associates about missing data;
it always routes to a specific clarification question chosen by which
missing slot unlocks the most rule-graph nodes.
"""
from __future__ import annotations
from typing import Dict, List, Optional
from .schemas import EnvironmentalInput
from .rule_graph import RULE_NODES

MIN_SLOTS_REQUIRED = 3

# Priority order: fields that gate the most rule nodes get asked first.
SLOT_PRIORITY = [
    "soil_organic_carbon_pct", "land_use", "rainfall_pattern",
    "region_biome", "species_richness_index", "soil_moisture_pct",
    "pollution_index", "deforestation_rate_pct_per_yr", "soil_ph",
]

SLOT_QUESTIONS = {
    "soil_organic_carbon_pct": "What's the soil organic carbon percentage (SOC %) for this land, if you know it?",
    "land_use": "What's the current land use — e.g. monoculture, polyculture, agroforestry, grassland, forest, wetland?",
    "rainfall_pattern": "How would you describe the rainfall pattern — low, moderate, high, or erratic?",
    "region_biome": "What biome/region type is this — semi-arid, arid, tropical, temperate, or Mediterranean?",
    "species_richness_index": "Do you have any estimate of species richness or biodiversity index (0-1) for the area?",
    "soil_moisture_pct": "What's the approximate soil moisture percentage?",
    "pollution_index": "Is there a known pollution index or runoff concern nearby (0-100 scale)?",
    "deforestation_rate_pct_per_yr": "Is there a known deforestation rate (% per year) for the region?",
    "soil_ph": "What's the soil pH, if measured?",
}


def missing_slots(filled: Dict) -> List[str]:
    return [s for s in SLOT_PRIORITY if filled.get(s) is None]


def has_enough_slots(filled: Dict) -> bool:
    non_null = [k for k in SLOT_PRIORITY if filled.get(k) is not None]
    return len(non_null) >= MIN_SLOTS_REQUIRED


def next_clarification(filled: Dict) -> Optional[str]:
    """Pick the missing slot that gates the most rule nodes, so the
    question asked is the one most likely to unlock a diagnosis."""
    missing = missing_slots(filled)
    if not missing:
        return None

    def gate_count(slot):
        return sum(1 for node in RULE_NODES if any(f == slot for f, _, _ in node["trigger"]))

    missing.sort(key=gate_count, reverse=True)
    top = missing[0]
    return SLOT_QUESTIONS.get(top, f"Can you provide {top}?")


def extract_slots_from_text(text: str, llm_extract_fn) -> Dict:
    """Delegates free-text -> structured slot extraction to an LLM call
    (see llm_generator.extract_structured_fields), constrained to only the
    fields defined in EnvironmentalInput. Never invents values not present
    in the text — the LLM extraction prompt enforces 'null if not stated'."""
    return llm_extract_fn(text)
