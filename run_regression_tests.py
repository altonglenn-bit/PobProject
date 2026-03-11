import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


DEFAULT_CASES_FILE = "regression_cases.json"
DEFAULT_RESULTS_FILE = "regression_results.json"


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_json(path: str | Path, data: Any) -> None:
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def load_cases(path: str | Path) -> list[dict[str, Any]]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    cases = raw["cases"] if isinstance(raw, dict) and "cases" in raw else raw
    if not isinstance(cases, list):
        raise ValueError("Regression cases file must contain a list or an object with a 'cases' list.")

    normalized: list[dict[str, Any]] = []
    for idx, case in enumerate(cases, start=1):
        if not isinstance(case, dict):
            raise ValueError(f"Case #{idx} is not an object.")
        name = str(case.get("name", f"case_{idx}")).strip()
        prompt = str(case.get("prompt", "")).strip()
        expected_archetype = case.get("expected_archetype")
        expected_stage = case.get("expected_stage")
        if not name:
            raise ValueError(f"Case #{idx} is missing a valid 'name'.")
        if not prompt:
            raise ValueError(f"Case '{name}' is missing a valid 'prompt'.")
        if not expected_archetype:
            raise ValueError(f"Case '{name}' is missing 'expected_archetype'.")
        if not expected_stage:
            raise ValueError(f"Case '{name}' is missing 'expected_stage'.")
        normalized.append(
            {
                "name": name,
                "prompt": prompt,
                "expected_archetype": str(expected_archetype),
                "expected_stage": str(expected_stage),
            }
        )
    return normalized


def run_command(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, encoding="utf-8", errors="replace")


def make_error_result(case: dict[str, Any], step: str, proc: subprocess.CompletedProcess[str] | None = None, message: str | None = None) -> dict[str, Any]:
    return {
        "name": case["name"],
        "prompt": case["prompt"],
        "expected_archetype": case["expected_archetype"],
        "expected_stage": case["expected_stage"],
        "status": "error",
        "error_step": step,
        "stderr": (proc.stderr if proc else message) or "",
        "stdout": (proc.stdout if proc else "") or "",
    }


def evaluate_generation_pipeline(case: dict[str, Any], recommendation: dict[str, Any], tmp: Path) -> dict[str, Any] | None:
    json_out = tmp / f"{case['name']}.json"
    xml_out = tmp / f"{case['name']}.xml"
    encoded_out = tmp / f"{case['name']}_encoded.txt"

    archetype = recommendation.get("recommended_archetype") or recommendation.get("archetype")
    stage = recommendation.get("recommended_stage") or recommendation.get("stage")

    progression_proc = run_command([
        sys.executable, "progression_build.py", "--archetype", str(archetype), "--stage", str(stage), "--out", str(json_out)
    ])
    if progression_proc.returncode != 0:
        return make_error_result(case, "progression_build", progression_proc)
    if not json_out.exists():
        return make_error_result(case, "progression_build", message="progression_build.py succeeded but did not create JSON output.")

    export_proc = run_command([
        sys.executable, "export_build_xml.py", "--in", str(json_out), "--out", str(xml_out)
    ])
    if export_proc.returncode != 0:
        return make_error_result(case, "export_build_xml", export_proc)
    if not xml_out.exists():
        return make_error_result(case, "export_build_xml", message="export_build_xml.py succeeded but did not create XML output.")

    encode_proc = run_command([
        sys.executable, "encode_build.py", "--in", str(xml_out), "--out", str(encoded_out)
    ])
    if encode_proc.returncode != 0:
        return make_error_result(case, "encode_build", encode_proc)
    if not encoded_out.exists():
        return make_error_result(case, "encode_build", message="encode_build.py succeeded but did not create encoded output.")

    roundtrip_proc = run_command([
        sys.executable, "roundtrip_test.py", "--json", str(json_out), "--xml", str(xml_out), "--encoded", str(encoded_out)
    ])
    if roundtrip_proc.returncode != 0:
        return make_error_result(case, "roundtrip_test", roundtrip_proc)

    encoded_text = encoded_out.read_text(encoding="utf-8").strip()
    return {
        "generated_files": {"json": str(json_out), "xml": str(xml_out), "encoded": str(encoded_out)},
        "encoded_length": len(encoded_text),
    }


def evaluate_case(case: dict[str, Any], e2e: bool = False) -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        prefs_path = tmp / f"{case['name']}_prefs.json"
        rec_path = tmp / f"{case['name']}_recommendation.json"

        prompt_proc = run_command([sys.executable, "prompt_to_prefs.py", "--prompt", case["prompt"], "--out", str(prefs_path)])
        if prompt_proc.returncode != 0:
            return make_error_result(case, "prompt_to_prefs", prompt_proc)

        recommend_proc = run_command([sys.executable, "recommend_build.py", "--prefs", str(prefs_path), "--out", str(rec_path)])
        if recommend_proc.returncode != 0:
            return make_error_result(case, "recommend_build", recommend_proc)
        if not rec_path.exists():
            return make_error_result(case, "recommend_build", message="recommend_build.py succeeded but did not create output JSON.")

        prefs = load_json(prefs_path)
        recommendation = load_json(rec_path)
        actual_archetype = recommendation.get("recommended_archetype") or recommendation.get("archetype")
        actual_stage = recommendation.get("recommended_stage") or recommendation.get("stage")
        result = {
            "name": case["name"],
            "prompt": case["prompt"],
            "expected_archetype": case["expected_archetype"],
            "actual_archetype": actual_archetype,
            "expected_stage": case["expected_stage"],
            "actual_stage": actual_stage,
            "score": recommendation.get("score"),
            "reasons": recommendation.get("reasons", []),
            "shortlist": recommendation.get("shortlist") or recommendation.get("top_matches", []),
            "breakdown": recommendation.get("breakdown", {}),
            "prefs": prefs,
            "status": "pass" if actual_archetype == case["expected_archetype"] and actual_stage == case["expected_stage"] else "fail",
        }

        if e2e:
            pipeline = evaluate_generation_pipeline(case, recommendation, tmp)
            if pipeline and pipeline.get("status") == "error":
                pipeline.update({
                    "actual_archetype": actual_archetype,
                    "actual_stage": actual_stage,
                    "score": result["score"],
                    "reasons": result["reasons"],
                    "shortlist": result["shortlist"],
                    "breakdown": result["breakdown"],
                    "prefs": prefs,
                })
                return pipeline
            if pipeline:
                result.update(pipeline)
        return result


