from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Lightweight consistency check for JSON/XML/encoded outputs."
    )
    parser.add_argument("--json", dest="json_path", default="build.json")
    parser.add_argument("--xml", dest="xml_path", default="build.xml")
    parser.add_argument("--encoded", dest="encoded_path", default="build_encoded.txt")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    problems: list[str] = []

    if not Path(args.json_path).exists():
        problems.append(f"Missing JSON: {args.json_path}")
    if not Path(args.xml_path).exists():
        problems.append(f"Missing XML: {args.xml_path}")
    if not Path(args.encoded_path).exists():
        problems.append(f"Missing encoded text: {args.encoded_path}")

    if problems:
        print("Problems found:")
        for p in problems:
            print(f"  - {p}")
        raise SystemExit(1)

    build = load_json(args.json_path)

    with open(args.xml_path, "r", encoding="utf-8") as f:
        xml_text = f.read()

    with open(args.encoded_path, "r", encoding="utf-8") as f:
        encoded_text = f.read().strip()

    skill_names = build.get("skill_names", [])
    missing_from_xml = [name for name in skill_names if name and name not in xml_text]

    print("=" * 60)
    print("ROUNDTRIP TEST")
    print("=" * 60)
    print(f"JSON:    {args.json_path}")
    print(f"XML:     {args.xml_path}")
    print(f"ENCODED: {args.encoded_path}")
    print(f"Encoded length: {len(encoded_text)}")
    print(f"Items: {len(build.get('items', []))}")
    print(f"Skill groups: {len(build.get('skill_groups', []))}")
    print(f"Skill names: {len(skill_names)}")

    if missing_from_xml:
        print("Skill names missing from XML:")
        for name in missing_from_xml:
            print(f"  - {name}")
    else:
        print("All skill names found in XML.")

    print("=" * 60)


if __name__ == "__main__":
    main()