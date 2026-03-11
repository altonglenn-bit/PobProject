from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from prompt_to_prefs import parse_prompt_to_prefs
import recommend_build


def recommend_from_prefs(prefs: dict) -> dict:
    if hasattr(recommend_build, "recommend_build"):
        return recommend_build.recommend_build(prefs)
    if hasattr(recommend_build, "recommend_build_from_prefs"):
        return recommend_build.recommend_build_from_prefs(prefs)
    if hasattr(recommend_build, "choose_recommendation"):
        return recommend_build.choose_recommendation(prefs)
    raise AttributeError(
        "No supported recommendation function found in recommend_build.py. "
        "Expected recommend_build, recommend_build_from_prefs, or choose_recommendation."
    )


def assert_pick(prompt: str, expected_archetype: str, expected_stage: str):
    prefs = parse_prompt_to_prefs(prompt)
    result = recommend_from_prefs(prefs)
    assert result["archetype"] == expected_archetype
    assert result["stage"] == expected_stage


def test_beginner_friendly_summoner_maps_bosses():
    assert_pick(
        "I want a beginner friendly summoner for maps and bosses",
        "spectre_summoner_necromancer",
        "endgame",
    )


def test_safe_red_maps_voidstones():
    assert_pick(
        "I want a safe build for red maps and voidstones",
        "kinetic_fusillade_totem",
        "endgame",
    )


def test_bossing_ubers():
    assert_pick(
        "I want a bossing build for ubers",
        "kinetic_fusillade_totem",
        "endgame",
    )


def test_fast_bow_mapper_low_budget():
    assert_pick(
        "I want a fast bow mapper league starter on low budget",
        "lightning_arrow_deadeye",
        "early_maps",
    )


def test_low_apm_minion_safe_bosses():
    assert_pick(
        "I want a low apm minion league starter that is safe for bosses",
        "spectre_summoner_necromancer",
        "endgame",
    )


def test_safe_totem_bosser():
    assert_pick(
        "I want a safe totem build for bossing",
        "kinetic_fusillade_totem",
        "endgame",
    )


def test_tanky_melee_low_apm_bosser():
    assert_pick(
        "I want a tanky melee league starter with low apm that can do bosses",
        "boneshatter_slayer",
        "endgame",
    )


def test_zoomy_bow_mapper():
    assert_pick(
        "I want a zoomy bow mapper for heist and maps on a low budget",
        "lightning_arrow_deadeye",
        "early_maps",
    )


def test_fast_caster_mapper():
    assert_pick(
        "I want a fast caster mapper for heist and maps",
        "elementalist_kinetic_blast",
        "early_maps",
    )


def test_prompt_parser_extracts_expected_preferences():
    prefs = parse_prompt_to_prefs(
        "I want a safe totem league starter for bossing"
    )

    assert prefs.get("playstyle") == "totem"
    assert prefs.get("league_starter") is True
    assert prefs.get("tankiness") == "high"
    assert "bossing" in prefs.get("content_tags", [])
