export interface ImpactedMetric {
  metric: string;
  expected_change: string;
  direction: "positive" | "negative" | "neutral";
}

export interface Recommendation {
  recommendation: string;
  reasoning: string;
  impacted_metrics: ImpactedMetric[];
  time_horizon: "short-term" | "medium-term" | "long-term";
  confidence: "High" | "Medium" | "Low";
  confidence_breakdown: string;
  trade_offs?: string | null;
  rejected_alternatives?: string[] | null;
  sources: string[];
  rule_node_id: string;
}

export interface EnvironmentalInput {
  soil_organic_carbon_pct?: number | null;
  soil_ph?: number | null;
  soil_moisture_pct?: number | null;
  land_use?: string | null;
  rainfall_pattern?: string | null;
  region_biome?: string | null;
  pollution_index?: number | null;
  deforestation_rate_pct_per_yr?: number | null;
  species_richness_index?: number | null;
  lat?: number | null;
  lon?: number | null;
}

export interface SystemResponse {
  session_id: string;
  reply_text: string;
  clarification_needed: boolean;
  missing_slots: string[];
  recommendations: Recommendation[];
  filled_input?: EnvironmentalInput | null;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  recommendations?: Recommendation[];
}
