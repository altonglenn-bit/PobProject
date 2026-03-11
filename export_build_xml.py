from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export a parsed/mutated PoB build JSON file back into PoB-style XML."
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
        help="Output XML file. Default: <input>.xml",
    )
    return parser


def load_build(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def ensure_out_path(input_path: str, output_path: str | None) -> str:
    if output_path:
        return output_path
    p = Path(input_path)
    return str(p.with_suffix(".xml"))


def bool_to_str(value) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    return "nil"


def value_to_str(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def indent(elem: ET.Element, level: int = 0) -> None:
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        for child in elem:
            indent(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = i
    if level and (not elem.tail or not elem.tail.strip()):
        elem.tail = i


def build_item_text(item: dict) -> str:
    existing = (item.get("text") or "").strip()
    if existing:
        return existing

    rarity = (item.get("rarity") or "Normal").upper()
    name = item.get("name") or ""
    base = item.get("base") or ""
    item_level = item.get("item_level")
    level_req = item.get("level_req")

    lines: list[str] = [f"Rarity: {rarity}"]
    if name:
        lines.append(name)
    if base and base != name:
        lines.append(base)
    if item_level is not None:
        lines.append(f"Item Level: {item_level}")
    if level_req is not None:
        lines.append(f"Level Requirement: {level_req}")

    return "\n".join(lines).strip()


def export_build_node(root: ET.Element, build: dict) -> None:
    ET.SubElement(
        root,
        "Build",
        {
            "level": value_to_str(build.get("level")),
            "className": value_to_str(build.get("class_name")),
            "ascendClassName": value_to_str(build.get("ascendancy_name")),
            "bandit": value_to_str(build.get("bandit")),
            "targetVersion": "3_0",
            "mainSocketGroup": "1",
            "viewMode": "ITEMS",
        },
    )


def export_tree_node(root: ET.Element, build: dict) -> None:
    tree_root = ET.SubElement(root, "Tree", {"activeSpec": "1"})

    trees = build.get("trees", []) or []
    if not trees:
        ET.SubElement(
            tree_root,
            "Spec",
            {
                "id": "1",
                "title": "",
                "classId": "",
                "ascendClassId": "",
                "treeVersion": "",
                "nodes": "",
                "url": "",
            },
        )
        return

    for idx, tree in enumerate(trees, start=1):
        nodes = tree.get("nodes", []) or []
        ET.SubElement(
            tree_root,
            "Spec",
            {
                "id": str(idx),
                "title": value_to_str(tree.get("title")),
                "classId": value_to_str(tree.get("class_id")),
                "ascendClassId": value_to_str(tree.get("ascend_class_id")),
                "treeVersion": value_to_str(tree.get("tree_version")),
                "nodes": ",".join(str(n) for n in nodes),
                "url": value_to_str(tree.get("url")),
            },
        )


def export_skills_node(root: ET.Element, build: dict) -> None:
    skills_root = ET.SubElement(
        root,
        "Skills",
        {
            "activeSkillSet": "1",
            "sortGemsByDPSField": "CombinedDPS",
        },
    )

    skill_set = ET.SubElement(skills_root, "SkillSet", {"id": "1"})

    for idx, group in enumerate(build.get("skill_groups", []) or [], start=1):
        skill_elem = ET.SubElement(
            skill_set,
            "Skill",
            {
                "enabled": value_to_str(group.get("enabled") if group.get("enabled") is not None else True),
                "slot": value_to_str(group.get("slot")),
                "mainActiveSkill": "1",
                "includeInFullDPS": "true",
                "label": value_to_str(group.get("label")),
                "groupIndex": str(idx),
            },
        )

        for gem in group.get("gems", []) or []:
            ET.SubElement(
                skill_elem,
                "Gem",
                {
                    "nameSpec": value_to_str(gem.get("name")),
                    "skillId": value_to_str(gem.get("skill_id")),
                    "level": value_to_str(gem.get("level")),
                    "quality": value_to_str(gem.get("quality")),
                    "enabled": value_to_str(gem.get("enabled") if gem.get("enabled") is not None else True),
                },
            )


def export_items_node(root: ET.Element, build: dict) -> None:
    items_root = ET.SubElement(root, "Items", {"activeItemSet": "1"})
    item_set = ET.SubElement(items_root, "ItemSet", {"id": "1", "useSecondWeaponSet": "nil"})

    items = build.get("items", []) or []

    for idx, item in enumerate(items, start=1):
        item_id = item.get("id") or str(idx)
        slot = item.get("slot")

        if slot:
            ET.SubElement(
                item_set,
                "Slot",
                {
                    "name": str(slot),
                    "itemId": str(item_id),
                },
            )

    for idx, item in enumerate(items, start=1):
        item_id = item.get("id") or str(idx)
        item_elem = ET.SubElement(items_root, "Item", {"id": str(item_id)})
        item_elem.text = build_item_text(item)


def export_config_node(root: ET.Element, build: dict) -> None:
    config_root = ET.SubElement(root, "Config", {"activeConfigSet": "1"})
    config_set = ET.SubElement(config_root, "ConfigSet", {"id": "1"})

    config = build.get("config", {}) or {}

    for key, value in config.items():
        if key.startswith("placeholder:"):
            name = key.split(":", 1)[1]
            attrs = {"name": name}

            if isinstance(value, bool):
                attrs["boolean"] = "true" if value else "false"
            elif isinstance(value, int) or isinstance(value, float):
                attrs["number"] = str(value)
            elif value is None:
                attrs["number"] = "0"
            else:
                attrs["string"] = str(value)

            ET.SubElement(config_set, "Placeholder", attrs)
        else:
            attrs = {"name": str(key)}

            if isinstance(value, bool):
                attrs["boolean"] = "true" if value else "false"
            elif isinstance(value, int) or isinstance(value, float):
                attrs["number"] = str(value)
            elif value is None:
                attrs["number"] = "0"
            else:
                attrs["string"] = str(value)

            ET.SubElement(config_set, "Input", attrs)


def export_notes_node(root: ET.Element, build: dict) -> None:
    notes_elem = ET.SubElement(root, "Notes")
    notes = build.get("notes")
    if notes:
        notes_elem.text = str(notes)
    else:
        notes_elem.text = ""


def export_placeholder_nodes(root: ET.Element) -> None:
    # PoB often includes these sections. Keeping them present helps compatibility.
    ET.SubElement(root, "Calcs")
    ET.SubElement(root, "Attributes")
    ET.SubElement(root, "PlayerStat")
    ET.SubElement(root, "MinionStat")


def export_build_xml(build: dict) -> ET.ElementTree:
    root = ET.Element("PathOfBuilding")

    export_build_node(root, build)
    export_config_node(root, build)
    export_tree_node(root, build)
    export_items_node(root, build)
    export_skills_node(root, build)
    export_notes_node(root, build)
    export_placeholder_nodes(root)

    indent(root)
    return ET.ElementTree(root)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    build = load_build(args.input_path)
    output_path = ensure_out_path(args.input_path, args.output_path)

    tree = export_build_xml(build)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)

    print("=" * 60)
    print("EXPORT SUMMARY")
    print("=" * 60)
    print(f"Input:  {args.input_path}")
    print(f"Output: {output_path}")
    print(f"Class: {build.get('class_name')}")
    print(f"Ascendancy: {build.get('ascendancy_name')}")
    print(f"Level: {build.get('level')}")
    print(f"Items: {len(build.get('items', []))}")
    print(f"Skill groups: {len(build.get('skill_groups', []))}")
    print(f"Trees: {len(build.get('trees', []))}")
    print("=" * 60)


if __name__ == "__main__":
    main()
