from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from progression_build import load_archetypes


STAGE_ORDER = {
    "leveling": 0,
    "early_maps": 1,
    "endgame": 2,
}


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def normalize_alias(value: str) -> str:
    return value.strip().lower().replace(" ", "_").replace("-", "_")


def infer_tags_for_archetype(archetype_name: str, config: dict[str, Any]) -> set[str]:
    tags: set[str] = set()

    for key in ("tags", "content_tags", "aliases"):
        value = config.get(key, [])
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    tags.add(normalize_alias(item))

    lowered_name = archetype_name.lower()
    for part in lowered_name.replace("-", "_").split("_"):
        if part:
            tags.add(part)

    playstyle = config.get("playstyle")
    if isinstance(playstyle, str) and playstyle.strip():
        tags.add(normalize_alias(playstyle))

    return tags


def get_stage_config(config: dict[str, Any], stage_name: str) -> dict[str, Any]:
    stages = config.get("stages", {})
    stage_config = stages.get(stage_name, {})
    if isinstance(stage_config, dict):
        return stage_config
    return {}


def stage_rank(stage_name: str) -> int:
    return STAGE_ORDER.get(stage_name, -1)


def make_result(
    archetype: str,
    stage: str,
    base: str,
    score: int,
    reasons: list[str],
    breakdown: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    return {
        "archetype": archetype,
        "stage": stage,
        "base": base,
        "base_file": base,
        "recommended_archetype": archetype,
        "recommended_stage": stage,
        "score": score,
        "reasons": reasons,
        "breakdown": breakdown,
    }


def add_breakdown(
    breakdown: dict[str, list[dict[str, Any]]],
    category: str,
    points: int,
    reason: str,
) -> None:
    if points == 0:
        return
    breakdown.setdefault(category, []).append({"points": points, "reason": reason})


def total_breakdown(breakdown: dict[str, list[dict[str, Any]]], category: str) -> int:
    return sum(entry["points"] for entry in breakdown.get(category, []))


def make_reason_list(breakdown: dict[str, list[dict[str, Any]]]) -> list[str]:
    ordered_categories = [
        "playstyle",
        "goal",
        "league_starter",
        "tankiness",
        "apm",
        "complexity",
        "budget",
        "speed",
        "content",
        "aliases",
        "stage",
        "special",
    ]
    reasons: list[str] = []
    for category in ordered_categories:
        for entry in breakdown.get(category, []):
            if entry["points"] > 0:
                reasons.append(entry["reason"])
    return reasons


def score_candidate(
    archetype_name: str,
    config: dict[str, Any],
    stage_name: str,
    prefs: dict[str, Any],
) -> dict[str, Any]:
    score = 0
    breakdown: dict[str, list[dict[str, Any]]] = {}

    base = config.get("base", "")
    archetype_tags = infer_tags_for_archetype(archetype_name, config)
    stage_config = get_stage_config(config, stage_name)

    profile = config.get("profile", {})
    if not isinstance(profile, dict):
        profile = {}

    requested_playstyle = prefs.get("playstyle")
    requested_goal = prefs.get("goal")
    requested_budget = prefs.get("budget")
    requested_speed = prefs.get("speed")
    requested_tankiness = prefs.get("tankiness")
    requested_apm = prefs.get("apm")
    requested_complexity = prefs.get("complexity")
    requested_stage = prefs.get("stage")
    requested_aliases = prefs.get("aliases", [])
    requested_content = prefs.get("content_tags", [])
    requested_league_starter = bool(prefs.get("league_starter"))

    playstyle = config.get("playstyle")
    if isinstance(playstyle, str):
        playstyle = normalize_alias(playstyle)

    # playstyle
    if requested_playstyle:
        requested_playstyle_norm = normalize_alias(requested_playstyle)
        if playstyle == requested_playstyle_norm:
            score += 7
            add_breakdown(
                breakdown,
                "playstyle",
                7,
                f"matches playstyle '{requested_playstyle_norm}'",
            )
        else:
            penalty = -6
            # slightly softer mismatch for ranged/caster-ish overlap or bow/caster style overlap
            if requested_playstyle_norm in {"caster", "bow"} and playstyle in {"caster", "bow"}:
                penalty = -3
                add_breakdown(
                    breakdown,
                    "penalties",
                    penalty,
                    f"slight penalty for weaker fit to requested playstyle '{requested_playstyle_norm}'",
                )
            else:
                add_breakdown(
                    breakdown,
                    "penalties",
                    penalty,
                    f"penalized for not matching requested playstyle '{requested_playstyle_norm}'",
                )
            score += penalty

    # goal
    if requested_goal == "bossing":
        if profile.get("bossing") == "strong":
            score += 5
            add_breakdown(breakdown, "goal", 5, "good bossing profile")
        elif "bossing" in archetype_tags:
            score += 3
            add_breakdown(breakdown, "goal", 3, "supports bossing content")
    elif requested_goal == "fast mapper":
        if profile.get("mapping") == "strong":
            score += 5
            add_breakdown(breakdown, "goal", 5, "strong mapping profile")
        if profile.get("clear_speed") == "high":
            score += 3
            add_breakdown(breakdown, "goal", 3, "high clear-speed profile")

    # league starter
    if requested_league_starter:
        if profile.get("league_starter") is True:
            score += 4
            add_breakdown(breakdown, "league_starter", 4, "good league starter")

    # tankiness / safe
    if requested_tankiness == "high":
        if profile.get("tankiness") == "high":
            score += 5
            add_breakdown(breakdown, "tankiness", 5, "fits tanky/safe preference")

    # apm
    if requested_apm == "low":
        if profile.get("apm") == "low":
            score += 3
            add_breakdown(breakdown, "apm", 3, "fits low apm preference")

    # complexity
    if requested_complexity == "low":
        if profile.get("complexity") == "low":
            score += 3
            add_breakdown(breakdown, "complexity", 3, "fits low complexity preference")

    # budget
    if requested_budget == "low":
        if profile.get("budget") == "low":
            score += 3
            add_breakdown(breakdown, "budget", 3, "fits low budget")

    # speed
    if requested_speed == "high":
        if profile.get("clear_speed") == "high":
            score += 3
            add_breakdown(breakdown, "speed", 3, "matches high-speed preference")

    # content tags
    for tag in requested_content:
        tag_norm = normalize_alias(tag)
        if tag_norm in archetype_tags:
            score += 2
            add_breakdown(breakdown, "content", 2, f"supports content '{tag_norm}'")

    # aliases
    for alias in requested_aliases:
        alias_norm = normalize_alias(alias)
        if alias_norm in archetype_tags:
            score += 4
            add_breakdown(breakdown, "aliases", 4, f"boosted by alias match: {alias_norm}")

    # stage fit
    if requested_stage:
        requested_rank = stage_rank(requested_stage)
        current_rank = stage_rank(stage_name)
        if requested_stage == stage_name:
            score += 2
            add_breakdown(breakdown, "stage", 2, f"fits {requested_stage.replace('_', ' ')} stage")
        elif requested_rank >= 0 and current_rank >= 0:
            diff = abs(current_rank - requested_rank)
            if diff == 1:
                score -= 1
                add_breakdown(
                    breakdown,
                    "penalties",
                    -1,
                    f"near miss on requested stage '{requested_stage}'",
                )
            elif diff >= 2:
                score -= 3
                add_breakdown(
                    breakdown,
                    "penalties",
                    -3,
                    f"weaker fit for requested stage '{requested_stage}'",
                )

    # special fits
    safe_request = requested_tankiness == "high"
    beginner_request = requested_complexity == "low"
    low_apm_request = requested_apm == "low"
    uber_request = "bossing" in [normalize_alias(x) for x in requested_content] and prefs.get("source_prompt", "").lower().find("uber") >= 0

    if safe_request and profile.get("safe_build") is True:
        score += 4
        add_breakdown(breakdown, "special", 4, "strong safe-build fit")

    if beginner_request and profile.get("beginner_friendly") is True:
        score += 4
        add_breakdown(breakdown, "special", 4, "strong beginner-friendly fit")

    if low_apm_request and profile.get("low_apm_special") is True:
        score += 4
        add_breakdown(breakdown, "special", 4, "strong low-apm fit")

    if profile.get("automated_bossing") is True and (safe_request or beginner_request or requested_playstyle == "minion"):
        score += 2
        add_breakdown(breakdown, "special", 2, "tiebreak boost for safer automated bossing")

    if profile.get("ranged_safe_bossing") is True and (safe_request or requested_goal == "bossing"):
        score += 2
        add_breakdown(breakdown, "special", 2, "tiebreak boost for safer ranged bossing")

    if profile.get("uber_ready_safe") is True and (safe_request or uber_request or requested_goal == "bossing"):
        score += 1
        add_breakdown(breakdown, "special", 1, "extra tiebreak boost for safe uber-ready profile")

    if uber_request and profile.get("safe_bosser") is True:
        score += 3
        add_breakdown(breakdown, "special", 3, "extra fit for safer uber bossing")

    if uber_request and playstyle == "melee":
        score -= 1
        add_breakdown(breakdown, "penalties", -1, "small tiebreak penalty for melee on safe uber-style request")

    reasons = make_reason_list(breakdown)
    return make_result(archetype_name, stage_name, base, score, reasons, breakdown)


def sort_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        results,
        key=lambda r: (r["score"], stage_rank(r["stage"])),
        reverse=True,
    )


