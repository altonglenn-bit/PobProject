from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path


DEFAULT_BASE = "build.json"


def load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


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


def append_notes(build: dict, text: str) -> None:
    current = build.get("notes") or ""
    build["notes"] = (current + "\n\n" + text).strip() if current else text


def set_level(build: dict, level: int) -> None:
    build["level"] = level


def set_class(build: dict, class_name: str | None = None, ascendancy_name: str | None = None) -> None:
    if class_name is not None:
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


def ensure_out_path(spec_path: str, output_path: str | None) -> str:
    if output_path:
        return output_path
    p = Path(spec_path)
    return str(p.with_suffix(".build.json"))


def parse_value(value):
    return value


def apply_aura_package(build: dict, aura_package: str | None) -> list[str]:
    changes = []
    if not aura_package:
        return changes

    if aura_package == "determination":
        replaced = replace_gem_everywhere(build, "Hatred", "Determination")
        if replaced:
            changes.append(f"Replaced Hatred with Determination ({replaced} occurrence(s))")

    elif aura_package == "grace":
        replaced = replace_gem_everywhere(build, "Hatred", "Grace")
        if replaced:
            changes.append(f"Replaced Hatred with Grace ({replaced} occurrence(s))")

    elif aura_package == "determination_grace":
        replaced = replace_gem_everywhere(build, "Hatred", "Determination")
        if replaced:
            changes.append(f"Replaced Hatred with Determination ({replaced} occurrence(s))")
        added = add_gem_to_group(build, 2, "Grace")
        if added:
            changes.append("Added Grace to group 2")

    elif aura_package == "no_clarity":
        removed = remove_gem_everywhere(build, "Clarity")
        if removed:
            changes.append(f"Removed Clarity ({removed} occurrence(s))")

    elif aura_package == "tanky":
        replaced = replace_gem_everywhere(build, "Hatred", "Determination")
        if replaced:
            changes.append(f"Replaced Hatred with Determination ({replaced} occurrence(s))")
        removed = remove_gem_everywhere(build, "Herald of Ice")
        if removed:
            changes.append(f"Removed Herald of Ice ({removed} occurrence(s))")
        added = add_gem_to_group(build, 2, "Grace")
        if added:
            changes.append("Added Grace to group 2")

    else:
        raise ValueError(f"Unknown aura_package: {aura_package}")

    return changes


def apply_main_skill(build: dict, main_skill: str | None, target_group: int = 4) -> list[str]:
    if not main_skill:
        return []

    idx = target_group - 1
    groups = build.get("skill_groups", [])
    if idx < 0 or idx >= len(groups):
        raise ValueError(f"target_group {target_group} is out of range")

    gems = groups[idx].get("gems", [])
    if not gems:
        add_gem_to_group(build, target_group, main_skill)
        return [f"Added main skill {main_skill} to empty group {target_group}"]

    old_name = gems[0].get("name")
    gems[0]["name"] = main_skill
    rebuild_skill_names(build)

    if old_name and old_name != main_skill:
        return [f"Replaced main skill {old_name} -> {main_skill} in group {target_group}"]
    return [f"Set main skill to {main_skill} in group {target_group}"]


def apply_movement(build: dict, movement_skills: list[str] | None, target_group: int = 5) -> list[str]:
    if not movement_skills:
        return []

    idx = target_group - 1
    groups = build.get("skill_groups", [])
    if idx < 0 or idx >= len(groups):
        raise ValueError(f"target_group {target_group} is out of range")

    group = groups[idx]
    gems = group.setdefault("gems", [])

    kept = []
    for gem in gems:
        name = gem.get("name")
        if name in {"Leap Slam", "Frostblink", "Dash", "Flame Dash", "Shield Charge", "Whirling Blades"}:
            continue
        kept.append(gem)

    for skill in movement_skills:
        kept.append(
            {
                "name": skill,
                "enabled": True,
                "level": None,
                "quality": None,
                "skill_id": None,
            }
        )

    group["gems"] = kept
    rebuild_skill_names(build)
    return [f"Set movement group {target_group} to: {', '.join(movement_skills)}"]


