.DEFAULT_GOAL := help

init: ## Initialize repository
	git config core.hooksPath .githooks
	git config commit.template .gitmessage

lock: ## Updates the lockfiles without installing dependencies
	rye lock --all-features --update-all

sync: ## Updates the virtualenv based on the pyproject.toml
	rye sync --all-features --no-lock || rye sync --all-features --no-lock --force

format: ## Run formatters
	@echo Formatting...
	# YAML
	@yamlfmt .
	# Python
	@rye fmt

lint: ## Run linters
	@echo Linting...
	# Renovate
	@check-jsonschema --builtin-schema vendor.renovate ./.github/renovate*.json
	# GitHub Actions
	@check-jsonschema --builtin-schema vendor.github-workflows ./.github/workflows/*.yml
	@actionlint
	# YAML
	@yamlfmt -lint .
	@yamllint .
	# Python
	@rye fmt --check
	@rye lint

test: ## Run project test
	rye test

build: ## Build project
	rye build

clean: ## Remove build artifacts
	rm -rf ./dist/
	find . -type d -name "__pycache__" | xargs rm -rf

help: ## Show help message
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m\033[0m\n"} /^[$$()% 0-9a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

.PHONY: build format help init lint lock sync test
