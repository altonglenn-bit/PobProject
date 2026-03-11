from __future__ import annotations

import argparse
import json
from copy import deepcopy
from typing import Any

from archetypes import ARCHETYPES, get_archetype, list_archetypes
from build_rules import apply_stage


PROFILE_OVERRIDES: dict[str, dict[str, Any]] = {
    "ice_crash_shadow": {
        "playstyle": "melee",
        "aliases": ["ice_crash"],
        "content_tags": ["maps"],
        "profile": {
            "league_starter": True,
            "tankiness": "high",
            "safe_build": True,
            "complexity": "low",
        },
    },
    "boneshatter_slayer": {
        "playstyle": "melee",
        "aliases": ["boneshatter", "slayer"],
        "content_tags": ["maps", "bossing"],
        "profile": {
            "bossing": "strong",
            "league_starter": True,
            "tankiness": "high",
            "safe_build": True,
            "complexity": "low",
            "apm": "low",
            "uber_ready_safe": True,
        },
    },
    "lightning_arrow_deadeye": {
        "playstyle": "bow",
        "aliases": ["lightning_arrow", "deadeye", "bow_mapper"],
        "content_tags": ["maps", "heist"],
        "profile": {
            "mapping": "strong",
            "clear_speed": "high",
            "budget": "low",
            "league_starter": True,
        },
    },
    "elementalist_kinetic_blast": {
        "playstyle": "caster",
        "aliases": ["kinetic_blast", "wander", "elementalist"],
        "content_tags": ["maps", "heist"],
        "profile": {
            "mapping": "strong",
            "clear_speed": "high",
        },
    },
    "spectre_summoner_necromancer": {
        "playstyle": "minion",
        "aliases": ["spectre", "summoner", "necromancer"],
        "content_tags": ["maps", "bossing"],
        "profile": {
            "league_starter": True,
            "tankiness": "high",
            "safe_build": True,
            "apm": "low",
            "low_apm_special": True,
            "complexity": "low",
            "beginner_friendly": True,
            "automated_bossing": True,
        },
    },
    "kinetic_fusillade_totem": {
        "playstyle": "totem",
        "aliases": ["totem", "ballista", "kinetic_fusillade"],
        "content_tags": ["maps", "bossing"],
        "profile": {
            "bossing": "strong",
            "league_starter": True,
            "tankiness": "high",
            "safe_build": True,
            "apm": "low",
            "ranged_safe_bossing": True,
            "uber_ready_safe": True,
            "safe_bosser": True,
        },
    },
}


def load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_archetypes() -> dict[str, dict[str, Any]]:
    """Compatibility helper for recommendation tooling.

    The project originally imported load_archetypes from this module. Some newer
    versions moved the source of truth into archetypes.py. Exposing the enriched
    data here keeps older callers working while centralizing the actual static
    definitions in archetypes.py.
    """
    enriched: dict[str, dict[str, Any]] = {}
    for name, config in ARCHETYPES.items():
        merged = deepcopy(config)
        merged.update(PROFILE_OVERRIDES.get(name, {}))
        merged.setdefault("base", merged.get("base_file", "build.json"))
        enriched[name] = merged
    return enriched


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate progression-stage builds from an archetype."
    )
    parser.add_argument("--base", default=None, help="Optional base build JSON override")
    parser.add_argument("--archetype", default=None, help="Archetype name")
    parser.add_argument("--stage", default=None, help="Stage name like leveling, early_maps, endgame")
    parser.add_argument("--out", default=None, help="Output JSON path")
    parser.add_argument("--list", action="store_true", help="List archetypes")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.list:
        print("Available archetypes:")
        for name in list_archetypes():
            print(f"  - {name}")
        return

    if not args.archetype or not args.stage:
        raise SystemExit("Please provide --archetype and --stage, or use --list.")

    archetype = get_archetype(args.archetype)
    base_path = args.base or archetype.get("base_file") or "build.json"

    base_build = load_json(base_path)
    result, changes = apply_stage(base_build, archetype, args.stage)

    out = args.out or f"{args.archetype}_{args.stage}.json"
    save_json(out, result)

    print("=" * 60)
    print("PROGRESSION BUILD SUMMARY")
    print("=" * 60)
    print(f"Base:      {base_path}")
    print(f"Archetype: {args.archetype}")
    print(f"Stage:     {args.stage}")
    print(f"Output:    {out}")
    print("Changes:")
    for change in changes:
        print(f"  - {change}")
    print("=" * 60)


if __name__ == "__main__":
    main()
