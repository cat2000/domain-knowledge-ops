#!/usr/bin/env python3
"""Shared policy loader for S3 proposition routing rules."""
from __future__ import annotations

import json
from pathlib import Path


def _deep_merge(base: dict[str, object], override: dict[str, object]) -> dict[str, object]:
    out = dict(base)
    for key, val in override.items():
        if isinstance(val, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(dict(out.get(key) or {}), val)
        else:
            out[key] = val
    return out


def load_policy_bundle(config_path: Path) -> dict[str, object]:
    """Load policy config; supports both layered and legacy flat schema."""
    try:
        raw = dict(json.loads(config_path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError):
        return {"global": {}, "intent_overrides": {}, "team_overrides": {}}

    if "global" in raw or "intent_overrides" in raw or "team_overrides" in raw:
        return {
            "global": dict(raw.get("global") or {}),
            "intent_overrides": dict(raw.get("intent_overrides") or {}),
            "team_overrides": dict(raw.get("team_overrides") or {}),
        }

    # Legacy flat schema fallback.
    return {"global": raw, "intent_overrides": {}, "team_overrides": {}}


def resolve_base_policy(bundle: dict[str, object], team: str = "") -> dict[str, object]:
    global_policy = dict(bundle.get("global") or {})
    if not team:
        return global_policy
    team_policy = dict(dict(bundle.get("team_overrides") or {}).get(team) or {})
    return _deep_merge(global_policy, dict(team_policy.get("global") or {}))


def resolve_intent_policy(bundle: dict[str, object], intent: str, team: str = "") -> dict[str, object]:
    policy = resolve_base_policy(bundle, team=team)
    intent_overrides = dict(bundle.get("intent_overrides") or {})
    if intent:
        policy = _deep_merge(policy, dict(intent_overrides.get(intent) or {}))

    if team:
        team_policy = dict(dict(bundle.get("team_overrides") or {}).get(team) or {})
        team_intent_overrides = dict(team_policy.get("intent_overrides") or {})
        if intent:
            policy = _deep_merge(policy, dict(team_intent_overrides.get(intent) or {}))
    return policy

