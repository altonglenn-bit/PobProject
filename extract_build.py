from __future__ import annotations

import base64
import json
import zlib
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from typing import Any
from urllib.request import urlopen


@dataclass
class GemData:
    name: str | None = None
    enabled: bool | None = None
    level: int | None = None
    quality: int | None = None
    skill_id: str | None = None


@dataclass
class SkillGroupData:
    label: str | None = None
    slot: str | None = None
    enabled: bool | None = None
    gems: list[GemData] = field(default_factory=list)


@dataclass
class ItemData:
    id: str | None = None
    slot: str | None = None
    name: str | None = None
    base: str | None = None
    rarity: str | None = None
    item_level: int | None = None
    level_req: int | None = None
    text: str | None = None


@dataclass
class TreeSpecData:
    title: str | None = None
    class_id: str | None = None
    ascend_class_id: str | None = None
    tree_version: str | None = None
    url: str | None = None
    nodes: list[int] = field(default_factory=list)


@dataclass
class BuildSchema:
    source: str
    class_name: str | None = None
    ascendancy_name: str | None = None
    level: int | None = None
    bandit: str | None = None
    notes: str | None = None
    stats: dict[str, Any] = field(default_factory=dict)
    config: dict[str, Any] = field(default_factory=dict)
    items: list[ItemData] = field(default_factory=list)
    skill_groups: list[SkillGroupData] = field(default_factory=list)
    skill_names: list[str] = field(default_factory=list)
    trees: list[TreeSpecData] = field(default_factory=list)


