SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c

.PHONY: help \
	uv.run \
	format format-check \
	lint lint-fix \
	ci


help: ## Show dynamic help for available targets
	@echo "Available targets:"
	@sh -c 'awk '\''BEGIN {FS = ":.*## "} /^[a-zA-Z0-9_.%\/-]+:.*## / {printf "  %-22s %s\n", $$1, $$2}'\'' $(MAKEFILE_LIST)'

uv.run: ## Run the command specified in CMD. Example: make uv.run CMD='ruff check'
	@test -n "$(CMD)" || (echo "Missing CMD. Example: make uv.run CMD='ruff check'" && exit 1)
	@uv run $(CMD)

format: ## Format code using ruff
	@echo "Formatting code with ruff..."
	@$(MAKE) --no-print-directory uv.run CMD='ruff format'

format-check: ## Check code formatting using ruff
	@echo "Checking code formatting with ruff..."
	@$(MAKE) --no-print-directory uv.run CMD='ruff format --check'

lint: ## Lint code using ruff
	@echo "Linting code with ruff..."
	@$(MAKE) --no-print-directory uv.run CMD='ruff check'

lint-fix: ## Lint code and automatically fix issues using ruff
	@echo "Linting code and fixing issues with ruff..."
	@$(MAKE) --no-print-directory uv.run CMD='ruff check --fix'
