.DEFAULT_GOAL := help

UV ?= uv
PYTEST_ARGS ?=

.PHONY: check clean docs docs-html help lint lock lock-check package package-check package-distribution package-upload sync sync-runtime test upgrade

lock:  ## Update the lockfile without upgrading locked dependencies
	$(UV) lock

lock-check:  ## Verify that the lockfile is up to date
	$(UV) lock --check

upgrade:  ## Upgrade all locked dependencies
	$(UV) lock --upgrade

sync:  ## Sync the project and development dependencies
	$(UV) sync --locked

sync-runtime:  ## Sync only the project and runtime dependencies
	$(UV) sync --locked --no-dev

lint:  ## Run all pre-commit checks
	$(UV) run --locked pre-commit run --all-files --show-diff-on-failure

check: lock-check lint  ## Verify the lockfile and run all checks

test:  ## Run the test suite; pass options with PYTEST_ARGS
	$(UV) run --locked pytest $(PYTEST_ARGS)

docs:  ## Run the documentation doctests and check the documentation builds
	$(UV) run --locked --directory docs sphinx-build -WT -b doctest -d _build/doctrees . _build/html
	$(UV) run --locked --directory docs sphinx-build -WT -b dummy -d _build/doctrees . _build/html

docs-html:  ## Build the HTML documentation into docs/_build/html
	$(UV) run --locked --directory docs sphinx-build -WT -b html -d _build/doctrees . _build/html

package-distribution: clean  ## Create distribution packages
	$(UV) build

package-check: package-distribution  ## Check the distribution is valid
	$(UV) tool run twine check --strict dist/*

package-upload: package-check  ## Upload distribution packages
	$(UV) tool run twine upload dist/* --repository-url https://upload.pypi.org/legacy/

package: package-upload

clean:  ## Clean the package directory
	rm -rf metsrw.egg-info/
	rm -rf build/
	rm -rf dist/

help:  ## Print this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
