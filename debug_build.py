from __future__ import annotations

import json
from pprint import pprint

import pobapi


def safe_attr(obj, name, default=None):
    try:
        return getattr(obj, name)
    except Exception as e:
        return f"<error: {e}>" if default is None else default


def dump_attrs(title, obj, max_items=80):
    print("=" * 80)
    print(title)
    print("=" * 80)

    names = [n for n in dir(obj) if not n.startswith("_")]
    for name in names[:max_items]:
        try:
            value = getattr(obj, name)
            if callable(value):
                print(f"{name}: <callable>")
            else:
                text = repr(value)
                if len(text) > 200:
                    text = text[:200] + "..."
                print(f"{name}: {text}")
        except Exception as e:
            print(f"{name}: <error: {e}>")
    print()


def main():
    source = input("Paste PoB import code or pastebin URL: ").strip()

    if source.startswith("http://") or source.startswith("https://"):
        build = pobapi.from_url(source)
    else:
        build = pobapi.from_import_code(source)

    print("\nTOP-LEVEL FIELDS")
    print(f"class_name: {safe_attr(build, 'class_name')}")
    print(f"ascendancy_name: {safe_attr(build, 'ascendancy_name')}")
    print(f"level: {safe_attr(build, 'level')}")
    print(f"bandit: {safe_attr(build, 'bandit')}")
    print(f"notes: {repr(safe_attr(build, 'notes'))[:300]}")
    print(f"skill_names: {safe_attr(build, 'skill_names')}")
    print(f"items count: {len(safe_attr(build, 'items', []) or [])}")
    print(f"skill_groups count: {len(safe_attr(build, 'skill_groups', []) or [])}")
    print(f"trees count: {len(safe_attr(build, 'trees', []) or [])}")
    print()

    dump_attrs("BUILD ATTRIBUTES", build)

    skill_groups = safe_attr(build, "skill_groups", []) or []
    for i, group in enumerate(skill_groups[:5], start=1):
        dump_attrs(f"SKILL GROUP {i}", group)
        gems = safe_attr(group, "gems", []) or []
        for j, gem in enumerate(gems[:10], start=1):
            dump_attrs(f"SKILL GROUP {i} GEM {j}", gem, max_items=40)

    trees = safe_attr(build, "trees", []) or []
    for i, tree in enumerate(trees[:3], start=1):
        dump_attrs(f"TREE {i}", tree, max_items=60)

    items = safe_attr(build, "items", []) or []
    for i, item in enumerate(items[:5], start=1):
        dump_attrs(f"ITEM {i}", item, max_items=60)

    with open("debug_snapshot.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "class_name": str(safe_attr(build, "class_name")),
                "ascendancy_name": str(safe_attr(build, "ascendancy_name")),
                "level": str(safe_attr(build, "level")),
                "skill_names": str(safe_attr(build, "skill_names")),
                "items_count": len(items),
                "skill_groups_count": len(skill_groups),
                "trees_count": len(trees),
            },
            f,
            indent=2,
        )

    print("Wrote debug_snapshot.json")


if __name__ == "__main__":
    main()