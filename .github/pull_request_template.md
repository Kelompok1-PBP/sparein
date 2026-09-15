<!--
Title must follow Conventional Commits, e.g. feat(guides): add safety warning list
Squash merge turns this title into the commit that lands on dev.
-->

## What changed

<!-- One or two sentences. What the reviewer will see, not how you built it. -->

## Why

<!-- The problem this solves. Link the issue: Closes #NN -->

Closes #

## Module

- [ ] `core` (shared, needs two approvals)
- [ ] `devices` (M1)
- [ ] `diagnostics` (M2)
- [ ] `guides` (M3)
- [ ] `parts` (M4)
- [ ] `journal` (M5)

## Contract impact

- [ ] No other module is affected
- [ ] Another module's contract changes, `docs/MODULES.md` is updated in this PR, and a `breaking` issue was opened first

## Checklist

- [ ] Branched from `dev` and targets `dev`
- [ ] Branch name matches `<type>/<module>-<slug>`
- [ ] `ruff check .` passes
- [ ] `python manage.py makemigrations --check --dry-run` passes
- [ ] `python manage.py test` passes
- [ ] Tests cover the new behaviour, including the auth filter
- [ ] Migrations touch only my own app
- [ ] No credential, `.env`, or secret in the diff

## How to verify

<!-- The exact steps a reviewer runs to see this work. -->

1.
2.

## Screenshots

<!-- UI changes only. Before and after. -->
