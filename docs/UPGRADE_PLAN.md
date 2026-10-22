# Overdrive upgrade plan
Audit date: 2026-10-22. Written on branch `docs/upgrade-plan`.

## Current state (measured)
- 18 files, about 600 lines of Python (FastAPI app in `app/`), 5 test files, Apache-2.0 license
- `pytest`: **14 passed**, with a deprecation warning: the `google.generativeai` package is deprecated
- `ruff check .`: 3 findings: `app/main.py:95` and `:111` (B008 on FastAPI `Depends`), `app/main.py:158` (W292, no newline at end of file)
- No CI

## Goals, in order
1. **Replace the deprecated SDK.** Migrate from `google.generativeai` to the current `google-genai` package.
   Done when the deprecation warning is gone and all tests pass.
2. **Lint properly.** B008 on `Depends` is a normal FastAPI idiom: configure `extend-immutable-calls` in ruff instead of rewriting code. Fix W292.
   Done when `ruff check .` is clean.
3. **CI.** GitHub Actions on push and PR (Python 3.11 and 3.12): ruff and pytest. The LLM is mocked in tests.
4. **Robust LLM calls.** Timeouts, bounded retries with backoff, clear error responses, streaming where applicable.
5. **Narrow the scope.** Pick ONE concrete use case (for example: find inefficiencies in a Python repository) and make it excellent.
   Do not analyse individual people: it adds privacy risk without a measurable benefit.
   Done when a documented demo shows measurable before/after results.
6. **Evaluation.** A small fixed set of cases with expected findings; report precision and recall honestly.

## Quality gate
`ruff check . && pytest`

## Rules for any contributor or AI model working from this plan
1. Work on a **new branch** (for example `feat/<topic>`). Never push to `main`. Open a pull request.
2. Run the quality gate before every push. Paste the real test output into the PR description.
3. Do not claim anything you did not measure. No invented benchmarks, no placeholder numbers.
4. Small, focused commits. Take git identity from `git log -1`; never invent an email address.
5. Never commit secrets, tokens, raw data or generated artifacts.
6. When a task is finished, tick its box here and note the date and PR number.

## Status
- [ ] Not started
