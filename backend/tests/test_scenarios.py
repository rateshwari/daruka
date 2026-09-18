"""
Regression test set — Section 10 of the architecture doc.
Encodes known input scenarios with their expected rule-node firings.
Run before every demo to catch silent regressions (this exact style of
test would have caught the region_biome-overwrite bug we hit while
wiring the geo-lookup feature) before a judge does.

Run: cd backend && pytest tests/test_scenarios.py -v
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

SCENARIOS = [
    {
        "name": "brief_example_semi_arid_monoculture",
        "data": {
            "soil_organic_carbon_pct": 0.3,
            "rainfall_pattern": "low",
            "land_use": "monoculture",
            "region_biome": "semi-arid",
        },
        "expected_nodes": {"node_low_soc_monoculture_dry", "node_reduced_till_dry"},
    },
    {
        "name": "alkaline_soil",
        "data": {"soil_ph": 9.0},
        "expected_nodes": {"node_alkaline_ph_imbalance"},
    },
    {
        "name": "species_decline_with_pollution",
        "data": {"species_richness_index": 0.3, "pollution_index": 45},
        "expected_nodes": {"node_pollution_water_proximity", "node_species_decline_pollution"},
    },
    {
        "name": "waterlogged_field",
        "data": {"soil_moisture_pct": 40},
        "expected_nodes": {"node_waterlogging_excess_moisture"},
    },
    {
        "name": "erratic_rainfall_low_carbon",
        "data": {"rainfall_pattern": "erratic", "soil_organic_carbon_pct": 0.7},
        "expected_nodes": {"node_erratic_rainfall_low_soc"},
    },
    {
        "name": "temperate_deforestation",
        "data": {"region_biome": "temperate", "deforestation_rate_pct_per_yr": 0.8},
        "expected_nodes": {"node_temperate_deforestation"},
    },
    {
        "name": "severe_compound_degradation",
        "data": {"soil_organic_carbon_pct": 0.2, "pollution_index": 60, "land_use": "monoculture"},
        "expected_nodes": {"node_pollution_water_proximity", "node_severe_compound_degradation"},
    },
    {
        "name": "healthy_land_no_trigger",
        "data": {
            "soil_organic_carbon_pct": 2.0,
            "soil_ph": 6.8,
            "land_use": "agroforestry",
            "rainfall_pattern": "moderate",
            "region_biome": "temperate",
        },
        "expected_nodes": set(),  # nothing should fire on healthy inputs
    },
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=[s["name"] for s in SCENARIOS])
def test_scenario_fires_expected_nodes(scenario):
    resp = client.post("/diagnose", json={
        "session_id": f"regtest-{scenario['name']}",
        "data": scenario["data"],
    })
    assert resp.status_code == 200, resp.text
    body = resp.json()
    fired = {r["rule_node_id"] for r in body["recommendations"]}
    assert fired == scenario["expected_nodes"], (
        f"{scenario['name']}: expected {scenario['expected_nodes']}, got {fired}"
    )


def test_geo_lookup_fills_biome_when_absent():
    resp = client.post("/diagnose", json={
        "session_id": "regtest-geo",
        "data": {"lat": 19.07, "lon": 72.87},
    })
    assert resp.status_code == 200
    assert resp.json()["filled_input"]["region_biome"] == "tropical"


def test_explicit_biome_overrides_geo_lookup():
    resp = client.post("/diagnose", json={
        "session_id": "regtest-geo-override",
        "data": {"lat": 19.07, "lon": 72.87, "region_biome": "arid"},
    })
    assert resp.status_code == 200
    assert resp.json()["filled_input"]["region_biome"] == "arid"


def test_clarification_fires_on_converse_with_fewer_than_3_slots():
    """/converse (free text) should still ask clarifying questions below
    the 3-slot minimum -- only /diagnose (deliberate structured input)
    skips that gate."""
    resp = client.post("/converse", json={
        "session_id": "regtest-clarify-converse",
        "message": "Soil organic carbon is 0.3%.",
    })
    body = resp.json()
    assert body["clarification_needed"] is True
    assert len(body["recommendations"]) == 0


def test_diagnose_reasons_immediately_even_with_1_slot():
    """/diagnose should NOT ask for clarification -- deliberate structured
    input reasons immediately, which is the whole point of the fix."""
    resp = client.post("/diagnose", json={
        "session_id": "regtest-diagnose-1-slot",
        "data": {"soil_ph": 9.0},
    })
    body = resp.json()
    assert body["clarification_needed"] is False
    assert {r["rule_node_id"] for r in body["recommendations"]} == {"node_alkaline_ph_imbalance"}