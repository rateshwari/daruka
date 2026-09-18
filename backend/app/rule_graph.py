"""
Multi-metric reasoning engine — Section 4 of the architecture doc.
This is deterministic, not an LLM prompt: each node's trigger is checked
against the filled input, and multiple triggers can fire simultaneously,
which is how the system guarantees multi-metric combination structurally
rather than hoping the LLM doesn't drop a variable.
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional
from .structured_db import diagnose_metric

OP_FUNCS = {
    "<": lambda a, b: a is not None and a < b,
    "<=": lambda a, b: a is not None and a <= b,
    ">": lambda a, b: a is not None and a > b,
    ">=": lambda a, b: a is not None and a >= b,
    "==": lambda a, b: a == b,
}

# Each node: trigger conditions (ALL must hold on present fields; a field
# absent from the input simply doesn't block the trigger unless required=True),
# a diagnosis, candidate interventions, per-intervention cross-metric effects,
# trade-offs, and explicitly rejected alternatives with the reason (used for
# the counterfactual UI element in Section 10).
RULE_NODES: List[Dict[str, Any]] = [
    {
        "id": "node_low_soc_monoculture_dry",
        "trigger": [
            ("soil_organic_carbon_pct", "<", 0.5),
            ("land_use", "==", "monoculture"),
            ("rainfall_pattern", "==", "low"),
        ],
        "diagnosis": "Low soil organic carbon combined with monoculture under water stress compounds erosion risk and habitat simplification.",
        "candidate_interventions": ["agroforestry_intercropping", "legume_cover_crop"],
        "primary_intervention": "agroforestry_intercropping",
        "cross_metric_effects": {
            "agroforestry_intercropping": [
                {"metric": "soil_organic_carbon_pct", "expected_change": "+15-25% over 2-3 years", "direction": "positive"},
                {"metric": "species_richness_index", "expected_change": "increase via canopy/pollinator niches", "direction": "positive"},
                {"metric": "soil_moisture_pct", "expected_change": "improved retention, 1-3°C canopy cooling", "direction": "positive"},
            ]
        },
        "trade_offs": "Primary crop yield typically drops 10-15% in year 1 due to light/resource competition; recovers or exceeds baseline by year 3-5.",
        "rejected_alternatives": [
            "Irrigation alone was not recommended: it does not address the underlying soil organic carbon deficit and can accelerate salinization if not carefully managed.",
        ],
        "time_horizon": "medium-term",
    },
    {
        "id": "node_reduced_till_dry",
        "trigger": [
            ("soil_organic_carbon_pct", "<", 1.0),
            ("rainfall_pattern", "==", "low"),
        ],
        "diagnosis": "Low organic carbon under low rainfall reduces the soil's water-holding buffer, amplifying crop failure risk during dry spells.",
        "candidate_interventions": ["reduced_tillage", "legume_cover_crop"],
        "primary_intervention": "reduced_tillage",
        "cross_metric_effects": {
            "reduced_tillage": [
                {"metric": "soil_moisture_pct", "expected_change": "+10-20% retention vs. conventional tillage", "direction": "positive"},
                {"metric": "soil_organic_carbon_pct", "expected_change": "gradual increase via reduced disturbance", "direction": "positive"},
            ]
        },
        "trade_offs": "May require updated equipment or short-term weed management adjustment.",
        "rejected_alternatives": [],
        "time_horizon": "short-term",
    },
    {
        "id": "node_fragmentation_monoculture",
        "trigger": [
            ("land_use", "==", "monoculture"),
            ("species_richness_index", "<", 0.4),
        ],
        "diagnosis": "Continuous monoculture is driving habitat fragmentation and pollinator/bird species decline.",
        "candidate_interventions": ["land_use_diversification", "crop_rotation", "hedgerow_windbreak"],
        "primary_intervention": "crop_rotation",
        "cross_metric_effects": {
            "crop_rotation": [
                {"metric": "species_richness_index", "expected_change": "gradual increase via microbial and pest-cycle diversity", "direction": "positive"},
                {"metric": "soil_organic_carbon_pct", "expected_change": "modest increase", "direction": "positive"},
            ]
        },
        "trade_offs": "Requires planning across seasons; some rotation crops may have lower immediate market value.",
        "rejected_alternatives": [
            "Full land-use conversion to grassland was not recommended: too disruptive to livelihood given no indication the user wants to stop farming.",
        ],
        "time_horizon": "medium-term",
    },
    {
        "id": "node_deforestation_tropical",
        "trigger": [
            ("region_biome", "==", "tropical"),
            ("deforestation_rate_pct_per_yr", ">", 1.0),
        ],
        "diagnosis": "Deforestation rate above the regional threshold is driving rapid species richness decline through habitat loss.",
        "candidate_interventions": ["reforestation"],
        "primary_intervention": "reforestation",
        "cross_metric_effects": {
            "reforestation": [
                {"metric": "species_richness_index", "expected_change": "30-50% recovery of original richness over 15-20 years", "direction": "positive"},
                {"metric": "deforestation_rate_pct_per_yr", "expected_change": "halted/reversed in restored area", "direction": "positive"},
            ]
        },
        "trade_offs": "Long time horizon before full recovery; requires proximity to intact forest fragments for best results.",
        "rejected_alternatives": [],
        "time_horizon": "long-term",
    },
    {
        "id": "node_pollution_water_proximity",
        "trigger": [
            ("pollution_index", ">", 30),
        ],
        "diagnosis": "Elevated pollution index suggests agricultural runoff or particulate load is degrading nearby ecosystems.",
        "candidate_interventions": ["riparian_buffer", "hedgerow_windbreak"],
        "primary_intervention": "riparian_buffer",
        "cross_metric_effects": {
            "riparian_buffer": [
                {"metric": "pollution_index", "expected_change": "-30-60% runoff reaching water bodies", "direction": "positive"},
            ]
        },
        "trade_offs": "Takes land out of direct production along waterway edges.",
        "rejected_alternatives": [],
        "time_horizon": "short-term",
    },
    {
        "id": "node_low_moisture_arid",
        "trigger": [
            ("soil_moisture_pct", "<", 10),
            ("region_biome", "==", "arid"),
        ],
        "diagnosis": "Soil moisture below the degraded threshold for arid biomes limits both crop viability and native species survival.",
        "candidate_interventions": ["hedgerow_windbreak", "reduced_tillage"],
        "primary_intervention": "hedgerow_windbreak",
        "cross_metric_effects": {
            "hedgerow_windbreak": [
                {"metric": "soil_moisture_pct", "expected_change": "improved via reduced wind erosion", "direction": "positive"},
                {"metric": "pollution_index", "expected_change": "reduced airborne particulates", "direction": "positive"},
            ]
        },
        "trade_offs": "Establishment period of 2-3 years before windbreak is fully effective.",
        "rejected_alternatives": [
            "Heavy irrigation was not recommended as the primary fix: addresses symptom, not the wind-driven moisture loss mechanism.",
        ],
        "time_horizon": "medium-term",
    },
    {
        "id": "node_ph_imbalance",
        "trigger": [
            ("soil_ph", "<", 6.0),
        ],
        "diagnosis": "Soil pH below the healthy range limits nutrient availability and constrains microbial diversity, compounding any organic carbon deficit.",
        "candidate_interventions": ["composting"],
        "primary_intervention": "composting",
        "cross_metric_effects": {
            "composting": [
                {"metric": "soil_ph", "expected_change": "gradual buffering toward neutral range", "direction": "positive"},
                {"metric": "soil_organic_carbon_pct", "expected_change": "faster first-year increase than cover cropping alone", "direction": "positive"},
            ]
        },
        "trade_offs": "Gains are less durable long-term without a follow-on living-root strategy such as cover cropping.",
        "rejected_alternatives": [],
        "time_horizon": "short-term",
    },
    {
        "id": "node_wetland_opportunity",
        "trigger": [
            ("land_use", "==", "wetland"),
            ("species_richness_index", "<", 0.5),
        ],
        "diagnosis": "Degraded wetland edges represent a high-leverage restoration opportunity for amphibian and pollinator recovery.",
        "candidate_interventions": ["wetland_restoration"],
        "primary_intervention": "wetland_restoration",
        "cross_metric_effects": {
            "wetland_restoration": [
                {"metric": "species_richness_index", "expected_change": "measurable increase within 2-3 growing seasons", "direction": "positive"},
            ]
        },
        "trade_offs": "Requires hydrological assessment before intervention to avoid unintended drainage changes.",
        "rejected_alternatives": [],
        "time_horizon": "medium-term",
    },
    {
        "id": "node_alkaline_ph_imbalance",
        "trigger": [
            ("soil_ph", ">", 8.5),
        ],
        "diagnosis": "Soil pH above the healthy range reduces micronutrient (iron, zinc, manganese) availability and constrains microbial community diversity, particularly in low-rainfall biomes where salts concentrate.",
        "candidate_interventions": ["sulfur_amendment"],
        "primary_intervention": "sulfur_amendment",
        "cross_metric_effects": {
            "sulfur_amendment": [
                {"metric": "soil_ph", "expected_change": "gradual reduction toward neutral range over 1-2 seasons", "direction": "positive"},
                {"metric": "soil_organic_carbon_pct", "expected_change": "indirect improvement via better microbial activity", "direction": "positive"},
            ]
        },
        "trade_offs": "Effect is slow (months, not weeks) and depends on soil buffering capacity — retest pH before reapplying.",
        "rejected_alternatives": [
            "Heavy irrigation to flush salts was not recommended as a standalone fix: without a drainage outlet it can raise the water table and worsen salinization.",
        ],
        "time_horizon": "medium-term",
    },
    {
        "id": "node_species_decline_pollution",
        "trigger": [
            ("species_richness_index", "<", 0.4),
            ("pollution_index", ">", 30),
        ],
        "diagnosis": "Species richness decline co-occurring with elevated pollution index points to runoff or particulate contamination as a direct driver, not just habitat structure.",
        "candidate_interventions": ["riparian_buffer", "integrated_pest_management"],
        "primary_intervention": "riparian_buffer",
        "cross_metric_effects": {
            "riparian_buffer": [
                {"metric": "pollution_index", "expected_change": "-30-60% runoff reaching water bodies", "direction": "positive"},
                {"metric": "species_richness_index", "expected_change": "indirect recovery as water quality improves", "direction": "positive"},
            ]
        },
        "trade_offs": "Buffer strips remove a margin of land from direct production.",
        "rejected_alternatives": [
            "Broad-spectrum pesticide reduction alone was not the primary recommendation here: pollution index elevation suggests a runoff/water-quality pathway, not only an on-field chemical-use pathway.",
        ],
        "time_horizon": "short-term",
    },
    {
        "id": "node_waterlogging_excess_moisture",
        "trigger": [
            ("soil_moisture_pct", ">", 35),
        ],
        "diagnosis": "Soil moisture above the healthy range risks root-zone oxygen depletion and anaerobic microbial shifts, which can suppress both crop root health and soil biodiversity.",
        "candidate_interventions": ["drainage_management"],
        "primary_intervention": "drainage_management",
        "cross_metric_effects": {
            "drainage_management": [
                {"metric": "soil_moisture_pct", "expected_change": "reduced to healthy range within 1 season with proper channel design", "direction": "positive"},
                {"metric": "soil_organic_carbon_pct", "expected_change": "improved aerobic decomposition and microbial diversity", "direction": "positive"},
            ]
        },
        "trade_offs": "Poorly designed drainage can increase downstream nutrient runoff — pair with a riparian buffer if near a water body.",
        "rejected_alternatives": [],
        "time_horizon": "short-term",
    },
    {
        "id": "node_erratic_rainfall_low_soc",
        "trigger": [
            ("rainfall_pattern", "==", "erratic"),
            ("soil_organic_carbon_pct", "<", 1.0),
        ],
        "diagnosis": "Erratic rainfall combined with low organic carbon means the soil lacks the water-buffering capacity to smooth out dry-spell/downpour cycles, raising both drought and erosion risk in the same season.",
        "candidate_interventions": ["legume_cover_crop", "reduced_tillage"],
        "primary_intervention": "legume_cover_crop",
        "cross_metric_effects": {
            "legume_cover_crop": [
                {"metric": "soil_organic_carbon_pct", "expected_change": "+15-25% over 2-3 years", "direction": "positive"},
                {"metric": "soil_moisture_pct", "expected_change": "improved buffering against erratic rainfall swings", "direction": "positive"},
            ]
        },
        "trade_offs": "Cover crop establishment itself needs a reliable early-season watering window, which erratic rainfall can complicate in year 1.",
        "rejected_alternatives": [],
        "time_horizon": "medium-term",
    },
    {
        "id": "node_temperate_deforestation",
        "trigger": [
            ("region_biome", "==", "temperate"),
            ("deforestation_rate_pct_per_yr", ">", 0.5),
        ],
        "diagnosis": "Deforestation rate above the temperate-biome threshold is fragmenting remaining habitat faster than natural regeneration can offset, even though temperate forests recover somewhat faster than tropical ones.",
        "candidate_interventions": ["reforestation", "hedgerow_windbreak"],
        "primary_intervention": "reforestation",
        "cross_metric_effects": {
            "reforestation": [
                {"metric": "species_richness_index", "expected_change": "partial recovery over 10-15 years, faster than tropical equivalents", "direction": "positive"},
                {"metric": "deforestation_rate_pct_per_yr", "expected_change": "halted in restored area", "direction": "positive"},
            ]
        },
        "trade_offs": "Requires multi-year land commitment; near-term land productivity for grazing/cropping is reduced in restored zones.",
        "rejected_alternatives": [],
        "time_horizon": "long-term",
    },
    {
        "id": "node_severe_compound_degradation",
        "trigger": [
            ("soil_organic_carbon_pct", "<", 0.3),
            ("pollution_index", ">", 50),
            ("land_use", "==", "monoculture"),
        ],
        "diagnosis": "Critically low organic carbon combined with high pollution load and continuous monoculture indicates compounding degradation across soil, water, and habitat axes simultaneously — a single intervention is unlikely to be sufficient.",
        "candidate_interventions": ["agroforestry_intercropping", "riparian_buffer", "composting"],
        "primary_intervention": "agroforestry_intercropping",
        "cross_metric_effects": {
            "agroforestry_intercropping": [
                {"metric": "soil_organic_carbon_pct", "expected_change": "+15-25% over 2-3 years", "direction": "positive"},
                {"metric": "species_richness_index", "expected_change": "increase via canopy/pollinator niches", "direction": "positive"},
            ]
        },
        "trade_offs": "This is a severe multi-axis case — agroforestry alone will not resolve the pollution pathway; pair with a riparian buffer and composting for full recovery, and expect a multi-year program rather than a single fix.",
        "rejected_alternatives": [
            "A single-metric fix (e.g. composting alone) was not recommended as sufficient: the pollution and habitat axes need independent interventions running in parallel.",
        ],
        "time_horizon": "long-term",
    },
]


def evaluate(input_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Returns all rule nodes whose trigger conditions are fully satisfied
    by the present (non-None) fields in input_data. A node only fires if
    EVERY field it references is present AND satisfies the condition —
    this is what keeps the reasoning grounded in what was actually given."""
    fired = []
    for node in RULE_NODES:
        ok = True
        for field, op, value in node["trigger"]:
            actual = input_data.get(field)
            if actual is None:
                ok = False
                break
            if not OP_FUNCS[op](actual, value):
                ok = False
                break
        if ok:
            fired.append(node)
    return fired


def biome_diagnosis_summary(input_data: Dict[str, Any]) -> List[str]:
    """Uses the structured DB (norms) to label each present metric as
    degraded/healthy/etc. for the given biome — the pre-recommendation
    diagnosis step described in Section 3.2."""
    biome = input_data.get("region_biome")
    lines = []
    for metric in [
        "soil_organic_carbon_pct", "soil_ph", "soil_moisture_pct",
        "species_richness_index", "pollution_index", "deforestation_rate_pct_per_yr",
    ]:
        val = input_data.get(metric)
        if val is not None:
            status = diagnose_metric(metric, val, biome)
            lines.append(f"{metric}={val} -> {status} (biome: {biome or 'unspecified'})")
    return lines
