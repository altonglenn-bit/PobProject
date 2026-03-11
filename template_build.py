from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path


BASE_BUILD_FILE = "build.json"


def load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def ensure_out_path(template_name: str, output_path: str | None) -> str:
    if output_path:
        return output_path
    return f"{template_name}.json"


def rebuild_skill_names(build: dict) -> None:
    seen = set()
    names = []
    for group in build.get("skill_groups", []):
        for gem in group.get("gems", []):
            name = gem.get("name")
            if name and name not in seen:
                seen.add(name)
                names.append(name)
    build["skill_names"] = names


def replace_gem_everywhere(build: dict, old_name: str, new_name: str) -> int:
    count = 0
    for group in build.get("skill_groups", []):
        for gem in group.get("gems", []):
            if gem.get("name") == old_name:
                gem["name"] = new_name
                count += 1
    rebuild_skill_names(build)
    return count


def remove_gem_everywhere(build: dict, gem_name: str) -> int:
    removed = 0
    for group in build.get("skill_groups", []):
        new_gems = []
        for gem in group.get("gems", []):
            if gem.get("name") == gem_name:
                removed += 1
            else:
                new_gems.append(gem)
        group["gems"] = new_gems
    rebuild_skill_names(build)
    return removed


def add_gem_to_group(build: dict, group_index_1_based: int, gem_name: str) -> bool:
    idx = group_index_1_based - 1
    groups = build.get("skill_groups", [])
    if idx < 0 or idx >= len(groups):
        return False

    groups[idx].setdefault("gems", []).append(
        {
            "name": gem_name,
            "enabled": True,
            "level": None,
            "quality": None,
            "skill_id": None,
        }
    )
    rebuild_skill_names(build)
    return True


def set_notes(build: dict, notes: str) -> None:
    build["notes"] = notes


def set_level(build: dict, level: int) -> None:
    build["level"] = level


def set_class(build: dict, class_name: str, ascendancy_name: str | None = None) -> None:
    build["class_name"] = class_name
    if ascendancy_name is not None:
        build["ascendancy_name"] = ascendancy_name


def rename_tree(build: dict, title: str, tree_index_1_based: int = 1) -> bool:
    idx = tree_index_1_based - 1
    trees = build.get("trees", [])
    if idx < 0 or idx >= len(trees):
        return False
    trees[idx]["title"] = title
    return True


def set_config_value(build: dict, key: str, value) -> None:
    build.setdefault("config", {})
    build["config"][key] = value


def apply_template(base_build: dict, template_name: str) -> dict:
    b = deepcopy(base_build)

    if template_name == "ice_crash_shadow_base":
        set_notes(
            b,
            "Template: Ice Crash Shadow base\nImported from source build and normalized for mutation/export.",
        )
        rename_tree(b, "Ice Crash Shadow Base")
        return b

    if template_name == "ice_crash_shadow_determination":
        replace_gem_everywhere(b, "Hatred", "Determination")
        set_notes(
            b,
            "Template: Ice Crash Shadow Determination\nAura package changed from Hatred to Determination.",
        )
        rename_tree(b, "Ice Crash Shadow Determination")
        return b

    if template_name == "ice_crash_shadow_no_clarity":
        remove_gem_everywhere(b, "Clarity")
        set_notes(
            b,
            "Template: Ice Crash Shadow No Clarity\nClarity removed for alternative mana setup testing.",
        )
        rename_tree(b, "Ice Crash Shadow No Clarity")
        return b

    if template_name == "ice_crash_shadow_level_40":
        set_level(b, 40)
        set_notes(
            b,
            "Template: Ice Crash Shadow Level 40\nLevel bumped for progression testing.",
        )
        rename_tree(b, "Ice Crash Shadow Level 40")
        set_config_value(b, "enemyLevel", 40)
        return b

    if template_name == "ice_crash_shadow_tanky":
        replace_gem_everywhere(b, "Hatred", "Determination")
        remove_gem_everywhere(b, "Herald of Ice")
        add_gem_to_group(b, 2, "Grace")
        set_notes(
            b,
            "Template: Ice Crash Shadow Tanky\nHatred -> Determination, Herald of Ice removed, Grace added.",
        )
        rename_tree(b, "Ice Crash Shadow Tanky")
        return b

    raise ValueError(f"Unknown template: {template_name}")


def list_templates() -> list[str]:
    return [
        "ice_crash_shadow_base",
        "ice_crash_shadow_determination",
        "ice_crash_shadow_no_clarity",
        "ice_crash_shadow_level_40",
        "ice_crash_shadow_tanky",
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create a template-derived build JSON from a base parsed build."
    )
    parser.add_argument(
        "--base",
        dest="base_path",
        default=BASE_BUILD_FILE,
        help="Base build JSON. Default: build.json",
    )
    parser.add_argument(
        "--template",
        dest="template_name",
        default=None,
        help="Template name to generate.",
    )
    parser.add_argument(
        "--out",
        dest="output_path",
        default=None,
        help="Output JSON file. Default: <template>.json",
    )
    parser.add_argument(
        "--list",
        dest="list_only",
        action="store_true",
        help="List available templates.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.list_only:
        print("Available templates:")
        for name in list_templates():
            print(f"  - {name}")
        return

    if not args.template_name:
        raise SystemExit("Please provide --template, or use --list.")

    base_build = load_json(args.base_path)
    result = apply_template(base_build, args.template_name)

    output_path = ensure_out_path(args.template_name, args.output_path)
    save_json(output_path, result)

    print("=" * 60)
    print("TEMPLATE BUILD SUMMARY")
    print("=" * 60)
    print(f"Base:     {args.base_path}")
    print(f"Template: {args.template_name}")
    print(f"Output:   {output_path}")
    print(f"Class:    {result.get('class_name')}")
    print(f"Asc:      {result.get('ascendancy_name')}")
    print(f"Level:    {result.get('level')}")
    print(f"Skills:   {len(result.get('skill_names', []))}")
    print("=" * 60)


if __name__ == "__main__":
    main()