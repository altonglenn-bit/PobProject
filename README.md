# POB AI Project

A Path of Building automation and recommendation project that can:

- parse a natural-language build request into preferences
- recommend the best archetype and stage
- generate a progression build JSON
- export the build to XML
- encode the XML into a Path of Building import string
- run regression and end-to-end validation

## Features

- Natural language prompt parsing
- Archetype recommendation with score breakdowns
- Stage-aware build generation
- Regression testing for recommendation quality
- End-to-end testing for full JSON → XML → encoded output pipeline
- Archetype validation utility

## Project layout

- `generate_build.py` — main entry point for prompt/archetype-based generation
- `recommend_build.py` — recommendation engine
- `prompt_to_prefs.py` — converts prompts into normalized preferences
- `progression_build.py` — applies archetype/stage progression logic
- `export_build_xml.py` — exports JSON builds to XML
- `encode_build.py` — encodes XML to a PoB import string
- `roundtrip_test.py` — validates generated artifacts
- `run_regression_tests.py` — regression and optional end-to-end test runner
- `validate_archetypes.py` — validates archetype definitions

## Requirements

- Python 3.11 recommended
- Windows PowerShell or Command Prompt
- Path of Building-compatible input data files in the repo

## Setup

### 1. Create and activate a virtual environment

#### Windows Command Prompt
```bat
python -m venv .venv
.venv\Scripts\activate
```

#### PowerShell
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

If you already have a `requirements.txt` file:

```bat
pip install -r requirements.txt
```

If not, install whatever the project currently depends on, then later freeze with:

```bat
pip freeze > requirements.txt
```

## Quick start

### List available archetypes

```bat
python progression_build.py --list
```

### Generate from a prompt

```bat
python generate_build.py --prompt "I want a beginner friendly summoner for maps and bosses"
```

### Generate from an explicit archetype and stage

```bat
python generate_build.py --archetype kinetic_fusillade_totem --stage endgame
```

### See recommendation debug output

```bat
python recommend_build.py --prefs safe_red_maps_voidstones_prefs.json --debug
```

## Validation and testing

### Validate archetype definitions

```bat
python validate_archetypes.py
```

### Run recommendation regression tests

```bat
python run_regression_tests.py
```

### Run verbose regression tests

```bat
python run_regression_tests.py --verbose
```

### Run a single regression case

```bat
python run_regression_tests.py --only bossing_ubers
```

### Run end-to-end pipeline tests

```bat
python run_regression_tests.py --e2e
```

### Run verbose end-to-end tests

```bat
python run_regression_tests.py --e2e --verbose
```

## Typical output artifacts

Depending on the command, the project may produce:

- `*_prefs.json`
- `*_recommendation.json`
- `*.json`
- `*.xml`
- `*_encoded.txt`
- `regression_results.json`

## Current status

The project currently has:

- archetype validation passing
- recommendation regression tests passing
- end-to-end build pipeline tests passing

## Recommended workflow

When making scoring or parsing changes:

1. Run:
   ```bat
   python validate_archetypes.py
   ```
2. Run:
   ```bat
   python run_regression_tests.py
   ```
3. Run:
   ```bat
   python run_regression_tests.py --e2e
   ```
4. Review any score shifts in verbose mode:
   ```bat
   python run_regression_tests.py --verbose
   ```

## GitHub

After changes:

```bat
git add .
git commit -m "Describe your change"
git push
```

## Notes

- Avoid typing multiple Python commands on one line in Command Prompt.
- Run one command at a time.
- If imports suddenly break, check whether a helper function was renamed or removed.
- If recommendation behavior shifts, run the verbose regression suite to inspect score breakdowns.

## License

Add a license here if you want the repo to be open for reuse.
