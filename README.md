# POB AI Project

## Current pipeline

1. `extract_build.py`
   - Takes a PoB import string or URL
   - Produces `build.json`

2. `summarize_build.py`
   - Displays a readable summary of a build JSON

3. `mutate_build.py`
   - Edits build JSON safely into a new output file

4. `export_build_xml.py`
   - Converts JSON back into PoB-style XML

5. `encode_build.py`
   - Compresses + base64-encodes XML into a PoB import string

6. `template_build.py`
   - Creates template-derived variants from a base build

7. `roundtrip_test.py`
   - Sanity-checks JSON/XML/encoded outputs

## Typical usage

### Extract a build
```bat
python extract_build.py
```

### Generate from prompt or archetype
```bat
python generate_build.py --prompt "I want a safe totem build for bossing"
python generate_build.py --archetype kinetic_fusillade_totem --stage endgame
```


## Validation

### Archetype preflight validation
```bat
python validate_archetypes.py
```

### Recommendation-only regression suite
```bat
python run_regression_tests.py
python run_regression_tests.py --verbose
python run_regression_tests.py --only bossing_ubers
```

### End-to-end regression suite
This runs the full chain for each case:
- `prompt_to_prefs.py`
- `recommend_build.py`
- `progression_build.py`
- `export_build_xml.py`
- `encode_build.py`
- `roundtrip_test.py`

```bat
python run_regression_tests.py --e2e
python run_regression_tests.py --e2e --verbose
```



## Quick local quality check

Install the lightweight test dependency:
```bat
pip install -r requirements.txt
```

Run unit + validation + regression + e2e in one shot:
```bat
check_all.bat
```

## CI

A GitHub Actions workflow is included at:
```text
.github/workflows/tests.yml
```

It runs:
- `pytest -q`
- `python validate_archetypes.py`
- `python run_regression_tests.py`
- `python run_regression_tests.py --e2e`
