# AI Engineering Worklog

## 2026-11-13 — API output boundary hardening

### Completed
- Validate provider output as exactly one JSON object; reject leading prose, trailing prose, arrays, non-text values, malformed JSON and extra schema fields.
- Enforce 3–7 bottlenecks with contiguous ascending unique ranks.
- Enforce supported severity values, positive strict integer ranks, confidence in [0, 1], and non-blank bounded names, causes, fixes, ROI text and summary.
- Strip and validate process descriptions; reject whitespace-only input.
- Return generic 503 responses for provider configuration errors and generic 502 responses for provider failures/schema errors without leaking exception details.
- Align documented provider names and missing-key warnings with adapters that actually exist; remove unsupported DeepSeek/OpenRouter key settings from the current settings contract.
- Add regression tests for invalid JSON, leading/trailing prose, non-text output, duplicate/out-of-order ranks, count boundaries, blank fields, extra fields and provider failures.

### Exact-head validation
- Exact validated PR head: `9b9d477cedb9c05c705fbb3da92537012a0a104f`.
- GitHub Actions run: [43413035446](https://github.com/Gitcoder12/Overdrive/actions/runs/43413035446).
- Python 3.11, 3.12 and 3.13: Ruff and pytest passed.
- Pytest: 35 passed on each version.

### Known follow-up
- The Google provider currently uses the deprecated `google-generativeai` SDK. Migrate it to `google-genai` in a separate provider-maintenance change.
- The MVP still relies on LLM-generated process analysis; outputs are structured and validated but are not independently measured process facts.