def print_case_result(result: dict[str, Any], verbose: bool = False, e2e: bool = False) -> None:
    print("-" * 72)
    print(f"[{result['status'].upper()}] {result['name']}")
    print(f"Prompt:              {result.get('prompt', '')}")
    print(f"Expected archetype:  {result.get('expected_archetype', '')}")
    print(f"Actual archetype:    {result.get('actual_archetype', '')}")
    print(f"Expected stage:      {result.get('expected_stage', '')}")
    print(f"Actual stage:        {result.get('actual_stage', '')}")
    if result.get("score") is not None:
        print(f"Score:               {result['score']}")
    if result["status"] == "error":
        print(f"Error step:          {result.get('error_step', '')}")
        if (result.get("stderr") or "").strip():
            print("stderr:")
            print((result.get("stderr") or "").strip())
        if (result.get("stdout") or "").strip():
            print("stdout:")
            print((result.get("stdout") or "").strip())
        return
    if e2e and result.get("encoded_length") is not None:
        print(f"Encoded length:      {result['encoded_length']}")
    if verbose or result["status"] != "pass":
        reasons = result.get("reasons", [])
        if reasons:
            print("Reasons:")
            for reason in reasons:
                print(f"  - {reason}")
        breakdown = result.get("breakdown", {})
        if breakdown:
            print("Score breakdown:")
            for category, entries in breakdown.items():
                total = sum(entry.get("points", 0) for entry in entries)
                print(f"  {category}: {total:+d}")
                for entry in entries:
                    print(f"    {entry.get('points', 0):+d}  {entry.get('reason', '')}")
        shortlist = result.get("shortlist", [])
        if shortlist:
            print("Top matches:")
            for idx, match in enumerate(shortlist[:5], start=1):
                print(f"  {idx}. {match.get('archetype')} | stage={match.get('stage')} | score={match.get('score')}")
                for reason in match.get("reasons", [])[:5]:
                    print(f"     - {reason}")
        if e2e and result.get("generated_files"):
            print("Generated files:")
            print(f"  - JSON:    {result['generated_files']['json']}")
            print(f"  - XML:     {result['generated_files']['xml']}")
            print(f"  - ENCODED: {result['generated_files']['encoded']}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run recommendation regression tests.")
    parser.add_argument("--cases", default=DEFAULT_CASES_FILE, help=f"Path to regression cases JSON (default: {DEFAULT_CASES_FILE})")
    parser.add_argument("--results", default=DEFAULT_RESULTS_FILE, help=f"Where to save results JSON (default: {DEFAULT_RESULTS_FILE})")
    parser.add_argument("--only", help="Run only the named case.")
    parser.add_argument("--verbose", action="store_true", help="Show reasons and top matches for every case.")
    parser.add_argument("--update", action="store_true", help="Update the cases file with actual outputs for failing cases.")
    parser.add_argument("--e2e", action="store_true", help="Also run progression_build, export_build_xml, encode_build, and roundtrip_test for each case.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cases = load_cases(args.cases)
    if args.only:
        cases = [case for case in cases if case["name"] == args.only]
        if not cases:
            raise SystemExit(f"No regression case named '{args.only}' found in {args.cases}.")

    print("=" * 72)
    print("RECOMMENDATION REGRESSION TESTS")
    print("=" * 72)
    print(f"Cases: {len(cases)}")
    if args.e2e:
        print("Mode: recommendation + end-to-end build pipeline")
    print()

    results: list[dict[str, Any]] = []
    passed = failed = errored = 0
    for case in cases:
        result = evaluate_case(case, e2e=args.e2e)
        results.append(result)
        print_case_result(result, verbose=args.verbose, e2e=args.e2e)
        if result["status"] == "pass":
            passed += 1
        elif result["status"] == "fail":
            failed += 1
        else:
            errored += 1

    save_json(args.results, {"results": results, "e2e": args.e2e})

    if args.update:
        original_cases = load_cases(args.cases)
        by_name = {r["name"]: r for r in results}
        updated_cases: list[dict[str, Any]] = []
        for case in original_cases:
            result = by_name.get(case["name"])
            if result and result["status"] in {"pass", "fail"}:
                updated_cases.append({
                    "name": case["name"],
                    "prompt": case["prompt"],
                    "expected_archetype": result.get("actual_archetype"),
                    "expected_stage": result.get("actual_stage"),
                })
            else:
                updated_cases.append(case)
        save_json(args.cases, updated_cases)

    print()
    print("=" * 72)
    print("SUMMARY")
    print("=" * 72)
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Errors: {errored}")
    print(f"Saved results: {args.results}")
    if args.update:
        print(f"Updated cases: {args.cases}")


if __name__ == "__main__":
    main()
