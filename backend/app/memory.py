"""
Session memory — Section 5.2. Two tiers: slot memory (the accumulating
EnvironmentalInput dict) and a short rolling message history for tone
continuity. In-memory dict is enough for a hackathon demo; swap for
Redis if you need multi-instance deployment.
"""
from __future__ import annotations
from typing import Dict, List
import time

_SESSIONS: Dict[str, dict] = {}


def get_session(session_id: str) -> dict:
    if session_id not in _SESSIONS:
        _SESSIONS[session_id] = {
            "slots": {},
            "history": [],
            "created_at": time.time(),
        }
    return _SESSIONS[session_id]


def update_slots(session_id: str, new_fields: dict) -> dict:
    session = get_session(session_id)
    for k, v in new_fields.items():
        if v is not None:
            session["slots"][k] = v
    return session["slots"]


def append_history(session_id: str, role: str, content: str, max_len: int = 12):
    session = get_session(session_id)
    session["history"].append({"role": role, "content": content})
    session["history"] = session["history"][-max_len:]
