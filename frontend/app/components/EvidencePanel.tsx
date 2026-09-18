import { Recommendation } from "../../lib/types";

export default function EvidencePanel({ recommendations }: { recommendations: Recommendation[] }) {
  if (recommendations.length === 0) {
    return (
      <div className="w-80 shrink-0 border-l border-neutral-800 p-4">
        <h2 className="text-sm font-semibold text-neutral-400 uppercase tracking-wide mb-2">
          Evidence & Reasoning
        </h2>
        <p className="text-xs text-neutral-600">
          Grounding sources and the reasoning-engine node that fired will appear here
          once a recommendation is generated.
        </p>
      </div>
    );
  }

  return (
    <div className="w-80 shrink-0 border-l border-neutral-800 p-4 overflow-y-auto space-y-4">
      <h2 className="text-sm font-semibold text-neutral-400 uppercase tracking-wide">
        Evidence & Reasoning
      </h2>
      {recommendations.map((rec, i) => (
        <div key={i} className="rounded-lg border border-neutral-800 p-3 space-y-2">
          <p className="text-xs text-neutral-500">
            Rule node: <span className="text-neutral-300 font-mono">{rec.rule_node_id}</span>
          </p>
          <p className="text-xs text-neutral-500">{rec.confidence_breakdown}</p>
          <div className="space-y-1">
            {rec.sources.map((s, j) => (
              <p key={j} className="text-xs text-neutral-400 border-l-2 border-neutral-700 pl-2">
                {s}
              </p>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
