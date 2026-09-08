SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c


.PHONY: help
help: ## Show dynamic help for available targets
	@echo "Available targets:"
	@sh -c 'awk '\''BEGIN {FS = ":.*## "} /^[a-zA-Z0-9_.%\/-]+:.*## / {printf "  %-22s %s\n", $$1, $$2}'\'' $(MAKEFILE_LIST)'

.PHONY: uv.run
uv.run: ## Run the command specified in CMD. Example: make uv.run CMD='ruff check'
	@test -n "$(CMD)" || (echo "Missing CMD. Example: make uv.run CMD='ruff check'" && exit 1)
	@uv run $(CMD)

.PHONY: format
format: ## Format code using ruff
	@echo "Formatting code with ruff..."
	@$(MAKE) --no-print-directory uv.run CMD='ruff format'

.PHONY: format-check
format-check: ## Check code formatting using ruff
	@echo "Checking code formatting with ruff..."
	@$(MAKE) --no-print-directory uv.run CMD='ruff format --check'

.PHONY: lint
lint: ## Lint code using ruff
	@echo "Linting code with ruff..."
	@$(MAKE) --no-print-directory uv.run CMD='ruff check'

.PHONY: lint-fix
lint-fix: ## Lint code and automatically fix issues using ruff
	@echo "Linting code and fixing issues with ruff..."
	@$(MAKE) --no-print-directory uv.run CMD='ruff check --fix'

.PHONY: test
test: ## Run tests
	@echo "Running tests"
	@$(MAKE) --no-print-directory uv.run CMD='pytest'

.PHONY: test.docker
test.docker: ## Run tests in docker
	@echo "Running tests in docker"
	@docker compose -f tests/compose.yml up --build --exit-code-from test