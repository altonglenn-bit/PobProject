from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path


def load_build(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_build(path: str, build: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(build, f, indent=2, ensure_ascii=False)


def set_notes(build: dict, notes: str | None) -> None:
    if notes is not None:
        build["notes"] = notes


def set_class_name(build: dict, class_name: str | None) -> None:
    if class_name is not None:
        build["class_name"] = class_name


def set_ascendancy_name(build: dict, ascendancy_name: str | None) -> None:
    if ascendancy_name is not None:
        build["ascendancy_name"] = ascendancy_name


def set_level(build: dict, level: int | None) -> None:
    if level is not None:
        build["level"] = level


def replace_gem_name(build: dict, old_name: str | None, new_name: str | None) -> int:
    if not old_name or not new_name:
        return 0

    replacements = 0

    for group in build.get("skill_groups", []):
        for gem in group.get("gems", []):
            if gem.get("name") == old_name:
                gem["name"] = new_name
                replacements += 1

    if replacements > 0:
        skill_names = []
        seen = set()

        for group in build.get("skill_groups", []):
            for gem in group.get("gems", []):
                name = gem.get("name")
                if name and name not in seen:
                    seen.add(name)
                    skill_names.append(name)

        build["skill_names"] = skill_names

    return replacements


def remove_gem_name(build: dict, gem_name: str | None) -> int:
    if not gem_name:
        return 0

    removed = 0

    for group in build.get("skill_groups", []):
        old_gems = group.get("gems", [])
        new_gems = []

        for gem in old_gems:
            if gem.get("name") == gem_name:
                removed += 1
            else:
                new_gems.append(gem)

        group["gems"] = new_gems

    skill_names = []
    seen = set()

    for group in build.get("skill_groups", []):
        for gem in group.get("gems", []):
            name = gem.get("name")
            if name and name not in seen:
                seen.add(name)
                skill_names.append(name)

    build["skill_names"] = skill_names
    return removed


def add_gem_to_group(build: dict, group_index_1_based: int | None, gem_name: str | None) -> bool:
    if group_index_1_based is None or not gem_name:
        return False

    groups = build.get("skill_groups", [])
    idx = group_index_1_based - 1

    if idx < 0 or idx >= len(groups):
        return False

    groups[idx].setdefault("gems", []).append(
        {
            "name": gem_name,
            "enabled": None,
            "level": None,
            "quality": None,
            "skill_id": None,
        }
    )

    skill_names = build.get("skill_names", [])
    if gem_name not in skill_names:
        skill_names.append(gem_name)
        build["skill_names"] = skill_names

    return True


def rename_tree_title(build: dict, new_title: str | None, tree_index_1_based: int | None = 1) -> bool:
    if not new_title:
        return False

    trees = build.get("trees", [])
    idx = (tree_index_1_based or 1) - 1

    if idx < 0 or idx >= len(trees):
        return False

    trees[idx]["title"] = new_title
    return True


def set_config_value(build: dict, key: str | None, value: str | None) -> bool:
    if not key:
        return False

    if "config" not in build or not isinstance(build["config"], dict):
        build["config"] = {}

    parsed = parse_cli_value(value)
    build["config"][key] = parsed
    return True


def parse_cli_value(value: str | None):
    if value is None:
        return None

    low = value.strip().lower()

    if low == "true":
        return True
    if low == "false":
        return False
    if low == "none" or low == "null":
        return None

    try:
        return int(value)
    except Exception:
        pass

    try:
        return float(value)
    except Exception:
        pass

    return value


def ensure_out_path(input_path: str, output_path: str | None) -> str:
    if output_path:
        return output_path

    p = Path(input_path)
    return str(p.with_name(f"{p.stem}_mutated{p.suffix}"))


def summarize_changes(
    input_path: str,
    output_path: str,
    notes: str | None,
    class_name: str | None,
    ascendancy_name: str | None,
    level: int | None,
    gem_replacements: int,
    gems_removed: int,
    gem_added: bool,
    tree_renamed: bool,
    config_changed: bool,
) -> None:
    print("=" * 60)
    print("MUTATION SUMMARY")
    print("=" * 60)
    print(f"Input:  {input_path}")
    print(f"Output: {output_path}")

    if notes is not None:
        print("Updated notes")
    if class_name is not None:
        print(f"Updated class_name -> {class_name}")
    if ascendancy_name is not None:
        print(f"Updated ascendancy_name -> {ascendancy_name}")
    if level is not None:
        print(f"Updated level -> {level}")
    if gem_replacements:
        print(f"Replaced gems: {gem_replacements}")
    if gems_removed:
        print(f"Removed gems: {gems_removed}")
    if gem_added:
        print("Added gem to skill group")
    if tree_renamed:
        print("Renamed tree title")
    if config_changed:
        print("Updated config value")
    print("=" * 60)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Mutate a parsed Path of Building build.json file."
    )

    parser.add_argument(
        "--in",
        dest="input_path",
        default="build.json",
        help="Input JSON file. Default: build.json",
    )
    parser.add_argument(
        "--out",
        dest="output_path",
        default=None,
        help="Output JSON file. Default: <input>_mutated.json",
    )

    parser.add_argument("--set-notes", dest="notes", default=None)
    parser.add_argument("--set-class", dest="class_name", default=None)
    parser.add_argument("--set-ascendancy", dest="ascendancy_name", default=None)
    parser.add_argument("--set-level", dest="level", type=int, default=None)

    parser.add_argument(
        "--replace-gem",
        nargs=2,
        metavar=("OLD_NAME", "NEW_NAME"),
        default=None,
        help='Example: --replace-gem "Hatred" "Determination"',
    )

    parser.add_argument(
        "--remove-gem",
        dest="remove_gem",
        default=None,
        help='Example: --remove-gem "Clarity"',
    )

    parser.add_argument(
        "--add-gem-to-group",
        nargs=2,
        metavar=("GROUP_INDEX", "GEM_NAME"),
        default=None,
        help='Example: --add-gem-to-group 1 "Determination"',
    )

    parser.add_argument(
        "--rename-tree",
        dest="tree_title",
        default=None,
        help='Example: --rename-tree "League Starter Tree"',
    )
    parser.add_argument(
        "--tree-index",
        dest="tree_index",
        type=int,
        default=1,
        help="Tree index for --rename-tree. Default: 1",
    )

    parser.add_argument(
        "--set-config",
        nargs=2,
        metavar=("KEY", "VALUE"),
        default=None,
        help='Example: --set-config enemyLevel 32 or --set-config condition true',
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    build = load_build(args.input_path)
    mutated = deepcopy(build)

    set_notes(mutated, args.notes)
    set_class_name(mutated, args.class_name)
    set_ascendancy_name(mutated, args.ascendancy_name)
    set_level(mutated, args.level)

    gem_replacements = 0
    if args.replace_gem:
        old_name, new_name = args.replace_gem
        gem_replacements = replace_gem_name(mutated, old_name, new_name)

    gems_removed = 0
    if args.remove_gem:
        gems_removed = remove_gem_name(mutated, args.remove_gem)

    gem_added = False
    if args.add_gem_to_group:
        raw_group_index, gem_name = args.add_gem_to_group
        gem_added = add_gem_to_group(mutated, int(raw_group_index), gem_name)

    tree_renamed = False
    if args.tree_title:
        tree_renamed = rename_tree_title(mutated, args.tree_title, args.tree_index)

    config_changed = False
    if args.set_config:
        key, value = args.set_config
        config_changed = set_config_value(mutated, key, value)

    output_path = ensure_out_path(args.input_path, args.output_path)
    save_build(output_path, mutated)

    summarize_changes(
        input_path=args.input_path,
        output_path=output_path,
        notes=args.notes,
        class_name=args.class_name,
        ascendancy_name=args.ascendancy_name,
        level=args.level,
        gem_replacements=gem_replacements,
        gems_removed=gems_removed,
        gem_added=gem_added,
        tree_renamed=tree_renamed,
        config_changed=config_changed,
    )


if __name__ == "__main__":
    main()