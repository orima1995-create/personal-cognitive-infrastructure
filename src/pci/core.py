from __future__ import annotations

import json
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUSES = ("AI_PROPOSED", "USER_CONFIRMED", "OBSERVED")
IMPACT_AXES = (
    "RICHNESS", "FEEL", "EASE", "GROW", "CONNECT", "CREATE", "TRANSFER"
)
IMPACT_LEVELS = ("LOW", "MEDIUM", "HIGH")


class ContractError(ValueError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def empty_store() -> dict[str, Any]:
    return {"schema_version": 1, "entries": []}


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
        result[axis] = level
    return result


def propose(
    store: dict[str, Any], *, seed: str, hook: str, ruler: str, bridge: str,
    unexpected: bool, relevant: bool, joy: bool, must: bool,
    expected_impact: dict[str, str],
) -> dict[str, Any]:
    if not all(value.strip() for value in (seed, hook, ruler, bridge)):
        raise ContractError("seed, hook, ruler, and bridge must be non-empty")
    if not (unexpected and relevant):
        raise ContractError("serendipity requires both unexpected and relevant")
    if not (joy or must):
        raise ContractError("record JOY, MUST, or both; do not infer them")
    timestamp = _now()
    entry = {
        "id": str(uuid.uuid4()),
        "status": "AI_PROPOSED",
        "seed": seed,
        "hook": hook,
        "ruler": ruler,
        "serendipity": {
            "unexpected": unexpected, "relevant": relevant, "bridge": bridge
        },
        "motivation": {"joy": joy, "must": must},
        "expected_impact": expected_impact,
        "experiences": [],
        "observed_impact": {},
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    validate_entry(entry)
    store["entries"].append(entry)
    return entry


def transition(store: dict[str, Any], entry_id: str, target: str, *,
               experience: str | None = None,
               observed_impact: dict[str, str] | None = None) -> dict[str, Any]:
    entry = get_entry(store, entry_id)
    current = entry["status"]
    expected = {"USER_CONFIRMED": "AI_PROPOSED", "OBSERVED": "USER_CONFIRMED"}
    if target not in expected or current != expected[target]:
        raise ContractError(f"invalid transition: {current} -> {target}")
    if target == "OBSERVED":
        if not experience or not experience.strip():
            raise ContractError("OBSERVED requires an actual experience")
        if not observed_impact:
            raise ContractError("OBSERVED requires at least one observed impact")
        entry["experiences"].append(experience)
        entry["observed_impact"] = observed_impact
    entry["status"] = target
    entry["updated_at"] = _now()
    validate_entry(entry)
    return entry


def get_entry(store: dict[str, Any], entry_id: str) -> dict[str, Any]:
    matches = [entry for entry in store["entries"] if entry["id"] == entry_id]
    if len(matches) != 1:
        raise ContractError(f"entry not found: {entry_id}")
    return matches[0]


def is_learnable(entry: dict[str, Any]) -> bool:
    serendipity = entry["serendipity"]
    return bool(
        entry["status"] == "OBSERVED"
        and entry["motivation"]["joy"]
        and serendipity["unexpected"]
        and serendipity["relevant"]
        and serendipity["bridge"].strip()
        and entry["observed_impact"]
    )


def present(entry: dict[str, Any]) -> dict[str, Any]:
    return {**entry, "learnable": is_learnable(entry)}


def validate_store(store: dict[str, Any]) -> None:
    if set(store) != {"schema_version", "entries"} or store["schema_version"] != 1:
        raise ContractError("unsupported store shape or schema version")
    if not isinstance(store["entries"], list):
        raise ContractError("entries must be a list")
    ids = []
    for entry in store["entries"]:
        validate_entry(entry)
        ids.append(entry["id"])
    if len(ids) != len(set(ids)):
        raise ContractError("entry ids must be unique")


def validate_entry(entry: dict[str, Any]) -> None:
    if entry.get("status") not in STATUSES:
        raise ContractError("invalid status")
    if not isinstance(entry.get("hook"), str) or not entry["hook"].strip():
        raise ContractError("exactly one non-empty hook string is required")
    for field in ("seed", "ruler"):
        if not isinstance(entry.get(field), str) or not entry[field].strip():
            raise ContractError(f"{field} is required")
    s = entry.get("serendipity", {})
    if not (s.get("unexpected") is True and s.get("relevant") is True
            and isinstance(s.get("bridge"), str) and s["bridge"].strip()):
        raise ContractError("serendipity requires unexpected + relevant + bridge")
    m = entry.get("motivation", {})
    if set(m) != {"joy", "must"} or not all(isinstance(v, bool) for v in m.values()):
        raise ContractError("motivation must explicitly separate joy and must")
    if not any(m.values()):
        raise ContractError("at least one motivation must be recorded")
    _validate_impact(entry.get("expected_impact"), "expected_impact")
    _validate_impact(entry.get("observed_impact"), "observed_impact")
    experiences = entry.get("experiences")
    if not isinstance(experiences, list) or not all(isinstance(x, str) and x.strip() for x in experiences):
        raise ContractError("experiences must be non-empty strings")
    observed = entry["status"] == "OBSERVED"
    if observed != bool(experiences) or observed != bool(entry["observed_impact"]):
        raise ContractError("experience and observed impact exist only in OBSERVED state")


def _validate_impact(value: Any, name: str) -> None:
    if not isinstance(value, dict):
        raise ContractError(f"{name} must be an object")
    if any(axis not in IMPACT_AXES or level not in IMPACT_LEVELS
           for axis, level in value.items()):
        raise ContractError(f"{name} contains an invalid axis or level")

