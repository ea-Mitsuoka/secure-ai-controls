---
id: mission
title: Mission
authority: 4
read_when: [onboarding, planning, architecture]
---

# Mission

## What this project is

secure-ai-controls — Terraform-built control infrastructure plus an audit-log monitoring
pipeline that places internal generative-AI usage (Vertex AI / Gemini) under governance
on Google Cloud, proven in a client-zero verification environment (fiscal-year goal 3,
2026-04 to 2027-03). Normative requirements: [docs/requirements.md](../docs/requirements.md)
(draft-v0.5, all open items decided — decision records #1–#14).

| Field                   | Value                                                                                                                                                                                                                                                        |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Problem being solved    | Internal gen-AI use lacks deterministic guardrails for three control requirements: sensitive-data filtering, prompt audit-log monitoring, and output legal compliance (technically detectable scope)                                                         |
| Primary users           | Internal AI taskforce; platform/security administrators operating the controlled environment                                                                                                                                                                 |
| Core value              | The three control requirements mapped to concrete GCP features (Model Armor, Sensitive Data Protection, request-response logging, Cloud Audit Logs, VPC-SC, Org Policy, CMEK) and enforced as reusable Terraform modules with a log→detection→alert pipeline |
| Explicitly out of scope | Legal judgments not technically detectable (copyright, grounding correctness); application-side changes; model quality tuning; general (non-AI) infrastructure — see requirements §2.5                                                                       |

## Success criteria

1. Goal B (baseline, by 2027-03): the verification environment demonstrates
   sensitive-data detection and prompt-audit-log capture → alert, delivered as
   (a) design doc mapping the 3 requirements to GCP features, (b) Terraform IaC,
   (c) log→detection→alert pipeline, plus demonstration logs.
2. Goal A: self-conducted red-teaming (prompt injection, data-exfiltration attempts)
   proves detection works, with a results report and expanded detection rules.

## Role of AI agents in this project

AI agents are long-term team members, not code generators. Expectations:

- **Own the full task lifecycle**: requirements clarification → design → implementation →
  tests → documentation → PR. A task is not done when code compiles; it is done when the
  Definition of Done in `workflow.md` (WF-090) is met.
- **Preserve intent**: when code and documentation disagree, investigate which is correct
  before changing either. Record the resolution.
- **Prefer reversible steps**: small PRs, feature flags, additive migrations.
- **Escalate, don't guess**: for the escalation triggers listed in `CLAUDE.md` §13, stop
  and ask the human. For everything else, decide and record the reasoning.

## Human role

Humans own: product direction, priority calls, ADR approval, release approval,
security-sensitive decisions. AI prepares options and recommendations; humans decide.
Division of responsibility with the technical lead: this project owns the AI-control
layer end to end; general infrastructure stays with the lead. No upfront working-group
sign-off — review happens at the production/release stage (decision record #14).
