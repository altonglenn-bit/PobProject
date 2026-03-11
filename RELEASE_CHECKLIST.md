# Release Checklist

## Before pushing

- [ ] Activate the virtual environment
- [ ] Run `python validate_archetypes.py`
- [ ] Run `python run_regression_tests.py`
- [ ] Run `python run_regression_tests.py --e2e`
- [ ] Review any score changes with `python run_regression_tests.py --verbose`
- [ ] Confirm no accidental local-only files are being committed

## Git workflow

- [ ] `git status`
- [ ] `git add .`
- [ ] `git commit -m "Describe your change"`
- [ ] `git push`

## After pushing

- [ ] Open the GitHub Actions tab
- [ ] Confirm the CI workflow passes
- [ ] Review generated logs if CI fails

## Good next upgrades

- [ ] Add `requirements.txt`
- [ ] Add unit tests for prompt parsing and scoring helpers
- [ ] Add a changelog
- [ ] Add sample prompts and expected outputs to the README