def apply_notes_from_spec(spec: dict, changes: list[str], build: dict) -> None:
    note_lines = []
    if spec.get("title"):
        note_lines.append(f"Title: {spec['title']}")
    if spec.get("variant"):
        note_lines.append(f"Variant: {spec['variant']}")
    if spec.get("playstyle"):
        note_lines.append(f"Playstyle: {spec['playstyle']}")
    if changes:
        note_lines.append("Applied changes:")
        for c in changes:
            note_lines.append(f"- {c}")

    if note_lines:
        set_notes(build, "\n".join(note_lines))


def apply_spec(base_build: dict, spec: dict) -> tuple[dict, list[str]]:
    b = deepcopy(base_build)
    changes: list[str] = []

    if spec.get("class_name") or spec.get("ascendancy_name"):
        set_class(b, spec.get("class_name"), spec.get("ascendancy_name"))
        changes.append(
            f"Set class={b.get('class_name')} ascendancy={b.get('ascendancy_name')}"
        )

    if spec.get("level") is not None:
        set_level(b, int(spec["level"]))
        changes.append(f"Set level={spec['level']}")
        set_config_value(b, "enemyLevel", int(spec["level"]))

    if spec.get("tree_title"):
        renamed = rename_tree(b, spec["tree_title"])
        if renamed:
            changes.append(f"Renamed tree to {spec['tree_title']}")

    changes.extend(apply_aura_package(b, spec.get("aura_package")))
    changes.extend(apply_main_skill(b, spec.get("main_skill"), int(spec.get("main_skill_group", 4))))
    changes.extend(apply_movement(b, spec.get("movement_skills"), int(spec.get("movement_group", 5))))

    for gem_name in spec.get("remove_gems", []) or []:
        removed = remove_gem_everywhere(b, gem_name)
        if removed:
            changes.append(f"Removed {gem_name} ({removed} occurrence(s))")

    for item in spec.get("add_gems", []) or []:
        group_index = int(item["group"])
        gem_name = item["name"]
        added = add_gem_to_group(b, group_index, gem_name)
        if added:
            changes.append(f"Added {gem_name} to group {group_index}")

    for key, value in (spec.get("config_overrides") or {}).items():
        set_config_value(b, key, parse_value(value))
        changes.append(f"Set config {key}={value}")

    apply_notes_from_spec(spec, changes, b)
    rebuild_skill_names(b)
    return b, changes


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a build JSON from a high-level spec file."
    )
    parser.add_argument(
        "--spec",
        required=True,
        help="Path to spec JSON file.",
    )
    parser.add_argument(
        "--base",
        dest="base_path",
        default=DEFAULT_BASE,
        help="Base build JSON. Default: build.json",
    )
    parser.add_argument(
        "--out",
        dest="output_path",
        default=None,
        help="Output build JSON path. Default: <spec>.build.json",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    spec = load_json(args.spec)
    base_build = load_json(args.base_path)

    result, changes = apply_spec(base_build, spec)
    output_path = ensure_out_path(args.spec, args.output_path)
    save_json(output_path, result)

    print("=" * 60)
    print("SPEC BUILD SUMMARY")
    print("=" * 60)
    print(f"Spec:   {args.spec}")
    print(f"Base:   {args.base_path}")
    print(f"Output: {output_path}")
    print(f"Class:  {result.get('class_name')}")
    print(f"Asc:    {result.get('ascendancy_name')}")
    print(f"Level:  {result.get('level')}")
    print(f"Skills: {len(result.get('skill_names', []))}")
    print("Changes:")
    for change in changes:
        print(f"  - {change}")
    print("=" * 60)


if __name__ == "__main__":
    main()