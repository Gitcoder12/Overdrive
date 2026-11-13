# Independent Model Audit Router — Overdrive

**Revision date:** 2026-11-13  
**Purpose:** Protect the original project, its real data, and the maintainer's credibility while independent models audit quality and help improve the repository.

## Non-negotiable data-integrity rules

1. **Never replace real project data with fabricated, synthetic, generated, or placeholder records.** Do not silently swap an existing dataset, source file, fixture, API response, or user-provided content.
2. Before changing data, trace its origin and inspect Git history. Record the exact path, prior commit, source, licence, collection date, and known limitations.
3. If a real source cannot be verified, preserve the existing source unchanged and mark the affected fields as `unknown` or `unverified`. Do not invent an alternative.
4. Synthetic data is permitted only in clearly labelled tests, fixtures, examples, or an explicitly requested demo. Keep it separate from production data and label it in the UI and documentation.
5. Do not fabricate people, company relationships, government records, licences, inspections, citations, metrics, benchmark results, customers, deployments, endorsements, or contributors.
6. Never claim tests passed unless they were run successfully against the exact commit being reviewed. Distinguish unit tests, mocked tests, integration tests, manual checks, CI and production observations.

## README preservation policy

- Treat the README version immediately before AI-generated edits as protected maintainer-authored content.
- Recover the baseline from Git history before changing README.md. Preserve its wording, sections, links, images, examples, and project-specific claims.
- Do not rewrite or replace the original README. Append a clearly labelled **AI-maintained notes / engineering addendum** at the very bottom only.
- The addendum must be secondary, dated, concise, factual, and linked to actual code, tests, issues, commits or PRs.
- Never remove a claim just because it is inconvenient. Flag unsupported claims for maintainer review and propose evidence-based corrections separately.

## Independent review agents

Run these as separate, sceptical reviews. One model may cover more than one role, but do not let one agent approve its own work.

1. **Data provenance checker:** traces every runtime dataset and official-looking field to a verifiable source; detects fabricated rows, identifiers, dates, names, scores and silent data substitutions.
2. **Code and architecture reviewer:** checks that documented commands, module paths, APIs, entry points, workflows and architecture match the actual source tree.
3. **Security and privacy reviewer:** checks secrets, credentials, unsafe input handling, authentication/authorisation, data exposure, dependency risk and privacy boundaries. Do not reproduce secrets in reports.
4. **Test and reliability reviewer:** runs the documented test/build/lint commands, examines edge cases and verifies results on the exact reviewed commit.
5. **README and attribution reviewer:** compares README.md with its pre-AI Git-history baseline, checks licensing, attribution, links, installation steps and claims.
6. **Career and research reviewer:** checks that recruiter/researcher/professor-facing claims are demonstrable, technically accurate, responsibly scoped and supported by public evidence.

## Required review output

For every finding, provide:

- Severity: **P0 blocker / P1 high / P2 medium / P3 low**
- Exact file path and line or symbol
- Reproduction steps and expected vs actual behaviour
- Evidence: commit SHA, test output, source URL or public documentation
- Whether the finding is confirmed, suspected or unverifiable
- Minimal proposed fix and regression test
- Whether data or README history could be affected

Do not report vague opinions as defects. Do not silently change files while auditing.

## Required audit sequence

1. Record repository URL, default branch, current HEAD SHA, working tree state, and whether this is an upstream fork.
2. Inspect the full diff/history for all AI-related commits and open PRs. Identify changes that are merged, open, closed-unmerged, reverted, or not independently verifiable.
3. Inventory runtime data files, data-loading paths, generated files, test fixtures, sample data, external APIs and data provenance.
4. Compare README.md against the protected pre-AI version. Propose restoration before editing it.
5. Run the real install/build/lint/test commands and inspect CI configuration for suppressed failures, skipped tests or false-green jobs.
6. Review security, privacy, accessibility, error handling, performance and reproducibility.
7. Audit links and career-facing claims. A company match is only a potential skill fit unless a real relationship is proven.
8. Publish the findings in the review handoff. Do not merge, delete, force-push, overwrite datasets or alter README originals without explicit maintainer approval.

## Merge gate — all must pass

- [ ] No fabricated data is presented as real or official.
- [ ] Existing real/user-provided data is preserved; any source change is explained and approved.
- [ ] Original README text is retained; AI notes are at the bottom only.
- [ ] Public claims are supported by accessible evidence.
- [ ] Tests and CI pass on the exact PR head, or failures are clearly recorded.
- [ ] No secrets, private personal details, classified or confidential material are added.
- [ ] Licensing and upstream attribution are preserved.
- [ ] A second reviewer independently checks the diff.
- [ ] Maintainer approves the final change.

## Repository-specific review notes

Repository: **Overdrive**  
Start with the repository's current README, source tree, runtime data, tests, workflow files, open PRs, and the last known maintainer-authored commit. Do not infer a feature from the repository name or roadmap.

**Maintainer authority:** The repository owner decides whether a change is accepted. Model confidence, contribution counts, green checks, and generated documentation do not replace review.
