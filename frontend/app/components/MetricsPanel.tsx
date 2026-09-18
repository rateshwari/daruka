import { EnvironmentalInput } from "../../lib/types";

const SLOT_LABELS: Record<string, string> = {
  soil_organic_carbon_pct: "Soil organic carbon (%)",
  soil_ph: "Soil pH",
  soil_moisture_pct: "Soil moisture (%)",
  land_use: "Land use",
  rainfall_pattern: "Rainfall pattern",
  region_biome: "Region biome",
  pollution_index: "Pollution index",
  deforestation_rate_pct_per_yr: "Deforestation rate (%/yr)",
  species_richness_index: "Species richness index",
};

export default function MetricsPanel({
  filled,
  onGeoChange,
}: {
  filled?: EnvironmentalInput | null;
  onGeoChange?: (field: "lat" | "lon", value: number) => void;
}) {
  const data = filled || {};
  return (
    <div className="w-72 shrink-0 border-r border-neutral-800 p-4 space-y-3 overflow-y-auto">
      <h2 className="text-sm font-semibold text-neutral-400 uppercase tracking-wide">
        Metrics
      </h2>
      <ul className="space-y-2">
        {Object.entries(SLOT_LABELS).map(([key, label]) => {
          const value = (data as Record<string, unknown>)[key];
          const filledIn = value !== undefined && value !== null;
          return (
            <li
              key={key}
              className={`flex items-center justify-between text-xs rounded-lg px-2 py-2 border ${
                filledIn
                  ? "border-emerald-700/50 bg-emerald-900/10 text-emerald-200"
                  : "border-neutral-800 text-neutral-500"
              }`}
            >
              <span>{label}</span>
              <span>{filledIn ? String(value) : "—"}</span>
            </li>
          );
        })}
      </ul>
      <div className="pt-3 border-t border-neutral-800">
        <h3 className="text-xs text-neutral-500 mb-2">Geo-coordinates (optional)</h3>
        <div className="flex gap-2">
          <input
            type="number"
            placeholder="lat"
            className="w-1/2 text-xs bg-neutral-900 border border-neutral-800 rounded px-2 py-1"
            onChange={(e) => onGeoChange?.("lat", parseFloat(e.target.value))}
          />
          <input
            type="number"
            placeholder="lon"
            className="w-1/2 text-xs bg-neutral-900 border border-neutral-800 rounded px-2 py-1"
            onChange={(e) => onGeoChange?.("lon", parseFloat(e.target.value))}
          />
        </div>
      </div>
    </div>
  );
}