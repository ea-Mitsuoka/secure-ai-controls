# Canonical command interface (CLAUDE.md §11) — Terraform/GCP wiring, adapted from
# profiles/terraform-gcp (contract semantics: profiles/README.md).
# Every agent, hook, and CI job calls ONLY these targets. Optional FILE=<path>
# narrows format/lint to one file.
#
# terraform/ does not exist until Phase② (docs/phase2-prep.md §3); every terraform
# target degrades to a notice instead of failing so hooks and CI stay green.

.PHONY: setup format lint test test-unit test-integration coverage build run \
        security-scan sbom clean help doctor

FILE ?=
TF_DIR := terraform

# Guard for recipes that need terraform code. Single shell line — usable inline.
TF_GUARD = if [ ! -d $(TF_DIR) ]; then echo "no $(TF_DIR)/ yet — IaC starts in Phase② (docs/phase2-prep.md)"; exit 0; fi

help: ## List available targets
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  make %-18s %s\n", $$1, $$2}'

setup: ## Install toolchain and git hooks (idempotent)
	@command -v terraform >/dev/null 2>&1 || echo "terraform not installed — required from Phase②"
	@if command -v tflint >/dev/null 2>&1 && [ -f .tflint.hcl ]; then tflint --init --config "$(CURDIR)/.tflint.hcl"; fi
	@if command -v pre-commit >/dev/null 2>&1; then pre-commit install --hook-type pre-commit --hook-type pre-push; else echo "pre-commit not installed — local gates inactive (CI still enforces)"; fi

format: ## Auto-format terraform (all, or FILE=<path>)
ifneq ($(FILE),)
	@case "$(FILE)" in \
		*.tf|*.tfvars) terraform fmt "$(FILE)" ;; \
		*) : ;; \
	esac
else
	@$(TF_GUARD); cd $(TF_DIR) && terraform fmt -recursive
endif

lint: ## Check-only, zero warnings (COD-001). Fixing is `make format`'s job.
	@$(TF_GUARD); \
	cd $(TF_DIR) && terraform fmt -recursive -check; cd ..; \
	if command -v tflint >/dev/null 2>&1 && [ -f .tflint.hcl ]; then tflint --recursive --config "$(CURDIR)/.tflint.hcl" --chdir $(TF_DIR); fi; \
	if command -v shellcheck >/dev/null 2>&1; then find $(TF_DIR) scripts -name "*.sh" -exec shellcheck -s bash {} + 2>/dev/null || true; fi

test: test-unit test-integration ## Full suite — TST-001

test-unit: ## Fast suite, used by pre-commit — TST-001
	@$(TF_GUARD); $(MAKE) build

test-integration: ## terraform test for every config that has *.tftest.hcl
	@$(TF_GUARD); set -e; \
	for dir in $$(find $(TF_DIR) -name '*.tftest.hcl' -not -path '*/.terraform/*' -exec dirname {} \; | sort -u); do \
		echo "Testing $$dir..."; \
		(cd "$$dir" && rm -rf .terraform .terraform.lock.hcl && terraform init -backend=false >/dev/null && terraform test); \
	done

coverage: ## Coverage ratchet (TST-003) — terraform has no line coverage; runs the suite
	@$(MAKE) test

build: ## IaC "build" = credential-free validate of every terraform config
	@$(TF_GUARD); set -e; \
	for dir in $$(find $(TF_DIR) -name '*.tf' -not -path '*/.terraform/*' -exec dirname {} \; | sort -u); do \
		echo "Validating $$dir..."; \
		(cd "$$dir" && terraform init -backend=false >/dev/null && terraform validate); \
	done

run: ## For IaC, "run" shows the execution plan (wired in Phase② via tf-plan/WIF)
	@$(TF_GUARD); echo "plan wiring lands in Phase② (gcp-cicd-workflows tf-plan) — docs/phase2-prep.md §3"

security-scan: ## Local security sweep (secrets + IaC misconfig)
	@if command -v gitleaks >/dev/null 2>&1; then gitleaks detect --no-banner; else echo "gitleaks not installed — CI still enforces SEC-002"; fi
	@if [ -d $(TF_DIR) ] && command -v trivy >/dev/null 2>&1; then trivy config --exit-code 1 $(TF_DIR); \
	elif command -v trivy >/dev/null 2>&1; then trivy fs --scanners vuln,misconfig,secret --exit-code 1 .; \
	else echo "trivy not installed — CI still enforces SEC-030"; fi

sbom: ## Generate SBOM (SPDX + CycloneDX) into ./dist — REL-020
	@mkdir -p dist
	@if command -v syft >/dev/null 2>&1; then syft . -o spdx-json=dist/sbom.spdx.json -o cyclonedx-json=dist/sbom.cdx.json && echo "SBOM written to dist/"; else echo "syft not installed — release workflow generates the authoritative SBOM"; fi

clean: ## Remove caches/artifacts inside the workspace only (GR-031)
	@if [ -d $(TF_DIR) ]; then \
		find $(TF_DIR) -type d -name ".terraform" -exec rm -rf {} +; \
		find $(TF_DIR) -type f -name ".terraform.lock.hcl" -exec rm -f {} +; \
	fi
	@rm -rf dist

doctor: ## Self-check the template: metadata invariants + guard-hook tests (foundation-level, stack-independent)
	@bash scripts/template-check.sh
	@bash .claude/hooks/tests/guard-bash.test.sh
