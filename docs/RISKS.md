# Risk Register

Nine risks, each with an owner, a trigger that says when to act, and a mitigation that is already in place rather than planned. Reviewed at every checkpoint.

Likelihood and impact are scored Low / Medium / High. Severity is the pair that decides review order.

| # | Risk | Likelihood | Impact | Owner |
|---|---|---|---|---|
| R1 | `devices` slips and blocks three modules | Medium | High | M1 owner |
| R2 | iFixit API unavailable or rate-limited | Medium | High | M1 + M3 owners |
| R4 | First PWS deployment attempted too late | Medium | High | M1 owner |
| R8 | PWS credentials committed to the repository | Low | High | whole team |
| R3 | Merge conflicts in `core/` | High | Medium | whole team |
| R6 | Branched migrations from parallel work | Medium | Medium | whole team |
| R9 | Pull requests pile up unreviewed | High | Medium | whole team |
| R5 | A member becomes unavailable | Low | Medium | whole team |
| R7 | Coverage below 80% near the deadline | Medium | Medium | whole team |

---

## R1. `devices` slips and blocks three modules

`diagnostics`, `guides`, and `parts` all hold a `Device` foreign key. If M1 is late, three people idle.

**Trigger:** models, migration, and `devices/fixtures/seed_devices.json` are not merged into `dev` by 21 September 2026.

**Mitigation in place.** The deliverable is split: the `Device` shape plus a loadable fixture lands first, views and templates follow. Layer 2 builds against the fixture, so M1 finishing its own UI is not on anyone else's critical path.

**If the trigger fires.** Whoever is available freezes the `Device` model as it stands, merges it, and M1 builds on top of that. An imperfect schema that ships unblocks three people; a perfect one that is late does not.

---

## R2. iFixit API unavailable or rate-limited

`https://www.ifixit.com/api/2.0` needs no key, which also means no quota guarantee. A demo that live-fetches is a demo that can fail in front of an assistant.

**Trigger:** `seed_devices` returns a non-2xx status, or a page waits on an upstream call at render time.

**Mitigation in place.** The API is called once by a management command, never during a request. Results are written to the database, responses are cached, and a fixture snapshot is committed so a fresh clone seeds with the network switched off.

---

## R3. Merge conflicts in `core/`

`base.html`, the navbar, and the Tailwind config are touched by everyone.

**Trigger:** two open pull requests both modify a file under `core/`.

**Mitigation in place.** CODEOWNERS routes `core/` to the whole team and requires two approvals. Modules add `{% block %}` content instead of editing shared markup. Anyone about to touch `core/` says so in the group chat first.

---

## R4. First PWS deployment attempted too late

A pipeline nobody has run yet usually breaks on its first real use, and the last week is the worst time to find out.

**Trigger:** no successful `deploy-pws` run by 2 October 2026, the Checkpoint 2 deadline.

**Mitigation in place.** `deploy-pws.yml` is committed at Checkpoint 1 and fires on every merge to `main`. The first release ships a nearly empty app on purpose, so the pipeline is proven before there is anything to lose.

---

## R5. A member becomes unavailable

Illness, another course, anything. Five modules and five people leaves no slack.

**Trigger:** a module has no commit for seven days, or the owner says they are blocked.

**Mitigation in place.** Every module has a named backup reviewer who has read its code since the first pull request, so handover does not start from zero. Module scope is sized so one person can absorb a second module's remaining CRUD if it comes to that.

---

## R6. Branched migrations from parallel work

Two members generating migrations in the same app produces multiple leaf nodes and a merge that Django refuses to run.

**Trigger:** `python manage.py makemigrations --check --dry-run` fails in CI.

**Mitigation in place.** One app, one owner. That check runs on every pull request, so a branched migration is caught before review, not during integration week.

---

## R7. Coverage below 80% near the deadline

Tests written in the final week tend to be shallow, and coverage is a scored line in the rubric.

**Trigger:** a pull request lands with new views and no test, or the coverage report drops below 80%.

**Mitigation in place.** CI prints the coverage number on every pull request from Checkpoint 1 onward, so the trend is visible weekly. Each module's definition of done includes tests for all four CRUD operations and its auth filter.

---

## R8. PWS credentials committed to the repository

`PWS_URL` embeds the SSO username and the project password. A public repository makes a leak permanent.

**Trigger:** any string matching `https://.*:.*@pws\.cs\.ui\.ac\.id` appears in a diff.

**Mitigation in place.** The URL exists only as a GitHub repository secret. `.env` and `*.env` are gitignored. Secret scanning and push protection are enabled on the repository.

**If the trigger fires.** Rotate the PWS project password first, then clean the history. Rotation is what closes the hole; rewriting history only removes the trace.

---

## R9. Pull requests pile up unreviewed

Five parallel branches with slow review means everyone rebases onto stale work.

**Trigger:** a ready-for-review pull request is older than 24 hours.

**Mitigation in place.** Review SLA is 24 hours. Incomplete work stays in Draft so the review queue only holds things that are actually reviewable. Branches sync from `dev` frequently rather than at the end, which keeps each conflict small.
