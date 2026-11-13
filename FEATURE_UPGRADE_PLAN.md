# Overdrive — Feature Upgrade Plan

## Objective

A proposed engineering platform that analyses a process, finds bottlenecks and compares possible ways to improve it.

## P0 — narrow scope and measurable baseline

- [ ] Choose one bounded domain/process and define measurable objective, constraints, inputs and outputs.
- [ ] Create a deterministic baseline and synthetic benchmark with documented assumptions.

## P1 — first useful optimiser

- [ ] Implement a transparent bottleneck report and one optimiser for the selected problem.
- [ ] Add a simulation adapter with clear boundaries and reproducible configurations.

## P2 — generalisation and agent safety

- [ ] Compare optimisation methods against baseline across fixed scenarios and sensitivity tests.
- [ ] Add agent orchestration only with permissions, audit logs and human approval for external actions.

## Collaboration work packages

1. Select one use case and specify objective/constraints.
2. Build reproducible baseline and data fixtures.
3. Implement one algorithm and compare quality/runtime.
4. Add simulation adapter with audit and safety constraints.

## Definition of done

- [ ] The supported problem and non-goals are explicit.
- [ ] Baseline and optimiser use identical inputs/constraints.
- [ ] Metrics are reproducible and include failure cases.
- [ ] Any agent action has explicit permissions and human approval.
