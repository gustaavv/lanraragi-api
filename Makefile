SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
MAKEFLAGS += --no-print-directory


.PHONY: help
help: ## Show dynamic help for available targets
	@echo "Available targets:"
	@sh -c 'awk '\''BEGIN {FS = ":.*## "} /^[a-zA-Z0-9_.%\/-]+:.*## / {printf "  %-22s %s\n", $$1, $$2}'\'' $(MAKEFILE_LIST)'

.PHONY: format
format: ## Format code using ruff
	@echo "Formatting code with ruff..."
	@uv run ruff format

.PHONY: format-check
format-check: ## Check code formatting using ruff
	@echo "Checking code formatting with ruff..."
	@uv run ruff format --check

.PHONY: lint
lint: ## Lint code using ruff
	@echo "Linting code with ruff..."
	@uv run ruff check

.PHONY: lint-fix
lint-fix: ## Lint code and automatically fix issues using ruff
	@echo "Linting code and fixing issues with ruff..."
	@uv run ruff check --fix

.PHONY: test
test: test.unit ## Short for test.unit target

.PHONY: test.unit
test.unit: ## Run unit test
	@echo "Run unit test"
	@uv run pytest tests/unit

.PHONY: test.integration
test.integration: ## Run integration test
	@echo "Run integration test"
	@$(MAKE) tools.check TOOL=docker
	@docker compose -f script/integration_test_setup/compose.yml down -v
	@docker compose -f script/integration_test_setup/compose.yml up -d --quiet-pull
	@uv run script/integration_test_setup/config_lrr.py --base-url http://localhost:33333 --lrr-container-name lrr_api_test_lrr
	@uv run pytest tests/integration
	@docker compose -f script/integration_test_setup/compose.yml down -v

.PHONY: docs.gen
docs.gen: ## Generate API docs
	@uv run sphinx-apidoc -f -o docs/source src/lanraragi_api

.PHONY: docs.gen-check
docs.gen-check: docs.gen ## Check that generated API docs are in sync with the code
	@git add -N docs/source
	@if ! git diff --quiet -- docs/source; then \
		echo "❌ API docs are out of sync with the code."; \
		echo "   Run 'make docs.gen' and commit the changes."; \
		echo; \
		git diff --stat -- docs/source; \
		exit 1; \
	fi
	@echo "✅ API docs are up to date."

.PHONY: docs.build
docs.build: docs.gen-check ## Build docs
	@uv run sphinx-build -M html "docs/source/" "docs/build/"

.PHONY: ci
ci: format-check lint docs.gen-check test.unit test.integration ## Run CI process locally

.PHONY: tools.check
tools.check:
	@if [ -z "$(TOOL)" ]; then \
		echo "ERROR: TOOL is required. Usage: make tools.check TOOL=<tool-name>" >&2; \
		exit 1; \
	fi
	@if ! command -v "$(TOOL)" >/dev/null 2>&1; then \
		echo "$(TOOL) not found."; \
		exit 1; \
	fi