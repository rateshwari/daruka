# Darukaa.Earth — AI Biodiversity Intelligence System

A grounded, multi-metric environmental reasoning system:
**Knowledge layer (FAISS + SQLite norms) → Reasoning engine (deterministic rule graph) → Conversation layer (slot-filling + memory) → LLM only for final prose.**

See `ARCHITECTURE.md` (if you kept the earlier design doc alongside this) for the full rationale. This README is just get-it-running.

---

## 0. Prerequisites

- Python 3.10+
- Node.js 18+
- (Optional) an Anthropic API key — the system runs without one using deterministic fallbacks, but responses read better with it.

---

## 1. Backend setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
# Note: sentence-transformers pulls in torch — this can be a large install
# (~2-3 min) and needs a few GB of disk. If disk space is tight, install
# the CPU-only torch wheel first:
#   pip install torch --index-url https://download.pytorch.org/whl/cpu
# then: pip install -r requirements.txt

cp .env.example .env
# Optionally add ANTHROPIC_API_KEY=sk-... to .env

python -m app.structured_db     # initializes norms.db (run once)

uvicorn app.main:app --reload --port 8000
```

Verify it's up: open `http://localhost:8000/health` → `{"status": "ok"}`

Quick smoke test (matches the brief's example use case):

```bash
curl -X POST http://localhost:8000/diagnose \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test1",
    "data": {
      "soil_organic_carbon_pct": 0.3,
      "rainfall_pattern": "low",
      "land_use": "monoculture",
      "region_biome": "semi-arid"
    }
  }'
```

You should get back JSON with `recommendations` including agroforestry intercropping and reduced tillage, each with `impacted_metrics`, `sources`, `confidence`, and `time_horizon` — this is the Output Contract from the architecture doc.

---

## 2. Frontend setup

```bash
cd frontend
npm install
echo "NEXT_PUBLIC_API_BASE=http://localhost:8000" > .env.local
npm run dev
```

Open `http://localhost:3000`. Try typing:

> Soil organic carbon is 0.3%, rainfall is low, we grow monoculture wheat in a semi-arid region.

You should see: the Metrics panel fill in on the left, a metric radar chart update, recommendation cards appear in the chat with confidence badges and metric chips, and the Evidence panel on the right show which rule node fired and which sources were retrieved.

---

## 3. Project structure

```
backend/
  app/
    schemas.py          # Pydantic input/output contracts (Section 6-7)
    structured_db.py     # SQLite norms — healthy ranges per metric/biome (Section 3.2)
    seed_sources.py       # Hand-chunked evidence corpus (Section 3.4)
    vector_store.py       # FAISS retrieval, metric-filtered then similarity-ranked (Section 3.3)
    rule_graph.py          # Deterministic multi-metric reasoning engine (Section 4)
    slot_filling.py         # Clarification logic, priority-ordered (Section 5.1)
    memory.py                # Session slot + history store (Section 5.2)
    llm_generator.py          # ONLY place the LLM is called — extraction + prose only
    output_formatter.py        # Builds Output Contract + confidence scoring (Section 4.3)
    main.py                      # FastAPI endpoints: /converse, /diagnose, /health

frontend/
  app/
    page.tsx                     # Three-panel layout (Section 9.1)
    components/
      MetricsPanel.tsx            # Slot-fill status checklist
      MetricRadarChart.tsx         # Multi-metric visualization (Section 9.4)
      ChatPanel.tsx                  # Conversation thread + recommendation cards
      RecommendationCard.tsx          # Structured recommendation rendering (Section 9.2)
      EvidencePanel.tsx                 # Live sources + rule node (Section 9.3)
  lib/
    api.ts                              # Backend client
    types.ts                             # Shared TS types matching schemas.py
```

---

## 4. Extending before the demo (highest-leverage first)

1. **Add more rule nodes** in `rule_graph.py` — currently 8 nodes. Each new node covering a distinct cross-metric pattern directly strengthens "Depth of Reasoning" scoring. Follow the existing pattern: `trigger`, `diagnosis`, `cross_metric_effects`, `trade_offs`, `rejected_alternatives`.
2. **Add more evidence chunks** in `seed_sources.py` — read the actual FAO/IPCC/IUCN sources you cite and write your own 1-2 sentence paraphrases with correct `metric_affected`/`biome_applicability` tags. Don't paste verbatim text from PDFs.
3. **Geo-coordinate → biome lookup** (bonus): add a small lat/lon-bounding-box table and call it from `/diagnose` before running the pipeline, to auto-fill `region_biome`.
4. **Regression test set**: write 5-8 known `EnvironmentalInput` scenarios with expected `rule_node_id` firing, assert against `/diagnose` — gives you a "verified against N scenarios" badge for the demo and catches regressions as you add rule nodes.
5. **Downloadable report**: serialize a session's final `SystemResponse` to Markdown/PDF — you already have the structured JSON, this is a rendering step only.

---

## 5. Common issues

- **`ModuleNotFoundError: faiss`** — reinstall with `pip install faiss-cpu` (not `faiss`, which is a different unmaintained package).
- **Torch install fails / disk space** — use the CPU-only wheel link in step 1, or swap `sentence-transformers` for a smaller model like `paraphrase-MiniLM-L3-v2` (edit `_MODEL_NAME` in `vector_store.py`).
- **CORS errors in browser** — confirm backend is running on port 8000 and `NEXT_PUBLIC_API_BASE` in `frontend/.env.local` matches.
- **Frontend shows no metrics filling in** — check the Network tab for the `/converse` response; if `filled_input` is null, the extraction fallback in `llm_generator._naive_extract` may not have matched your phrasing — try the exact example sentence above first to confirm wiring, then loosen the regex.
