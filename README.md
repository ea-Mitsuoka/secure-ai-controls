# secure-ai-controls

Terraform-built **control infrastructure + audit-log monitoring** that places internal
generative-AI usage (Vertex AI / Gemini) under governance on Google Cloud, proven in a
client-zero verification environment. Fiscal-year goal 3 (2026-04 → 2027-03).

> **AI agents:** stop reading this file. Your entry point is [CLAUDE.md](CLAUDE.md)
> (Claude Code) or [AGENTS.md](AGENTS.md) (everyone else).

## Start here

| Reader                                       | Document                                                                   |
| -------------------------------------------- | -------------------------------------------------------------------------- |
| Anyone (workspace index, 日本語)             | [secure-ai-controls.md](secure-ai-controls.md)                             |
| Requirements — all decisions #1–#14 (日本語) | [docs/requirements.md](docs/requirements.md)                               |
| Immutable goal statement (日本語)            | [docs/requirements/goal-statement.md](docs/requirements/goal-statement.md) |
| Phase② build checklist (日本語)              | [docs/phase2-prep.md](docs/phase2-prep.md)                                 |
| Mission / why this exists                    | [.ai/mission.md](.ai/mission.md)                                           |

## What gets built

Three control requirements, mapped to GCP features and enforced as Terraform modules
(requirements §3, decision #13):

| Control                                          | Enforced by                                                            | Module                                |
| ------------------------------------------------ | ---------------------------------------------------------------------- | ------------------------------------- |
| Sensitive-data filtering (input)                 | Model Armor + Sensitive Data Protection, project-level floor setting   | `model-armor-guard`                   |
| Prompt audit-log monitoring                      | request-response logging + Cloud Audit Logs → log-based metric → alert | `vertex-audit-pipeline`               |
| Output legal compliance (technically detectable) | Model Armor RAI / malicious-URL / PII response filters                 | `model-armor-guard`                   |
| Environment guardrails                           | VPC-SC perimeter; Org Policy subset; IAM least privilege; CMEK         | `vpc-sc-perimeter`, `ai-org-policies` |

Modules live in [terraform-gcp-modules](https://github.com/Yukihide-Mitsuoka/terraform-gcp-modules)
(tag-pinned git source); this repo holds the environment definitions, detection rules,
and demonstration scenarios.

## Working in this repo

- Rules single source of truth: [`.ai/`](.ai/) — guardrails first ([.ai/guardrails.md](.ai/guardrails.md)).
- All automation goes through `make` targets only (`make help` lists them) — CLAUDE.md §11.
- GitHub Flow; Conventional Commits; squash merge; PR template must be fully filled.
- Built from the ai-dev-foundation template; foundation updates arrive via template-sync PRs.

## License

MIT — see [LICENSE](LICENSE). Internal verification workspace; not an external product.
