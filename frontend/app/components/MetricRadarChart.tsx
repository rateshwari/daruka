"use client";
import {
  Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer,
} from "recharts";
import { EnvironmentalInput } from "../../lib/types";

// Rough 0-1 normalization against typical healthy ranges, purely for the
// visual — the real diagnosis comes from the backend's structured_db norms.
function normalize(key: string, value?: number | null): number {
  if (value === undefined || value === null) return 0;
  const ranges: Record<string, [number, number]> = {
    soil_organic_carbon_pct: [0, 3],
    soil_ph: [4, 9],
    soil_moisture_pct: [0, 40],
    pollution_index: [0, 100],
    species_richness_index: [0, 1],
    deforestation_rate_pct_per_yr: [0, 3],
  };
  const [lo, hi] = ranges[key] || [0, 1];
  return Math.max(0, Math.min(1, (value - lo) / (hi - lo)));
}

export default function MetricRadarChart({ filled }: { filled?: EnvironmentalInput | null }) {
  const data = [
    { metric: "SOC", value: normalize("soil_organic_carbon_pct", filled?.soil_organic_carbon_pct) },
    { metric: "pH", value: normalize("soil_ph", filled?.soil_ph) },
    { metric: "Moisture", value: normalize("soil_moisture_pct", filled?.soil_moisture_pct) },
    { metric: "Species richness", value: normalize("species_richness_index", filled?.species_richness_index) },
    { metric: "Low pollution", value: 1 - normalize("pollution_index", filled?.pollution_index) },
    { metric: "Low deforest.", value: 1 - normalize("deforestation_rate_pct_per_yr", filled?.deforestation_rate_pct_per_yr) },
  ];

  return (
    <div className="h-56 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart data={data} outerRadius="55%" cx="50%" cy="50%">
          <PolarGrid stroke="#3f3f46" />
          <PolarAngleAxis dataKey="metric" tick={{ fill: "#a1a1aa", fontSize: 9 }} tickSize={4} />
          <PolarRadiusAxis domain={[0, 1]} tick={false} axisLine={false} />
          <Radar dataKey="value" stroke="#34d399" fill="#34d399" fillOpacity={0.3} />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
