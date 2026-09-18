import { Recommendation } from "../../lib/types";

const confidenceColor: Record<string, string> = {
  High: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40",
  Medium: "bg-amber-500/20 text-amber-300 border-amber-500/40",
  Low: "bg-rose-500/20 text-rose-300 border-rose-500/40",
};

const horizonLabel: Record<string, string> = {
  "short-term": "Short-term",
  "medium-term": "Medium-term",
  "long-term": "Long-term",
};

export default function RecommendationCard({ rec }: { rec: Recommendation }) {
  return (
    <div className="rounded-xl border border-neutral-800 bg-neutral-900 p-4 space-y-3 max-w-xl">
      <div className="flex items-center justify-between gap-2">
        <h3 className="font-semibold text-neutral-100">{rec.recommendation}</h3>
        <span className={`text-xs px-2 py-1 rounded-full border ${confidenceColor[rec.confidence]}`}>
          {rec.confidence} confidence
        </span>
      </div>

      <p className="text-sm text-neutral-300">{rec.reasoning}</p>

      <div className="flex flex-wrap gap-2">
        {rec.impacted_metrics.map((m, i) => (
          <span
            key={i}
            className={`text-xs px-2 py-1 rounded-full border ${
              m.direction === "positive"
                ? "border-emerald-600 text-emerald-300"
                : m.direction === "negative"
                ? "border-rose-600 text-rose-300"
                : "border-neutral-600 text-neutral-300"
            }`}
          >
            {m.metric.replaceAll("_", " ")}: {m.expected_change}
          </span>
        ))}
      </div>

      {rec.trade_offs && (
        <p className="text-xs text-neutral-400 border-l-2 border-amber-600 pl-2">
          Trade-off: {rec.trade_offs}
        </p>
      )}

      {rec.rejected_alternatives && rec.rejected_alternatives.length > 0 && (
        <div className="text-xs text-neutral-500">
          {rec.rejected_alternatives.map((r, i) => (
            <p key={i}>Considered and rejected: {r}</p>
          ))}
        </div>
      )}

      <div className="flex items-center justify-between text-xs text-neutral-500 pt-2 border-t border-neutral-800">
        <span>{horizonLabel[rec.time_horizon]}</span>
        <span>{rec.confidence_breakdown}</span>
      </div>

      <details className="text-xs text-neutral-400">
        <summary className="cursor-pointer text-neutral-300">Sources ({rec.sources.length})</summary>
        <ul className="list-disc list-inside mt-1 space-y-1">
          {rec.sources.map((s, i) => (
            <li key={i}>{s}</li>
          ))}
        </ul>
      </details>
    </div>
  );
}
