"""
Static lat/lon bounding-box -> biome lookup. No external GIS service —
good enough for a hackathon demo. ~20 regions covering common biomes.
Extend with more boxes if your demo needs a specific region covered.
"""
from typing import Optional

# (lat_min, lat_max, lon_min, lon_max, biome)
REGIONS = [
    (8.0, 37.0, 68.0, 90.0, "tropical"),        # South/SE Asia (India, SE Asia)
    (-10.0, 10.0, -80.0, -35.0, "tropical"),     # Amazon basin
    (-10.0, 10.0, 10.0, 40.0, "tropical"),       # Central Africa
    (15.0, 30.0, -20.0, 55.0, "arid"),           # Sahara / Arabian desert belt
    (20.0, 35.0, 60.0, 80.0, "semi-arid"),       # Central/South Asia dryland
    (30.0, 45.0, -10.0, 40.0, "mediterranean"),  # Mediterranean basin
    (35.0, 55.0, -10.0, 40.0, "temperate"),      # Western/Central Europe
    (35.0, 55.0, -100.0, -70.0, "temperate"),    # Eastern North America
    (-45.0, -20.0, 110.0, 155.0, "arid"),        # Australian interior
    (-40.0, -10.0, -75.0, -50.0, "temperate"),   # Southern South America
]


def lookup_biome(lat: float, lon: float) -> Optional[str]:
    for lat_min, lat_max, lon_min, lon_max, biome in REGIONS:
        if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
            return biome
    return None