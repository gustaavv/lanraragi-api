SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
MAKEFLAGS += --no-print-directory

DOCS_SOURCE_DIR := docs/source
DOCS_TARGET_DIR := docs/build
# Coverage reports go straight into the docs output so that they ship in the same
# artifact: `make test.unit` / `test.integration` fill them in, `make docs.build`
# reuses them, and the docs workflow downloads CI's artifacts back into this directory.
# Each suite also keeps its raw data as .coverage.unit / .coverage.integration, which the
# test.coverage.* targets combine into a third report and the badge.
DOCS_COVERAGE_DIR := $(DOCS_TARGET_DIR)/html/coverage
COVERAGE_UNIT_DATA := .coverage.unit
COVERAGE_INTEGRATION_DATA := .coverage.integration
COVERAGE_COMBINED_DATA := .coverage.combined


.PHONY: help
help: ## Show dynamic help for available targets
	@echo "Available targets:"
	@sh -c 'awk '\''BEGIN {FS = ":.*## "} /^[a-zA-Z0-9_.%\/-]+:.*## / {printf "  %-22s %s\n", $$1, $$2}'\'' $(MAKEFILE_LIST)'

.PHONY: install
install: ## Install all the project dependencies. Use UV_OPTS for additional options
	uv sync --group={dev,docs} $(UV_OPTS)

.PHONY: install.docs
install.docs: ## Install only the docs dependencies. Use UV_OPTS for additional options
	uv sync --only-group docs $(UV_OPTS)

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
test.unit: ## Run unit test. Use PYTEST_OPTS for additional options
	@echo "Run unit test"
	@COVERAGE_FILE=$(COVERAGE_UNIT_DATA) uv run pytest $(PYTEST_OPTS) --cov-report=html:$(DOCS_COVERAGE_DIR)/unit tests/unit

.PHONY: test.integration
test.integration: ## Run integration test. Use PYTEST_OPTS for additional options
	@echo "Run integration test"
	@$(MAKE) tools.check TOOL=docker
	@docker compose -f script/integration_test_setup/compose.yml down -v
	@docker compose -f script/integration_test_setup/compose.yml up -d --quiet-pull
	@uv run script/integration_test_setup/config_lrr.py --base-url http://localhost:33333 --lrr-container-name lrr_api_test_lrr
	@COVERAGE_FILE=$(COVERAGE_INTEGRATION_DATA) uv run pytest $(PYTEST_OPTS) --cov-report=html:$(DOCS_COVERAGE_DIR)/integration tests/integration
	@docker compose -f script/integration_test_setup/compose.yml down -v

# There is deliberately no rule creating the data files: if a suite has not been run
# yet, make aborts instead of building a partial report. --keep is load-bearing, as
# coverage deletes the data files it combines unless told not to.
$(COVERAGE_COMBINED_DATA): $(COVERAGE_UNIT_DATA) $(COVERAGE_INTEGRATION_DATA)
	@echo "Combine coverage data"
	@uv run coverage combine --keep --data-file=$@ $(COVERAGE_UNIT_DATA) $(COVERAGE_INTEGRATION_DATA)

.PHONY: test.coverage.combined
test.coverage.combined: $(COVERAGE_COMBINED_DATA) ## Combine both suites into a third coverage report
	@uv run coverage html --data-file=$(COVERAGE_COMBINED_DATA) -d $(DOCS_COVERAGE_DIR)/combined

.PHONY: test.coverage.badge
test.coverage.badge: $(COVERAGE_COMBINED_DATA) ## Generate the coverage badge from the combined coverage data
	@echo "Generate the coverage badge"
	@uv run coverage xml --data-file=$(COVERAGE_COMBINED_DATA) -o coverage.xml
	@uv run genbadge coverage -i coverage.xml -o $(DOCS_TARGET_DIR)/html/coverage-badge.svg

.PHONY: docs.gen
docs.gen: ## Generate API docs
	@uv run sphinx-apidoc -f -o docs/source src/lanraragi_api

.PHONY: docs.gen-check
docs.gen-check: docs.gen ## Check that generated API docs are in sync with the code
	@git add -N 'docs/source/*.rst'
	@if ! git diff --quiet -- 'docs/source/*.rst'; then \
		echo "❌ API docs are out of sync with the code."; \
		echo "   Run 'make docs.gen' and commit the changes."; \
		echo; \
		git diff --stat -- 'docs/source/*.rst'; \
		exit 1; \
	fi
	@echo "✅ API docs are up to date."

.PHONY: docs.build
docs.build: docs.gen-check ## Build docs
	@uv run sphinx-build -M html "$(DOCS_SOURCE_DIR)" "$(DOCS_TARGET_DIR)"

DOCS_SERVE_PORT ?= 38000
.PHONY: docs.serve
docs.serve: ## Serve the docs built locally. Use DOCS_SERVE_PORT to change the default port (38000)
	@cd $(DOCS_TARGET_DIR)/html && uv run python -m http.server $(DOCS_SERVE_PORT)

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