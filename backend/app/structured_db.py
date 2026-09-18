"""
Structured knowledge store: healthy-range norms per metric per biome.
This is what lets the system say "0.3% SOC is critically low for
semi-arid cropland" instead of guessing — Section 3.2 of the architecture doc.

SQLite for zero-setup; swap for Postgres later without changing the interface.
"""
import sqlite3
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).parent / "norms.db"

NORMS = [
    # metric, biome, low, high, degraded_below, unit, source
    ("soil_organic_carbon_pct", "semi-arid", 1.0, 2.5, 0.5, "%", "FAO Global Soil Partnership, Soil Organic Carbon Mapping (2020)"),
    ("soil_organic_carbon_pct", "arid", 0.5, 1.5, 0.3, "%", "FAO Global Soil Partnership, Soil Organic Carbon Mapping (2020)"),
    ("soil_organic_carbon_pct", "tropical", 2.0, 4.0, 1.0, "%", "FAO Global Soil Partnership (2020)"),
    ("soil_organic_carbon_pct", "temperate", 1.5, 3.5, 0.8, "%", "FAO Global Soil Partnership (2020)"),
    ("soil_ph", "semi-arid", 6.5, 8.0, None, "pH", "FAO Soil Portal, Soil pH Guidelines"),
    ("soil_ph", "tropical", 5.0, 6.5, None, "pH", "FAO Soil Portal, Soil pH Guidelines"),
    ("soil_moisture_pct", "semi-arid", 15.0, 30.0, 10.0, "%", "FAO AQUASTAT regional soil moisture baselines"),
    ("soil_moisture_pct", "arid", 5.0, 15.0, 3.0, "%", "FAO AQUASTAT regional soil moisture baselines"),
    ("species_richness_index", "semi-arid", 0.4, 0.7, 0.25, "index(0-1)", "IUCN Red List Index regional baselines"),
    ("species_richness_index", "tropical", 0.6, 0.9, 0.4, "index(0-1)", "IUCN Red List Index regional baselines"),
    ("pollution_index", "semi-arid", 0.0, 30.0, None, "index(0-100)", "UNEP Environmental Pollution Index methodology"),
    ("deforestation_rate_pct_per_yr", "tropical", 0.0, 0.5, 1.0, "%/yr", "FAO Global Forest Resources Assessment 2020"),
]


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS norms (
            metric TEXT, biome TEXT, healthy_low REAL, healthy_high REAL,
            degraded_below REAL, unit TEXT, source TEXT
        )
    """)
    conn.execute("DELETE FROM norms")
    conn.executemany("INSERT INTO norms VALUES (?,?,?,?,?,?,?)", NORMS)
    conn.commit()
    conn.close()


def get_norm(metric: str, biome: Optional[str]) -> Optional[dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM norms WHERE metric=? AND biome=?", (metric, biome)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def diagnose_metric(metric: str, value: float, biome: Optional[str]) -> str:
    """Returns 'degraded' | 'healthy' | 'above_normal' | 'unknown' against biome norms."""
    norm = get_norm(metric, biome)
    if not norm:
        return "unknown"
    if norm["degraded_below"] is not None and value < norm["degraded_below"]:
        return "degraded"
    if value < norm["healthy_low"]:
        return "below_normal"
    if value > norm["healthy_high"]:
        return "above_normal"
    return "healthy"


if __name__ == "__main__":
    init_db()
    print("norms.db initialized with", len(NORMS), "rows")
