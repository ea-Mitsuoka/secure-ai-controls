# ADR-0005: Adopt terraform-gcp-template as the direct parent template

| Field                      | Value                                                                                                                                              |
| -------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| Status                     | accepted                                                                                                                                           |
| Date                       | 2026-07-16                                                                                                                                         |
| Deciders                   | repository owner                                                                                                                                   |
| Author                     | Claude (AI agent)                                                                                                                                  |
| Supersedes / Superseded by | Changes the parentage assumed at instantiation (direct ai-dev-foundation); governed by [ADR-0004](0004-harden-multi-level-template-inheritance.md) |

## Context

This repository was instantiated directly from `ai-dev-foundation`. Phase② (基盤試作)
needs Terraform-specific scaffolding that `ai-dev-foundation` does not carry:

- `infra/envs/<env>/` root-config layout that references modules from
  `terraform-gcp-modules` by pinned tag (requirements decision #13).
- A Makefile wired to that layout (`terraform fmt/validate/test` over `infra/`,
  `plan ENV=<env>`) instead of the current hand-rolled Makefile, which guards a
  non-canonical `terraform/` directory — already a divergence from the shared convention.
- An IaC-misconfiguration scan wired as a **required** check.
- A GitHub governance profile that declares that required check.

`terraform-gcp-template` (public, `is_template`) already inherits from `ai-dev-foundation`
and adds exactly this layer: `infra/`, `.github/workflows/iac.yml` + a `terraform-gcp`
governance profile requiring `iac-scan`, a Terraform-wired Makefile, and governance /
workflow contract tests. [ADR-0004](0004-harden-multi-level-template-inheritance.md)
established a hardened, manifest-owned, direct-parent, multi-level inheritance contract and
explicitly anticipates the chain `ai-dev-foundation -> terraform-gcp-template -> child`.

Two facts constrain how far this decision can be executed today:

- `terraform-gcp-template` currently **lags** `ai-dev-foundation`: it has no ADR-0004, and
  its `iac.yml` job is named `scan`-era `iac-scan` while our inherited `iac.yml` is a later,
  path-filtered revision. The owner syncs it at least weekly and is migrating it to
  commit-based sync, so the lag is bounded and self-healing.
- The commit-based inheritance tool (`scripts/template_inheritance.py`) supports `validate`
  and `plan` only — **materialization (writing inherited files) is a follow-up**. So the
  manifest can be declared and validated now, but files are not pulled automatically yet.

## Options considered

### Option 1: Do nothing

Keep `ai-dev-foundation` as the informal source and hand-maintain the Terraform layer.

- **Pros:** no new coupling; nothing to set up.
- **Cons:** re-derives the Terraform layer already solved in `terraform-gcp-template`; the
  hand-rolled Makefile keeps drifting from the canonical `infra/` layout; every future GCP
  repo repeats the work. Fails the DRY intent of the whole template ecosystem.

### Option 2: One-off cherry-pick of the Terraform files

Copy `infra/`, the Terraform Makefile, the `terraform-gcp` profile, and the tests once.

- **Pros:** unblocks Phase② immediately; no coupling to an intermediate template.
- **Cons:** frozen copies drift from upstream improvements; still needs a local owner;
  ignores that ADR-0004 was built precisely to avoid this.

### Option 3: Adopt terraform-gcp-template as the direct parent (chosen)

Point this repo's ADR-0004 inheritance manifest at `terraform-gcp-template`.

- **Pros:** single source of truth for Terraform conventions across the growing set of GCP
  repos; infra/iac improvements flow down automatically; matches ADR-0004's intended
  topology; retires the hand-rolled Makefile debt path.
- **Cons:** couples to an intermediate template that must stay current (lag risk, bounded by
  ≥weekly sync); nothing materializes until the tool's materialize step lands, so Phase②
  still needs an interim manual adoption; this repo's ADR numbering now advances
  independently of the foundation's.

## Decision

Choose Option 3. This repository's direct template parent MUST be
`Yukihide-Mitsuoka/terraform-gcp-template`, governed by the
[ADR-0004](0004-harden-multi-level-template-inheritance.md) manifest contract. The parentage
is declared now via `.github/inheritance/manifest.json` + `lock.json` (pinned to
`terraform-gcp-template` commit `e2b42fc`), and MUST validate with
`python3 scripts/template_inheritance.py validate --root .`.

Project-authored or customized files (requirements docs, mission, CLAUDE.md, README,
CODEOWNERS, the workspace index, local governance, the customized `dependabot.yml`) MUST be
listed as `protected_paths`. Shared foundation files plus the Terraform scaffolding MUST be
listed as `inherited_paths`.

Because materialization is not implemented yet, actual adoption of the Terraform layer
(`infra/`, the Terraform Makefile, the `terraform-gcp` governance profile, wiring `iac-scan`
as a required check) is DEFERRED to Phase② start, done as a reviewed `plan`-then-apply once
the tool supports it, or as a single reviewed manual copy if Phase② begins first. The
`scan` vs `iac-scan` job-name mismatch MUST be reconciled at that point so the required
check name matches the profile.

## Consequences

**Positive:**

- Terraform conventions live in one place; this repo and future GCP repos inherit them.
- Removes the hand-rolled Makefile as a maintained divergence.
- Uses ADR-0004 as designed, validating that contract on a real second consumer.

**Negative:**

- Adds a dependency on an intermediate template that must be kept synced; a stale parent
  would propagate stale foundation files. Mitigated by the owner's ≥weekly sync.
- No files move until materialization ships, so Phase② needs an interim manual adoption and
  this ADR does not by itself change any runtime behavior.
- ADR and decision-log numbering now diverge from the foundation's; a future foundation
  ADR-0005 would collide and need renumbering here.

**Follow-ups:**

- Create `.github/inheritance/manifest.json` + `lock.json`; validate.
- Repoint `.github/workflows/template-sync.yml` source to `terraform-gcp-template` as the
  interim file-transport, kept opt-in and disabled (`TEMPLATE_SYNC_ENABLED` unset).
- Append decision-log entries (DOC-030); update `secure-ai-controls.md` and
  `docs/phase2-prep.md` to name the new parentage.
- At Phase② start: `plan` against the parent, review, then materialize/copy `infra/` + the
  Terraform Makefile + the `terraform-gcp` profile, and make `iac-scan` a required check with
  a matching job name.
