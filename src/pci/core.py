from __future__ import annotations

import json
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUSES = ("AI_PROPOSED", "USER_CONFIRMED", "USER_REJECTED", "OBSERVED")
IMPACT_AXES = ("RICHNESS", "FEEL", "EASE", "GROW", "CONNECT", "CREATE", "TRANSFER")
IMPACT_LEVELS = ("LOW", "MEDIUM", "HIGH")
ENTRY_KEYS = {
    "id", "status", "seed", "hook", "ruler", "serendipity", "motivation",
    "expected_impact", "experiences", "observed_impact", "decision_note",
    "created_at", "updated_at",
}


class ContractError(ValueError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def empty_store() -> dict[str, Any]:
    return {"schema_version": 2, "entries": []}


def load_store(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ContractError(f"store does not exist: {path}; run init first")
    data = json.loads(path.read_text(encoding="utf-8"))
    validate_store(data)
    return data


def save_store(path: Path, data: dict[str, Any]) -> None:
    validate_store(data)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def init_store(path: Path) -> None:
    if path.exists():
        load_store(path)
        return
    save_store(path, empty_store())


def parse_impacts(items: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in items:
        try:
            axis, level = item.split("=", 1)
        except ValueError as exc:
            raise ContractError(f"impact must be AXIS=LEVEL: {item}") from exc
        axis, level = axis.upper(), level.upper()
        if axis not in IMPACT_AXES:
            raise ContractError(f"unknown impact axis: {axis}")
        if level not in IMPACT_LEVELS:
            raise ContractError(f"unknown impact level: {level}")
        if axis in result:
            raise ContractError(f"duplicate impact axis: {axis}")
        result[axis] = level
    return result


def propose(store: dict[str, Any], *, seed: str, hook: str, ruler: str,
            bridge: str, unexpected: bool, relevant: bool,
            expected_impact: dict[str, str]) -> dict[str, Any]:
    if not all(isinstance(value, str) and value.strip()
               for value in (seed, hook, ruler, bridge)):
        raise ContractError("seed, hook, ruler, and bridge must be non-empty")
    if not (unexpected and relevant):
        raise ContractError("serendipity requires both unexpected and relevant")
    timestamp = _now()
    entry = {
        "id": str(uuid.uuid4()), "status": "AI_PROPOSED", "seed": seed,
        "hook": hook, "ruler": ruler,
        "serendipity": {"unexpected": unexpected, "relevant": relevant, "bridge": bridge},
        "motivation": {"joy": None, "must": None},
        "expected_impact": expected_impact, "experiences": [],
        "observed_impact": {}, "decision_note": None,
        "created_at": timestamp, "updated_at": timestamp,
    }
    validate_entry(entry)
    store["entries"].append(entry)
    return entry


def confirm(store: dict[str, Any], entry_id: str, *, joy: bool, must: bool,
            note: str | None = None) -> dict[str, Any]:
    entry = get_entry(store, entry_id)
    if entry["status"] != "AI_PROPOSED":
        raise ContractError(f"invalid transition: {entry['status']} -> USER_CONFIRMED")
    if not (joy or must):
        raise ContractError("confirmation must explicitly record JOY, MUST, or both")
    entry["motivation"] = {"joy": joy, "must": must}
    entry["decision_note"] = _clean_optional(note)
    entry["status"] = "USER_CONFIRMED"
    entry["updated_at"] = _now()
    validate_entry(entry)
    return entry


def reject(store: dict[str, Any], entry_id: str, *, note: str | None = None) -> dict[str, Any]:
    entry = get_entry(store, entry_id)
    if entry["status"] != "AI_PROPOSED":
        raise ContractError(f"invalid transition: {entry['status']} -> USER_REJECTED")
    entry["decision_note"] = _clean_optional(note)
    entry["status"] = "USER_REJECTED"
    entry["updated_at"] = _now()
    validate_entry(entry)
    return entry


def observe(store: dict[str, Any], entry_id: str, *, experience: str,
            observed_impact: dict[str, str]) -> dict[str, Any]:
    entry = get_entry(store, entry_id)
    if entry["status"] != "USER_CONFIRMED":
        raise ContractError(f"invalid transition: {entry['status']} -> OBSERVED")
    if not isinstance(experience, str) or not experience.strip():
        raise ContractError("OBSERVED requires an actual experience")
    if not observed_impact:
        raise ContractError("OBSERVED requires at least one observed impact")
    entry["experiences"].append(experience)
    entry["observed_impact"] = observed_impact
    entry["status"] = "OBSERVED"
    entry["updated_at"] = _now()
    validate_entry(entry)
    return entry


def get_entry(store: dict[str, Any], entry_id: str) -> dict[str, Any]:
    matches = [entry for entry in store["entries"] if entry["id"] == entry_id]
    if len(matches) != 1:
        raise ContractError(f"entry not found: {entry_id}")
    return matches[0]


def is_learnable(entry: dict[str, Any]) -> bool:
    s = entry["serendipity"]
    return bool(entry["status"] == "OBSERVED"
                and entry["motivation"]["joy"] is True
                and s["unexpected"] and s["relevant"] and s["bridge"].strip()
                and entry["observed_impact"])


def present(entry: dict[str, Any]) -> dict[str, Any]:
    return {**entry, "learnable": is_learnable(entry)}


def audit_store(store: dict[str, Any]) -> dict[str, Any]:
    validate_store(store)
    counts = {status: 0 for status in STATUSES}
    must_only = learnable = 0
    for entry in store["entries"]:
        counts[entry["status"]] += 1
        must_only += int(entry["motivation"] == {"joy": False, "must": True})
        learnable += int(is_learnable(entry))
    return {
        "schema_version": store["schema_version"], "valid": True,
        "entry_count": len(store["entries"]), "status_counts": counts,
        "learnable_count": learnable, "must_only_count": must_only,
        "aggregate_qol_score": None,
    }


def validate_store(store: dict[str, Any]) -> None:
    if not isinstance(store, dict) or set(store) != {"schema_version", "entries"}:
        raise ContractError("unsupported store shape")
    if store["schema_version"] != 2:
        raise ContractError("unsupported schema version; expected 2")
    if not isinstance(store["entries"], list):
        raise ContractError("entries must be a list")
    ids = []
    for entry in store["entries"]:
        validate_entry(entry)
        ids.append(entry["id"])
    if len(ids) != len(set(ids)):
        raise ContractError("entry ids must be unique")


def validate_entry(entry: dict[str, Any]) -> None:
    if not isinstance(entry, dict) or set(entry) != ENTRY_KEYS:
        raise ContractError("entry has missing or unknown fields")
    try:
        uuid.UUID(entry["id"])
    except (ValueError, TypeError, AttributeError) as exc:
        raise ContractError("entry id must be a UUID") from exc
    if entry["status"] not in STATUSES:
        raise ContractError("invalid status")
    if not isinstance(entry["hook"], str) or not entry["hook"].strip():
        raise ContractError("exactly one non-empty hook string is required")
    for field in ("seed", "ruler"):
        if not isinstance(entry[field], str) or not entry[field].strip():
            raise ContractError(f"{field} is required")
    s = entry["serendipity"]
    if (not isinstance(s, dict) or set(s) != {"unexpected", "relevant", "bridge"}
            or s["unexpected"] is not True or s["relevant"] is not True
            or not isinstance(s["bridge"], str) or not s["bridge"].strip()):
        raise ContractError("serendipity requires unexpected + relevant + bridge")
    motivation = entry["motivation"]
    if not isinstance(motivation, dict) or set(motivation) != {"joy", "must"}:
        raise ContractError("motivation must explicitly separate joy and must")
    if entry["status"] in {"USER_CONFIRMED", "OBSERVED"}:
        if not all(isinstance(v, bool) for v in motivation.values()) or not any(motivation.values()):
            raise ContractError("confirmed motivation requires JOY, MUST, or both")
    elif motivation != {"joy": None, "must": None}:
        raise ContractError("AI proposals and rejections cannot claim human motivation")
    _validate_impact(entry["expected_impact"], "expected_impact")
    _validate_impact(entry["observed_impact"], "observed_impact")
    experiences = entry["experiences"]
    if not isinstance(experiences, list) or not all(isinstance(x, str) and x.strip() for x in experiences):
        raise ContractError("experiences must be non-empty strings")
    observed = entry["status"] == "OBSERVED"
    if observed != bool(experiences) or observed != bool(entry["observed_impact"]):
        raise ContractError("experience and observed impact exist only in OBSERVED state")
    note = entry["decision_note"]
    if note is not None and (not isinstance(note, str) or not note.strip()):
        raise ContractError("decision_note must be null or a non-empty string")
    for name in ("created_at", "updated_at"):
        _validate_timestamp(entry[name], name)
    if datetime.fromisoformat(entry["updated_at"]) < datetime.fromisoformat(entry["created_at"]):
        raise ContractError("updated_at cannot precede created_at")


def _clean_optional(value: str | None) -> str | None:
    if value is None:
        return None
    return value.strip() or None


def _validate_timestamp(value: Any, name: str) -> None:
    if not isinstance(value, str):
        raise ContractError(f"{name} must be an ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ContractError(f"{name} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ContractError(f"{name} must include a timezone")


def _validate_impact(value: Any, name: str) -> None:
    if not isinstance(value, dict):
        raise ContractError(f"{name} must be an object")
    if any(axis not in IMPACT_AXES or level not in IMPACT_LEVELS for axis, level in value.items()):
        raise ContractError(f"{name} contains an invalid axis or level")

