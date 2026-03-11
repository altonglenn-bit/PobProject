from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = text.replace("-", " ")
    text = text.replace("_", " ")
    text = re.sub(r"\s+", " ", text)
    return text


def has_any(text: str, phrases: list[str]) -> bool:
    return any(phrase in text for phrase in phrases)


def add_alias(prefs: dict[str, Any], alias: str) -> None:
    aliases = prefs.setdefault("aliases", [])
    if alias not in aliases:
        aliases.append(alias)


def add_content_tag(prefs: dict[str, Any], tag: str) -> None:
    tags = prefs.setdefault("content_tags", [])
    if tag not in tags:
        tags.append(tag)


def infer_playstyle(text: str, prefs: dict[str, Any]) -> None:
    if has_any(text, ["spectre", "summoner", "minion", "necromancer"]):
        prefs["playstyle"] = "minion"
        if "spectre" in text:
            add_alias(prefs, "spectre")
        if "summoner" in text:
            add_alias(prefs, "summoner")
        return

    if has_any(text, ["ballista", "totem"]):
        prefs["playstyle"] = "totem"
        if "ballista" in text:
            add_alias(prefs, "ballista")
        if "totem" in text:
            add_alias(prefs, "totem")
        return

    if has_any(text, ["lightning arrow", "deadeye", "bow", "archer"]):
        prefs["playstyle"] = "bow"
        if "lightning arrow" in text:
            add_alias(prefs, "lightning_arrow")
        if "deadeye" in text:
            add_alias(prefs, "deadeye")
        if "bow mapper" in text or ("bow" in text and ("mapper" in text or "mapping" in text)):
            add_alias(prefs, "bow_mapper")
        return

    if has_any(text, ["kinetic blast", "wander", "wand", "caster", "elementalist"]):
        prefs["playstyle"] = "caster"
        if "kinetic blast" in text:
            add_alias(prefs, "kinetic_blast")
        return

    if has_any(text, ["boneshatter", "slayer", "melee", "ice crash"]):
        prefs["playstyle"] = "melee"
        if "boneshatter" in text:
            add_alias(prefs, "boneshatter")
        if "slayer" in text:
            add_alias(prefs, "slayer")
        return


def infer_goal(text: str, prefs: dict[str, Any]) -> None:
    mapping_intent = has_any(
        text,
        [
            "mapper",
            "mapping",
            "maps",
            "fast mapper",
            "zoomy",
            "zoom",
            "clear speed",
            "heist",
        ],
    )
    bossing_intent = has_any(
        text,
        [
            "boss",
            "bossing",
            "ubers",
            "voidstones",
        ],
    )

    if mapping_intent:
        prefs["goal"] = "fast mapper"

    if bossing_intent:
        prefs["goal"] = "bossing"


def infer_budget(text: str, prefs: dict[str, Any]) -> None:
    if has_any(text, ["low budget", "cheap", "budget", "starter budget"]):
        prefs["budget"] = "low"


def infer_speed(text: str, prefs: dict[str, Any]) -> None:
    if has_any(text, ["fast", "zoomy", "zoom", "speedy", "high speed"]):
        prefs["speed"] = "high"


def infer_tankiness(text: str, prefs: dict[str, Any]) -> None:
    if has_any(text, ["safe", "tanky", "tanky build", "hardcore viable", "hc viable"]):
        prefs["tankiness"] = "high"

    if "hardcore" in text or re.search(r"\bhc\b", text):
        prefs["hardcore"] = True
        prefs["tankiness"] = "high"


def infer_league_starter(text: str, prefs: dict[str, Any]) -> None:
    if has_any(text, ["league starter", "starter", "start the league"]):
        prefs["league_starter"] = True


def infer_apm_and_complexity(text: str, prefs: dict[str, Any]) -> None:
    if has_any(text, ["low apm", "few buttons", "easy to play", "simple rotation"]):
        prefs["apm"] = "low"

    if has_any(text, ["beginner", "beginner friendly", "new player", "easy", "simple", "low complexity"]):
        prefs["complexity"] = "low"

    if has_any(text, ["beginner", "beginner friendly", "new player"]):
        prefs["apm"] = prefs.get("apm", "low")


def infer_content_tags(text: str, prefs: dict[str, Any]) -> None:
    if "maps" in text or "mapping" in text or "mapper" in text:
        add_content_tag(prefs, "maps")

    if "boss" in text or "bossing" in text or "ubers" in text or "voidstones" in text:
        add_content_tag(prefs, "bossing")

    if "heist" in text:
        add_content_tag(prefs, "heist")

    if "sanctum" in text:
        add_content_tag(prefs, "sanctum")

    if "delve" in text:
        add_content_tag(prefs, "delve")

    if "blight" in text:
        add_content_tag(prefs, "blight")

    if "expedition" in text:
        add_content_tag(prefs, "expedition")

    if "simulacrum" in text:
        add_content_tag(prefs, "simulacrum")


