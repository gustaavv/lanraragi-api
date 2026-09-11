SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c


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
	@docker compose -f script/integration_test_setup/compose.yml down -v
	@docker compose -f script/integration_test_setup/compose.yml up -d --quiet-pull
	@uv run script/integration_test_setup/config_lrr.py --base-url http://localhost:33333 --lrr-container-name lrr_api_test_lrr
	@uv run pytest tests/integration
	@docker compose -f script/integration_test_setup/compose.yml down -v

.PHONY: ci
ci: format-check lint test.unit test.integration ## Run CI process locally

.PHONY: docs.gen
docs.gen: ## Generate API docs
	@uv run sphinx-apidoc -f -o docs/source src/lanraragi_api

.PHONY: docs.build
docs.build: ## Build docs
	@uv run sphinx-build -M html "docs/source/" "docs/build/"

