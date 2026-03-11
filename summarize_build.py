from __future__ import annotations

import argparse
import json


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Summarize a parsed Path of Building build JSON file."
    )
    parser.add_argument(
        "--in",
        dest="input_path",
        default="build.json",
        help="Input JSON file. Default: build.json",
    )
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    with open(args.input_path, "r", encoding="utf-8") as f:
        build = json.load(f)

    print("=" * 60)
    print("BUILD SUMMARY")
    print("=" * 60)
    print(f"Input file: {args.input_path}")
    print(f"Class: {build.get('class_name')}")
    print(f"Ascendancy: {build.get('ascendancy_name')}")
    print(f"Level: {build.get('level')}")
    print(f"Bandit: {build.get('bandit')}")
    print()

    notes = build.get("notes")
    if notes:
        print("Notes:")
        print(notes[:500])
        print()

    trees = build.get("trees", [])
    print(f"Trees: {len(trees)}")
    for i, tree in enumerate(trees[:10], start=1):
        title = tree.get("title") or "(no title)"
        version = tree.get("tree_version") or "(no version)"
        node_count = len(tree.get("nodes", []))
        print(f"  {i}. {title} | version {version} | {node_count} nodes")
    if len(trees) > 10:
        print(f"  ... and {len(trees) - 10} more trees")
    print()

    skill_names = build.get("skill_names", [])
    print(f"Skill names ({len(skill_names)}):")
    for name in skill_names[:20]:
        print(f"  - {name}")
    if len(skill_names) > 20:
        print(f"  ... and {len(skill_names) - 20} more")
    print()

    skill_groups = build.get("skill_groups", [])
    print(f"Skill groups: {len(skill_groups)}")
    for i, group in enumerate(skill_groups[:10], start=1):
        gems = group.get("gems", [])
        gem_names = [g.get("name") for g in gems if g.get("name")]
        label = group.get("label") or "(no label)"
        slot = group.get("slot") or "(no slot)"
        enabled = group.get("enabled")
        print(f"  Group {i}: {', '.join(gem_names) if gem_names else '(empty)'}")
        print(f"    label={label} | slot={slot} | enabled={enabled}")
    if len(skill_groups) > 10:
        print(f"  ... and {len(skill_groups) - 10} more groups")
    print()

    items = build.get("items", [])
    print(f"Items: {len(items)}")
    for i, item in enumerate(items[:10], start=1):
        name = item.get("name") or "(no name)"
        base = item.get("base") or "(no base)"
        rarity = item.get("rarity") or "(unknown rarity)"
        slot = item.get("slot") or "(no slot)"
        print(f"  {i}. {name} | {base} | {rarity} | slot={slot}")
    if len(items) > 10:
        print(f"  ... and {len(items) - 10} more items")
    print()

    config = build.get("config", {})
    print(f"Config fields: {len(config)}")
    config_keys = list(config.keys())
    for k in config_keys[:20]:
        print(f"  - {k}: {config[k]}")
    if len(config) > 20:
        print(f"  ... and {len(config) - 20} more config fields")

    print("=" * 60)


if __name__ == "__main__":
    main()