def infer_stage(text: str, prefs: dict[str, Any]) -> None:
    """
    Stage inference rules are intentionally ordered from most explicit to most inferred.

    Key intent:
    - explicit "leveling/campaign/acts" => leveling
    - explicit "early maps/white maps/yellow maps" => early_maps
    - explicit "endgame/red maps/voidstones/ubers" => endgame

    Then fallback intent rules:
    - bossing-oriented prompts default to endgame, even if they also say "league starter"
      because the user is usually asking for the stage they want the build to perform at
    - fast mapper + league starter usually means early_maps
    - plain league starter with no stronger signal means leveling
    """
    explicit_leveling = has_any(text, ["leveling", "campaign", "act ", "acts"])
    explicit_early_maps = has_any(text, ["early maps", "white maps", "yellow maps", "atlas start"])
    explicit_endgame = has_any(text, ["endgame", "red maps", "voidstones", "ubers"])

    if explicit_leveling:
        prefs["stage"] = "leveling"
        return

    if explicit_early_maps:
        prefs["stage"] = "early_maps"
        return

    if explicit_endgame:
        prefs["stage"] = "endgame"
        return

    league_starter = bool(prefs.get("league_starter"))
    goal = prefs.get("goal")
    playstyle = prefs.get("playstyle")
    tanky = prefs.get("tankiness") == "high"
    low_apm = prefs.get("apm") == "low"
    low_complexity = prefs.get("complexity") == "low"
    tags = set(prefs.get("content_tags", []))

    bossing_intent = goal == "bossing" or "bossing" in tags
    mapping_intent = goal == "fast mapper" or "maps" in tags or "heist" in tags

    # Strong endgame intent:
    # bossing / safe bossing / beginner bossing / low-apm bossing requests should land on endgame
    if bossing_intent:
        prefs["stage"] = "endgame"
        return

    # League-starter mapper prompts usually want the "first useful atlas" version, not campaign
    if league_starter and mapping_intent:
        prefs["stage"] = "early_maps"
        return

    # Beginner/low-apm summoner prompts without explicit mapping-only intent are usually asking
    # for the stable finished recommendation, not an act-by-act leveling setup.
    if playstyle == "minion" and (low_apm or low_complexity or tanky):
        prefs["stage"] = "endgame"
        return

    # Generic safe/tanky prompts without bossing still lean later rather than campaign
    if tanky and mapping_intent:
        prefs["stage"] = "endgame"
        return

    # Plain league starter fallback
    if league_starter:
        prefs["stage"] = "leveling"
        return

    # Mapping fallback
    if mapping_intent:
        prefs["stage"] = "early_maps"
        return


def cleanup_prefs(prefs: dict[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}

    key_order = [
        "source_prompt",
        "aliases",
        "playstyle",
        "goal",
        "budget",
        "speed",
        "tankiness",
        "league_starter",
        "stage",
        "apm",
        "complexity",
        "hardcore",
        "content_tags",
    ]

    for key in key_order:
        value = prefs.get(key)
        if value is None:
            continue
        if isinstance(value, list) and not value:
            continue
        cleaned[key] = value

    return cleaned


def parse_prompt(prompt: str) -> dict[str, Any]:
    raw = prompt.strip()
    text = normalize_text(raw)

    prefs: dict[str, Any] = {
        "source_prompt": raw,
    }

    infer_playstyle(text, prefs)
    infer_goal(text, prefs)
    infer_budget(text, prefs)
    infer_speed(text, prefs)
    infer_tankiness(text, prefs)
    infer_league_starter(text, prefs)
    infer_apm_and_complexity(text, prefs)
    infer_content_tags(text, prefs)
    infer_stage(text, prefs)

    return cleanup_prefs(prefs)


def parse_prompt_to_prefs(prompt: str) -> dict[str, Any]:
    return parse_prompt(prompt)


def print_summary(prompt: str, prefs: dict[str, Any], out_path: str | None) -> None:
    print("=" * 60)
    print("PROMPT TO PREFS")
    print("=" * 60)
    print(f"Prompt: {prompt}")
    print("Parsed preferences:")
    for key, value in prefs.items():
        print(f"  - {key}: {value}")
    if out_path:
        print(f"Saved: {out_path}")
    print("=" * 60)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Parse a natural language build prompt into preferences JSON.")
    parser.add_argument("--prompt", required=True, help="Natural language prompt")
    parser.add_argument("--out", help="Path to save preferences JSON")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    prefs = parse_prompt(args.prompt)

    if args.out:
        Path(args.out).write_text(
            json.dumps(prefs, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    print_summary(args.prompt, prefs, args.out)


if __name__ == "__main__":
    main()