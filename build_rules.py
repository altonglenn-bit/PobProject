from __future__ import annotations

from copy import deepcopy


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


def set_class(build: dict, class_name: str | None = None, ascendancy_name: str | None = None) -> None:
    if class_name is not None:
        build["class_name"] = class_name
    if ascendancy_name is not None:
        build["ascendancy_name"] = ascendancy_name


def set_config_value(build: dict, key: str, value) -> None:
    build.setdefault("config", {})
    build["config"][key] = value


def select_tree_by_title(build: dict, desired_title: str) -> bool:
    trees = build.get("trees", [])
    if not trees:
        return False

    desired_norm = (desired_title or "").strip().lower()
    if not desired_norm:
        return False

    for i, tree in enumerate(trees):
        title = (tree.get("title") or "").strip().lower()
        if title == desired_norm:
            if i != 0:
                chosen = trees.pop(i)
                trees.insert(0, chosen)
            return True

    return False


def rename_first_tree(build: dict, title: str) -> bool:
    trees = build.get("trees", [])
    if not trees:
        return False
    trees[0]["title"] = title
    return True


def _group_gem_names(group: dict) -> list[str]:
    return [g.get("name") for g in group.get("gems", []) if g.get("name")]


def _group_contains_gem(group: dict, gem_name: str) -> bool:
    target = (gem_name or "").strip().lower()
    if not target:
        return False
    for name in _group_gem_names(group):
        if (name or "").strip().lower() == target:
            return True
    return False


def select_skill_group_by_gem_name(build: dict, gem_name: str) -> bool:
    groups = build.get("skill_groups", [])
    if not groups:
        return False

    for i, group in enumerate(groups):
        if _group_contains_gem(group, gem_name):
            if i != 0:
                chosen = groups.pop(i)
                groups.insert(0, chosen)
            return True

    return False


def remove_skill_groups_containing_gems(build: dict, gem_names: list[str]) -> int:
    if not gem_names:
        return 0

    targets = {(name or "").strip().lower() for name in gem_names if name}
    if not targets:
        return 0

    old_groups = build.get("skill_groups", [])
    new_groups = []
    removed = 0

    for group in old_groups:
        names = {(name or "").strip().lower() for name in _group_gem_names(group)}
        if names.intersection(targets):
            removed += 1
        else:
            new_groups.append(group)

    build["skill_groups"] = new_groups
    rebuild_skill_names(build)
    return removed


def keep_only_skill_groups_with_gems(build: dict, gem_names: list[str]) -> int:
    if not gem_names:
        return 0

    targets = {(name or "").strip().lower() for name in gem_names if name}
    if not targets:
        return 0

    old_groups = build.get("skill_groups", [])
    kept = []
    removed = 0

    for group in old_groups:
        names = {(name or "").strip().lower() for name in _group_gem_names(group)}
        if names.intersection(targets):
            kept.append(group)
        else:
            removed += 1

    if kept:
        build["skill_groups"] = kept
        rebuild_skill_names(build)

    return removed


def apply_primary_skill_setup(
    build: dict,
    preferred_group_gem: str | None = None,
    remove_alternate_groups_with_gems: list[str] | None = None,
    keep_only_groups_with_gems: list[str] | None = None,
) -> list[str]:
    changes: list[str] = []

    if preferred_group_gem:
        if select_skill_group_by_gem_name(build, preferred_group_gem):
            changes.append(f"Selected primary skill group containing '{preferred_group_gem}'")

    if keep_only_groups_with_gems:
        removed = keep_only_skill_groups_with_gems(build, keep_only_groups_with_gems)
        if removed:
            changes.append(
                f"Removed {removed} non-primary skill group(s) using keep_only_groups_with_gems"
            )

    if remove_alternate_groups_with_gems:
        removed = remove_skill_groups_containing_gems(build, remove_alternate_groups_with_gems)
        if removed:
            changes.append(
                f"Removed {removed} alternate skill group(s) matching remove_alternate_groups_with_gems"
            )

    return changes


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
        if add_gem_to_group(build, 2, "Grace"):
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
        if add_gem_to_group(build, 2, "Grace"):
            changes.append("Added Grace to group 2")

    else:
        raise ValueError(f"Unknown aura_package: {aura_package}")

    return changes


