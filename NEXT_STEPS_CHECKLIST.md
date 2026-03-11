# Next Steps Checklist

## Current state
- Recommendation regression suite passing: 15/15
- End-to-end regression suite passing: 15/15
- Archetype validation passing
- Debug breakdowns working
- CI scaffold added
- Local `pytest` scaffold added
- One-command local check script added

## Immediate next actions
- [ ] Run `pip install -r requirements.txt`
- [ ] Run `pytest -q`
- [ ] Run `python validate_archetypes.py`
- [ ] Run `python run_regression_tests.py`
- [ ] Run `python run_regression_tests.py --e2e`
- [ ] Commit the new workflow and test scaffolding
- [ ] Push to GitHub and confirm Actions passes

## Recommended implementation roadmap

### 1. Lock in stability
- [ ] Keep import helpers centralized in one place
- [ ] Avoid duplicating loader helpers across scripts
- [ ] Add a small compatibility layer for public helper functions
- [ ] Add smoke tests for CLI entry points

### 2. Expand parser coverage
- [ ] Add more prompt parsing unit tests for ambiguous prompts
- [ ] Add tests for explicit stage phrases like `leveling`, `early maps`, `red maps`
- [ ] Add tests for content tags like `heist`, `sanctum`, `delve`, `blight`
- [ ] Add tests for combined intents like `safe low-apm mapper`

### 3. Improve scoring robustness
- [ ] Separate raw score from recommendation confidence
- [ ] Normalize reason wording across archetypes
- [ ] Reduce repeated explanations in verbose output
- [ ] Add tie-break regression cases explicitly documenting expected winner logic

### 4. Improve project hygiene
- [ ] Move generated outputs into a dedicated `outputs/` folder
- [ ] Reduce checked-in generated JSON/XML/TXT artifacts
- [ ] Add `.gitignore` entries for temp or generated test artifacts
- [ ] Keep regression fixtures intentional and documented

### 5. V1 release readiness
- [ ] Add a release checklist to README
- [ ] Add sample commands for common user flows
- [ ] Add expected exit codes for validation/test scripts
- [ ] Decide what counts as supported prompts for v1

## Suggested definition of done for v1
- [ ] All regression tests pass locally
- [ ] All e2e tests pass locally
- [ ] GitHub Actions passes on push and pull request
- [ ] README contains setup, test, and usage instructions
- [ ] Core recommendation behavior is locked with regression coverage
- [ ] No known import-path regressions remain

## Suggested command bundle
```bat
pip install -r requirements.txt
pytest -q
python validate_archetypes.py
python run_regression_tests.py
python run_regression_tests.py --e2e
check_all.bat
```