def unique_top_matches(results: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    """
    Keep only the highest scoring stage per archetype for display purposes.
    This does not affect the winner selection, only the printed ranking clarity.
    """
    chosen: dict[str, dict[str, Any]] = {}
    for result in sort_results(results):
        archetype = result["archetype"]
        if archetype not in chosen:
            chosen[archetype] = result
        else:
            existing = chosen[archetype]
            if result["score"] > existing["score"]:
                chosen[archetype] = result
            elif result["score"] == existing["score"] and stage_rank(result["stage"]) > stage_rank(existing["stage"]):
                chosen[archetype] = result

    return sort_results(list(chosen.values()))[:limit]


def recommend_build(
    prefs: dict[str, Any],
    debug: bool = False,
) -> dict[str, Any]:
    archetypes = load_archetypes()

    all_results: list[dict[str, Any]] = []

    for archetype_name, config in archetypes.items():
        stages = config.get("stages", {})
        if not isinstance(stages, dict) or not stages:
            continue

        for stage_name in stages.keys():
            result = score_candidate(archetype_name, config, stage_name, prefs)
            all_results.append(result)

    if not all_results:
        raise ValueError("No archetypes or stages available to recommend from.")

    sorted_all = sort_results(all_results)
    winner = deepcopy(sorted_all[0])

    display_top = unique_top_matches(sorted_all, limit=5)
    winner["top_matches"] = deepcopy(display_top)
    winner["shortlist"] = deepcopy(display_top)

    if debug:
        winner["all_ranked_results"] = deepcopy(sorted_all)

    return winner


def print_breakdown(breakdown: dict[str, list[dict[str, Any]]]) -> None:
    ordered_categories = [
        "playstyle",
        "goal",
        "league_starter",
        "tankiness",
        "apm",
        "complexity",
        "budget",
        "speed",
        "content",
        "aliases",
        "stage",
        "special",
        "penalties",
    ]

    print("Score breakdown:")
    for category in ordered_categories:
        entries = breakdown.get(category, [])
        if not entries:
            continue
        total = sum(entry["points"] for entry in entries)
        print(f"  {category}: {total:+d}")
        for entry in entries:
            print(f"    {entry['points']:+d}  {entry['reason']}")


def print_result(result: dict[str, Any], out_path: str | None, debug: bool) -> None:
    print("=" * 60)
    print("BUILD RECOMMENDATION")
    print("=" * 60)
    print(f"Archetype: {result['archetype']}")
    print(f"Stage:     {result['stage']}")
    print(f"Base:      {result['base']}")
    print(f"Score:     {result['score']}")
    print("Reasons:")
    for reason in result["reasons"]:
        print(f"  - {reason}")
    print("Command:")
    print(f"  python generate_build.py --archetype {result['archetype']} --stage {result['stage']}")
    print()

    if debug:
        print_breakdown(result["breakdown"])
        print()

    print("Top matches:")
    for idx, match in enumerate(result["top_matches"], start=1):
        print(f"  {idx}. {match['archetype']} | stage={match['stage']} | score={match['score']}")
        for reason in match["reasons"][:5]:
            print(f"     - {reason}")
        if debug:
            print("     Breakdown totals:")
            for category in [
                "playstyle",
                "goal",
                "league_starter",
                "tankiness",
                "apm",
                "complexity",
                "budget",
                "speed",
                "content",
                "aliases",
                "stage",
                "special",
                "penalties",
            ]:
                total = total_breakdown(match["breakdown"], category)
                if total != 0:
                    print(f"       - {category}: {total:+d}")

    if out_path:
        print(f"Saved:     {out_path}")
    print("=" * 60)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Recommend the best build archetype/stage from preference JSON.")
    parser.add_argument("--prefs", required=True, help="Path to preferences JSON")
    parser.add_argument("--out", default="recommended_build.json", help="Output path for recommendation JSON")
    parser.add_argument("--debug", action="store_true", help="Print scoring breakdown")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    prefs = load_json(args.prefs)
    result = recommend_build(prefs, debug=args.debug)

    Path(args.out).write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print_result(result, args.out, args.debug)


if __name__ == "__main__":
    main()