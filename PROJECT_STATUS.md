# POB AI Project Status

## Current status

The project is in a strong v1-ready state for recommendation and build generation.

### What is working now
- Prompt -> preferences parsing
- Recommendation scoring with explainable reasons and score breakdowns
- Archetype/stage recommendation regression suite
- End-to-end generation pipeline:
  - progression build generation
  - XML export
  - PoB encoding
  - roundtrip verification
- Verbose debugging for recommendation decisions
- Single-case and full-suite test execution

### Current evidence
- Recommendation regression suite: 15/15 passing
- End-to-end regression suite: 15/15 passing
- Patched import regressions fixed:
  - `parse_prompt_to_prefs` compatibility issue
  - `load_archetypes` compatibility issue

## Estimated completion
- Core feature completeness: ~90%
- V1 readiness: ~85%
- Production robustness: ~70%

## Remaining work

### High priority
- Keep the regression suite protected and updated deliberately
- Centralize shared helper APIs to reduce import breakage risk
- Add more parser-focused unit tests for ambiguous prompts
- Add archetype preflight validation to the normal workflow

### Medium priority
- Normalize wording in explanations and reasons
- Add a confidence field separate from raw score
- Add CI automation for regression + e2e runs
- Reduce duplicate generated artifacts checked into the project directory

### Nice to have
- Structured HTML/markdown test report output
- Archetype metadata registry file separate from scoring logic
- Small benchmark suite for recommendation latency

## Recommended workflow

### Before changing scoring logic
1. Run `python validate_archetypes.py`
2. Run `python run_regression_tests.py`
3. Run `python run_regression_tests.py --e2e`

### Before shipping a release
1. Run the full verbose regression suite
2. Run the full verbose e2e suite
3. Review any score changes in the top matches
4. Update regression snapshots only when behavior changes are intentional