def parse_int(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except Exception:
        return None


def parse_bool(value: str | None) -> bool | None:
    if value is None:
        return None
    value = value.strip().lower()
    if value in ("true", "1", "yes"):
        return True
    if value in ("false", "0", "no", "nil"):
        return False
    return None


def read_source_input() -> str:
    source = input("Paste PoB import code, pastebin URL, or path to a .txt file: ").strip()

    # If the user gives a local text file path, read from it.
    if source.lower().endswith(".txt"):
        try:
            with open(source, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception as e:
            raise ValueError(f"Failed to read text file: {source}") from e

    return source


def decode_pob_import_code(import_code: str) -> str:
    # Remove whitespace/newlines so pasted multi-line content still works
    import_code = "".join(import_code.strip().split())

    if not import_code:
        raise ValueError("PoB import code is empty.")

    # If the remainder is 1, the base64 length is impossible and almost certainly truncated
    if len(import_code) % 4 == 1:
        raise ValueError(
            "PoB import code length is invalid. The code is likely truncated or missing a character."
        )

    padding = "=" * (-len(import_code) % 4)
    encoded = import_code + padding

    try:
        compressed = base64.urlsafe_b64decode(encoded.encode("ascii"))
    except Exception as e:
        raise ValueError(
            "Failed to base64-decode PoB import code. The code is likely incomplete, corrupted, or copied incorrectly."
        ) from e

    try:
        xml_bytes = zlib.decompress(compressed)
    except Exception as e:
        raise ValueError(
            "Failed to decompress PoB import code. The code may not be a valid PoB export string."
        ) from e

    try:
        return xml_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return xml_bytes.decode("utf-8", errors="replace")


def load_build_xml_text(source: str) -> str:
    source = source.strip()

    if source.startswith("http://") or source.startswith("https://"):
        try:
            with urlopen(source) as resp:
                data = resp.read()
            return data.decode("utf-8", errors="replace")
        except Exception as e:
            raise ValueError("Failed to load build XML from URL.") from e

    return decode_pob_import_code(source)


def xml_root_from_source(source: str) -> ET.Element:
    xml_text = load_build_xml_text(source)
    try:
        return ET.fromstring(xml_text)
    except Exception as e:
        raise ValueError("Decoded PoB data is not valid XML.") from e


def parse_item_text(text: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "rarity": None,
        "name": None,
        "base": None,
        "item_level": None,
        "level_req": None,
    }

    if not text:
        return result

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return result

    if lines[0].startswith("Rarity:"):
        result["rarity"] = lines[0].split(":", 1)[1].strip().title()
        if len(lines) >= 2:
            result["name"] = lines[1]
        if len(lines) >= 3:
            result["base"] = lines[2]

    for line in lines:
        if line.startswith("Item Level:"):
            result["item_level"] = parse_int(line.split(":", 1)[1].strip())
        elif line.startswith("LevelReq:"):
            result["level_req"] = parse_int(line.split(":", 1)[1].strip())
        elif line.startswith("Level Requirement:"):
            result["level_req"] = parse_int(line.split(":", 1)[1].strip())

    return result


def parse_items(root: ET.Element) -> list[ItemData]:
    items_section = root.find("Items")
    if items_section is None:
        return []

    active_item_set_id = items_section.attrib.get("activeItemSet")
    slot_by_item_id: dict[str, str] = {}

    for item_set in items_section.findall("ItemSet"):
        if active_item_set_id and item_set.attrib.get("id") != active_item_set_id:
            continue
        for slot in item_set.findall("Slot"):
            item_id = slot.attrib.get("itemId")
            slot_name = slot.attrib.get("name")
            if item_id and slot_name:
                slot_by_item_id[item_id] = slot_name

    out: list[ItemData] = []

    for item in items_section.findall("Item"):
        item_id = item.attrib.get("id")
        text = item.text or ""
        parsed = parse_item_text(text)

        out.append(
            ItemData(
                id=item_id,
                slot=slot_by_item_id.get(item_id),
                name=parsed["name"],
                base=parsed["base"],
                rarity=parsed["rarity"],
                item_level=parsed["item_level"],
                level_req=parsed["level_req"],
                text=text.strip(),
            )
        )

    return out


def parse_skills(root: ET.Element) -> tuple[list[SkillGroupData], list[str]]:
    skills_section = root.find("Skills")
    if skills_section is None:
        return [], []

    active_skill_set = skills_section.attrib.get("activeSkillSet")
    groups: list[SkillGroupData] = []
    skill_names: list[str] = []

    skill_sets = skills_section.findall("SkillSet")

    selected_sets = []
    if active_skill_set is not None:
        for skill_set in skill_sets:
            if skill_set.attrib.get("id") == active_skill_set:
                selected_sets.append(skill_set)

    if not selected_sets:
        selected_sets = skill_sets

    for skill_set in selected_sets:
        for skill in skill_set.findall("Skill"):
            gems: list[GemData] = []

            for gem in skill.findall("Gem"):
                name = gem.attrib.get("nameSpec") or gem.attrib.get("name")
                if name:
                    skill_names.append(name)

                gems.append(
                    GemData(
                        name=name,
                        enabled=parse_bool(gem.attrib.get("enabled")),
                        level=parse_int(gem.attrib.get("level")),
                        quality=parse_int(gem.attrib.get("quality")),
                        skill_id=gem.attrib.get("skillId"),
                    )
                )

            groups.append(
                SkillGroupData(
                    label=skill.attrib.get("label"),
                    slot=skill.attrib.get("slot"),
                    enabled=parse_bool(skill.attrib.get("enabled")),
                    gems=gems,
                )
            )

    seen = set()
    ordered_skill_names = []
    for name in skill_names:
        if name and name not in seen:
            seen.add(name)
            ordered_skill_names.append(name)

    return groups, ordered_skill_names


def parse_trees(root: ET.Element) -> list[TreeSpecData]:
    tree_section = root.find("Tree")
    if tree_section is None:
        return []

    trees: list[TreeSpecData] = []

    for spec in tree_section.findall("Spec"):
        nodes_raw = spec.attrib.get("nodes", "")
        nodes = []
        if nodes_raw.strip():
            for n in nodes_raw.split(","):
                n = n.strip()
                if n.isdigit():
                    nodes.append(int(n))

        trees.append(
            TreeSpecData(
                title=spec.attrib.get("title"),
                class_id=spec.attrib.get("classId"),
                ascend_class_id=spec.attrib.get("ascendClassId"),
                tree_version=spec.attrib.get("treeVersion"),
                url=spec.attrib.get("url"),
                nodes=nodes,
            )
        )

    return trees


def parse_notes(root: ET.Element) -> str:
    notes_node = root.find("Notes")
    if notes_node is None or notes_node.text is None:
        return ""
    return notes_node.text.strip()


def parse_config(root: ET.Element) -> dict[str, Any]:
    config_node = root.find("Config")
    if config_node is None:
        return {}

    result: dict[str, Any] = {}
    active_config_set = config_node.attrib.get("activeConfigSet")
    selected_sets = []
    config_sets = config_node.findall("ConfigSet")

    if active_config_set is not None:
        for cfg in config_sets:
            if cfg.attrib.get("id") == active_config_set:
                selected_sets.append(cfg)

    if not selected_sets:
        selected_sets = config_sets

    for cfg in selected_sets:
        for input_node in cfg.findall("Input"):
            name = input_node.attrib.get("name")
            value = (
                input_node.attrib.get("value")
                or input_node.attrib.get("boolean")
                or input_node.attrib.get("number")
                or input_node.attrib.get("string")
            )
            if not name:
                continue

            parsed_bool = parse_bool(value)
            if parsed_bool is not None:
                result[name] = parsed_bool
                continue

            parsed_int = parse_int(value)
            if parsed_int is not None:
                result[name] = parsed_int
                continue

            result[name] = value

        for placeholder_node in cfg.findall("Placeholder"):
            name = placeholder_node.attrib.get("name")
            value = (
                placeholder_node.attrib.get("value")
                or placeholder_node.attrib.get("boolean")
                or placeholder_node.attrib.get("number")
                or placeholder_node.attrib.get("string")
            )
            if name:
                result[f"placeholder:{name}"] = value

    return result


def parse_build_attrs(root: ET.Element) -> dict[str, Any]:
    build_node = root.find("Build")
    if build_node is None:
        return {
            "class_name": None,
            "ascendancy_name": None,
            "level": None,
            "bandit": None,
        }

    return {
        "class_name": build_node.attrib.get("className"),
        "ascendancy_name": build_node.attrib.get("ascendClassName"),
        "level": parse_int(build_node.attrib.get("level")),
        "bandit": build_node.attrib.get("bandit"),
    }


def main() -> None:
    source = read_source_input()
    root = xml_root_from_source(source)

    build_attrs = parse_build_attrs(root)
    items = parse_items(root)
    skill_groups, skill_names = parse_skills(root)
    trees = parse_trees(root)
    notes = parse_notes(root)
    config = parse_config(root)

    schema = BuildSchema(
        source=source,
        class_name=build_attrs["class_name"],
        ascendancy_name=build_attrs["ascendancy_name"],
        level=build_attrs["level"],
        bandit=build_attrs["bandit"],
        notes=notes,
        stats={},
        config=config,
        items=items,
        skill_groups=skill_groups,
        skill_names=skill_names,
        trees=trees,
    )

    with open("build.json", "w", encoding="utf-8") as f:
        json.dump(asdict(schema), f, indent=2, ensure_ascii=False)

    print("Wrote build.json")
    print(f"Class: {schema.class_name}")
    print(f"Ascendancy: {schema.ascendancy_name}")
    print(f"Level: {schema.level}")
    print(f"Items: {len(schema.items)}")
    print(f"Skill groups: {len(schema.skill_groups)}")
    print(f"Skill names: {len(schema.skill_names)}")
    print(f"Trees: {len(schema.trees)}")


if __name__ == "__main__":
    main()