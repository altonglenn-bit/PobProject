from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def run_step(cmd: list[str]) -> None:
    cmd = [str(part) for part in cmd if part is not None]
    print(f"> {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def slugify(value: str, max_words: int = 6, max_len: int = 48) -> str:
    words = re.findall(r"[a-z0-9]+", value.lower())
    if not words:
        return "prompt_build"

    stopwords = {
        "i",
        "want",
        "a",
        "an",
        "the",
        "for",
        "that",
        "with",
        "and",
        "to",
        "of",
        "on",
        "build",
        "please",
        "can",
        "me",
    }
    filtered = [w for w in words if w not in stopwords]
    if not filtered:
        filtered = words

    slug_words = filtered[:max_words]
    slug = "_".join(slug_words)
    slug = slug[:max_len].strip("_")
    return slug or "prompt_build"


def prefix_from_prompt(prompt: str) -> str:
    return slugify(prompt)


def default_prefix_for_source(
    archetype: str | None,
    stage: str | None,
    spec: str | None,
    recommend: str | None,
    prompt: str | None,
) -> str:
    if spec:
        return Path(spec).stem
    if archetype and stage:
        return f"{archetype}_{stage}"
    if recommend:
        return "recommended_build"
    if prompt:
        return prefix_from_prompt(prompt)
    return "generated_build"


def print_prompt_details(prefs: dict, recommendation: dict) -> None:
    print("=" * 60)
    print("PROMPT ANALYSIS")
    print("=" * 60)

    source_prompt = prefs.get("source_prompt")
    if source_prompt:
        print(f"Prompt: {source_prompt}")

    print("Parsed preferences:")
    visible_keys = [
        "playstyle",
        "goal",
        "budget",
        "tankiness",
        "speed",
        "apm",
        "complexity",
        "damage",
        "league_starter",
        "stage",
        "hardcore",
        "ssf",
        "trade",
        "content_tags",
    ]
    found_any = False
    for key in visible_keys:
        if key in prefs:
            print(f"  - {key}: {prefs[key]}")
            found_any = True
    if not found_any:
        print("  - (no strong preferences detected)")

    print()
    print("Chosen recommendation:")
    print(f"  - archetype: {recommendation['recommended_archetype']}")
    print(f"  - stage: {recommendation['recommended_stage']}")
    print(f"  - base: {recommendation['base_file']}")
    print(f"  - score: {recommendation['score']}")

    print("  - reasons:")
    if recommendation.get("reasons"):
        for reason in recommendation["reasons"]:
            print(f"    * {reason}")
    else:
        print("    * no strong matching signals")

    print()
    print("Top matches:")
    shortlist = recommendation.get("shortlist", [])
    for idx, entry in enumerate(shortlist, start=1):
        print(f"  {idx}. {entry['archetype']} | stage={entry['stage']} | score={entry['score']}")
        if entry.get("reasons"):
            for reason in entry["reasons"][:5]:
                print(f"     - {reason}")
        else:
            print("     - no strong matching signals")

    print("=" * 60)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a JSON/XML/encoded PoB build from an archetype, spec, recommendation, or prompt."
    )
    parser.add_argument("--archetype", help="Archetype name from archetypes.py")
    parser.add_argument("--stage", help="Stage name for the archetype")
    parser.add_argument("--spec", help="Path to spec JSON file")
    parser.add_argument("--recommend", help="Path to preference JSON file to recommend from")
    parser.add_argument("--prompt", help="Natural-language build request")
    parser.add_argument("--base", help="Optional base build override")
    parser.add_argument("--prefix", help="Output file prefix")
    parser.add_argument(
        "--show-ranking",
        action="store_true",
        help="When using --recommend, print parsed prefs and ranked recommendation details",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    python_exe = sys.executable

    mode_count = sum(
        1
        for value in [args.spec, args.prompt, args.recommend, args.archetype]
        if value is not None
    )
    if mode_count != 1:
        raise ValueError(
            "Choose exactly one source mode: --spec, --prompt, --recommend, or --archetype/--stage."
        )

    if args.archetype and not args.stage:
        raise ValueError("--stage is required when using --archetype.")

    prefix = args.prefix or default_prefix_for_source(
        archetype=args.archetype,
        stage=args.stage,
        spec=args.spec,
        recommend=args.recommend,
        prompt=args.prompt,
    )

    json_out = f"{prefix}.json"
    xml_out = f"{prefix}.xml"
    encoded_out = f"{prefix}_encoded.txt"

    source_summary = None
    prefs_path = None
    recommendation_path = None
    recommendation = None
    prefs = None

    if args.spec:
        run_step(
            [
                python_exe,
                "spec_build.py",
                "--spec",
                args.spec,
                "--base",
                args.base or "build.json",
                "--out",
                json_out,
            ]
        )
        source_summary = f"spec:{args.spec}"

    elif args.recommend:
        recommendation_path = f"{prefix}_recommendation.json"
        run_step(
            [
                python_exe,
                "recommend_build.py",
                "--prefs",
                args.recommend,
                "--out",
                recommendation_path,
            ]
        )
        recommendation = load_json(recommendation_path)

        if args.show_ranking:
            prefs = load_json(args.recommend)
            print_prompt_details(prefs, recommendation)

        run_step(
            [
                python_exe,
                "progression_build.py",
                "--archetype",
                recommendation["recommended_archetype"],
                "--stage",
                recommendation["recommended_stage"],
                *(["--base", args.base] if args.base else []),
                "--out",
                json_out,
            ]
        )
        source_summary = (
            f"recommend:{args.recommend} -> "
            f"archetype:{recommendation['recommended_archetype']} "
            f"stage:{recommendation['recommended_stage']}"
        )

    elif args.prompt:
        prefs_path = f"{prefix}_prefs.json"
        recommendation_path = f"{prefix}_recommendation.json"

        run_step(
            [
                python_exe,
                "prompt_to_prefs.py",
                "--prompt",
                args.prompt,
                "--out",
                prefs_path,
            ]
        )

        run_step(
            [
                python_exe,
                "recommend_build.py",
                "--prefs",
                prefs_path,
                "--out",
                recommendation_path,
            ]
        )

        prefs = load_json(prefs_path)
        recommendation = load_json(recommendation_path)

        print_prompt_details(prefs, recommendation)

        run_step(
            [
                python_exe,
                "progression_build.py",
                "--archetype",
                recommendation["recommended_archetype"],
                "--stage",
                recommendation["recommended_stage"],
                *(["--base", args.base] if args.base else []),
                "--out",
                json_out,
            ]
        )
        source_summary = (
            f"prompt:{args.prompt} -> "
            f"archetype:{recommendation['recommended_archetype']} "
            f"stage:{recommendation['recommended_stage']}"
        )

    else:
        run_step(
            [
                python_exe,
                "progression_build.py",
                "--archetype",
                args.archetype,
                "--stage",
                args.stage,
                *(["--base", args.base] if args.base else []),
                "--out",
                json_out,
            ]
        )
        source_summary = f"archetype:{args.archetype} stage:{args.stage}"

    run_step(
        [
            python_exe,
            "export_build_xml.py",
            "--in",
            json_out,
            "--out",
            xml_out,
        ]
    )

    run_step(
        [
            python_exe,
            "encode_build.py",
            "--in",
            xml_out,
            "--out",
            encoded_out,
        ]
    )

    run_step(
        [
            python_exe,
            "roundtrip_test.py",
            "--json",
            json_out,
            "--xml",
            xml_out,
            "--encoded",
            encoded_out,
        ]
    )

    encoded_text = read_text(encoded_out)

    print("=" * 60)
    print("GENERATE BUILD SUMMARY")
    print("=" * 60)
    print(f"Source:   {source_summary}")
    print(f"Base:     {args.base if args.base else '(auto)'}")
    print(f"Prefix:   {prefix}")
    if prefs_path:
        print(f"Prefs:    {prefs_path}")
    if recommendation_path:
        print(f"Recommend:{recommendation_path}")
    print(f"JSON:     {json_out}")
    print(f"XML:      {xml_out}")
    print(f"ENCODED:  {encoded_out}")
    print("=" * 60)
    print("First 120 chars of import string:")
    print(encoded_text[:120])
    print("=" * 60)


if __name__ == "__main__":
    main()