def apply_main_skill(build: dict, main_skill: str | None, target_group: int = 4) -> list[str]:
    if not main_skill:
        return []

    groups = build.get("skill_groups", [])
    if not groups:
        add_gem_to_group(build, 1, main_skill)
        return [f"Added main skill {main_skill} to new group 1"]

    idx = target_group - 1
    if idx < 0 or idx >= len(groups):
        idx = 0

    gems = groups[idx].get("gems", [])
    if not gems:
        groups[idx].setdefault("gems", []).append(
            {
                "name": main_skill,
                "enabled": True,
                "level": None,
                "quality": None,
                "skill_id": None,
            }
        )
        rebuild_skill_names(build)
        return [f"Added main skill {main_skill} to group {idx + 1}"]

    old_name = gems[0].get("name")
    gems[0]["name"] = main_skill
    rebuild_skill_names(build)

    if old_name and old_name != main_skill:
        return [f"Replaced main skill {old_name} -> {main_skill} in group {idx + 1}"]
    return [f"Set main skill to {main_skill} in group {idx + 1}"]


def apply_movement(build: dict, movement_skills: list[str] | None, target_group: int = 5) -> list[str]:
    if not movement_skills:
        return []

    movement_skill_names = {
        "Leap Slam",
        "Frostblink",
        "Dash",
        "Flame Dash",
        "Shield Charge",
        "Whirling Blades",
        "Blink Arrow",
    }

    groups = build.get("skill_groups", [])
    if not groups:
        build["skill_groups"] = [{"label": None, "slot": None, "enabled": True, "gems": []}]
        groups = build["skill_groups"]

    idx = target_group - 1
    if idx < 0 or idx >= len(groups):
        idx = min(len(groups) - 1, 0)

    # Remove movement gems from every group first, so we don't duplicate them.
    for group in groups:
        group["gems"] = [
            gem for gem in group.get("gems", [])
            if gem.get("name") not in movement_skill_names
        ]

    # Then place the desired movement setup only into the target group.
    target = groups[idx]
    target_gems = target.setdefault("gems", [])

    for skill in movement_skills:
        target_gems.append(
            {
                "name": skill,
                "enabled": True,
                "level": None,
                "quality": None,
                "skill_id": None,
            }
        )

    rebuild_skill_names(build)
    return [f"Set movement group {idx + 1} to: {', '.join(movement_skills)}"]


def apply_stage(base_build: dict, archetype: dict, stage_name: str) -> tuple[dict, list[str]]:
    if stage_name not in archetype["stages"]:
        raise ValueError(f"Unknown stage: {stage_name}")

    stage = archetype["stages"][stage_name]
    build = deepcopy(base_build)
    changes: list[str] = []

    set_class(build, archetype.get("base_class"), archetype.get("default_ascendancy"))
    changes.append(
        f"Set class={build.get('class_name')} ascendancy={build.get('ascendancy_name')}"
    )

    if stage.get("level") is not None:
        set_level(build, int(stage["level"]))
        changes.append(f"Set level={stage['level']}")

    if stage.get("tree_title"):
        if select_tree_by_title(build, stage["tree_title"]):
            changes.append(f"Selected tree '{stage['tree_title']}'")
        elif rename_first_tree(build, stage["tree_title"]):
            changes.append(f"Renamed first tree to '{stage['tree_title']}'")

    changes.extend(
        apply_primary_skill_setup(
            build,
            preferred_group_gem=stage.get("preferred_group_gem")
            or archetype.get("preferred_group_gem"),
            remove_alternate_groups_with_gems=stage.get("remove_alternate_groups_with_gems")
            or archetype.get("remove_alternate_groups_with_gems"),
            keep_only_groups_with_gems=stage.get("keep_only_groups_with_gems")
            or archetype.get("keep_only_groups_with_gems"),
        )
    )

    changes.extend(
        apply_main_skill(
            build,
            stage.get("main_skill_override") or archetype.get("default_main_skill"),
            int(stage.get("main_skill_group") or archetype.get("default_main_skill_group", 4)),
        )
    )

    movement_group = int(stage.get("movement_group") or archetype.get("default_movement_group", 5))
    movement_skills = stage.get("movement_skills") or archetype.get("default_movement_skills")
    changes.extend(apply_movement(build, movement_skills, movement_group))

    changes.extend(apply_aura_package(build, stage.get("aura_package")))

    for gem_name in stage.get("remove_gems", []) or []:
        removed = remove_gem_everywhere(build, gem_name)
        if removed:
            changes.append(f"Removed {gem_name} ({removed} occurrence(s))")

    for item in stage.get("add_gems", []) or []:
        if add_gem_to_group(build, int(item["group"]), item["name"]):
            changes.append(f"Added {item['name']} to group {item['group']}")

    for key, value in (stage.get("config_overrides") or {}).items():
        set_config_value(build, key, value)
        changes.append(f"Set config {key}={value}")

    notes = [
        f"Archetype stage: {stage_name}",
        stage.get("notes", ""),
        "Applied changes:",
        *[f"- {c}" for c in changes],
    ]
    set_notes(build, "\n".join(line for line in notes if line))

    rebuild_skill_names(build)
    return build, changes