from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from progression_build import load_archetypes

REQUIRED_TOP_LEVEL = ["base", "stages"]
REQUIRED_STAGE_KEYS = ["level"]
VALID_STAGES = {"leveling", "early_maps", "endgame"}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    archetypes = load_archetypes()
    root = Path(__file__).resolve().parent

    print("=" * 72)
    print("ARCHETYPE VALIDATION")
    print("=" * 72)
    print(f"Archetypes: {len(archetypes)}")

    errors: list[str] = []
    warnings: list[str] = []

    for name, config in sorted(archetypes.items()):
        base = str(config.get("base", "")).strip()
        stages = config.get("stages", {})
        print("-" * 72)
        print(f"[{name}]")

        for key in REQUIRED_TOP_LEVEL:
            if key not in config:
                errors.append(f"{name}: missing top-level key '{key}'")

        if not base:
            errors.append(f"{name}: missing base file")
        else:
            base_path = root / base
            if not base_path.exists():
                errors.append(f"{name}: base file not found: {base}")
            else:
                try:
                    data = load_json(base_path)
                    print(f"Base file: {base} [ok]")
                    if not isinstance(data, dict):
                        errors.append(f"{name}: base file is not a JSON object: {base}")
                except Exception as exc:
                    errors.append(f"{name}: failed to parse base file {base}: {exc}")

        if not isinstance(stages, dict) or not stages:
            errors.append(f"{name}: stages must be a non-empty object")
            continue

        unknown_stages = set(stages) - VALID_STAGES
        if unknown_stages:
            warnings.append(f"{name}: unknown stage keys: {sorted(unknown_stages)}")

        for stage_name, stage_cfg in sorted(stages.items()):
            if not isinstance(stage_cfg, dict):
                errors.append(f"{name}: stage '{stage_name}' must be an object")
                continue
            missing = [k for k in REQUIRED_STAGE_KEYS if k not in stage_cfg]
            if missing:
                errors.append(f"{name}: stage '{stage_name}' missing keys: {', '.join(missing)}")
            else:
                print(f"  - {stage_name}: level={stage_cfg.get('level')} [ok]")

        profile = config.get("profile", {})
        if not isinstance(profile, dict):
            errors.append(f"{name}: profile must be an object")
        else:
            if profile.get("bossing") == "strong" and "bossing" not in set(config.get("content_tags", [])):
                warnings.append(f"{name}: strong bossing profile but missing 'bossing' content tag")
            if profile.get("mapping") == "strong" and "maps" not in set(config.get("content_tags", [])):
                warnings.append(f"{name}: strong mapping profile but missing 'maps' content tag")

    print("=" * 72)
    print("SUMMARY")
    print("=" * 72)
    print(f"Warnings: {len(warnings)}")
    for item in warnings:
        print(f"  - {item}")
    print(f"Errors:   {len(errors)}")
    for item in errors:
        print(f"  - {item}")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
