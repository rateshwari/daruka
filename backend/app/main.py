"""
FastAPI orchestration layer. Two entry points:
  POST /converse   -> free text input (extraction -> slot fill -> reason)
  POST /diagnose    -> structured JSON input (straight to reasoning)
Both funnel into the same reasoning + retrieval + formatting pipeline,
so the two input modes never diverge in behavior.
"""
from __future__ import annotations
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .schemas import ConverseRequest, DiagnoseRequest, SystemResponse, EnvironmentalInput
from . import memory, slot_filling, rule_graph, output_formatter, llm_generator
from .structured_db import init_db

app = FastAPI(title="Darukaa.Earth Biodiversity Intelligence API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten for production
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()


def _run_pipeline(session_id: str, skip_clarification: bool = False) -> SystemResponse:
    session = memory.get_session(session_id)
    slots = session["slots"]

    if not skip_clarification and not slot_filling.has_enough_slots(slots):
        question = slot_filling.next_clarification(slots)
        memory.append_history(session_id, "assistant", question)
        return SystemResponse(
            session_id=session_id,
            reply_text=question,
            clarification_needed=True,
            missing_slots=slot_filling.missing_slots(slots),
            filled_input=EnvironmentalInput(**slots),
        )

    fired_nodes = rule_graph.evaluate(slots)
    diagnosis_lines = rule_graph.biome_diagnosis_summary(slots)

    if not fired_nodes:
        reply = (
            "Based on what you've shared, none of the known degradation "
            "patterns clearly match yet. Diagnosis against biome norms: "
            + "; ".join(diagnosis_lines) if diagnosis_lines else
            "I don't have enough matched conditions to make a grounded recommendation yet — "
            "could you share more detail (e.g. land use, rainfall, region biome)?"
        )
        memory.append_history(session_id, "assistant", reply)
        return SystemResponse(
            session_id=session_id, reply_text=reply, clarification_needed=False,
            filled_input=EnvironmentalInput(**slots),
        )

    recommendations = []
    reply_parts = []
    for node in fired_nodes:
        rec = output_formatter.build_recommendation(node, slots)
        reply_parts.append(rec.pop("reply_text"))
        recommendations.append(rec)

    reply_text = "\n\n".join(reply_parts)
    memory.append_history(session_id, "assistant", reply_text)

    return SystemResponse(
        session_id=session_id,
        reply_text=reply_text,
        clarification_needed=False,
        recommendations=recommendations,
        filled_input=EnvironmentalInput(**slots),
    )


@app.post("/converse", response_model=SystemResponse)
def converse(req: ConverseRequest):
    memory.append_history(req.session_id, "user", req.message)
    extracted = llm_generator.extract_structured_fields(req.message)
    memory.update_slots(req.session_id, extracted)
    return _run_pipeline(req.session_id)


@app.post("/diagnose", response_model=SystemResponse)
def diagnose(req: DiagnoseRequest):
    data = req.data.model_dump()
    if data.get("region_biome") is None and data.get("lat") is not None and data.get("lon") is not None:
        from .geo_lookup import lookup_biome
        inferred = lookup_biome(data["lat"], data["lon"])
        if inferred:
            data["region_biome"] = inferred
    memory.update_slots(req.session_id, data)
    return _run_pipeline(req.session_id, skip_clarification=True)


@app.get("/health")
def health():
    return {"status": "ok"}
