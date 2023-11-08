.DEFAULT_GOAL := help

.PHONY: clean package package-deps package-distribution package-upload pip-compile pip-upgrade

package-deps:  ## Upgrade dependencies for packaging
	python3 -m pip install --upgrade build twine

package-distribution: package-deps  ## Create distribution packages
	python3 -m build

package-check: package-distribution  ## Check the distribution is valid
	python3 -m twine check --strict dist/*

package-upload: package-deps package-check  ## Upload distribution packages
	python3 -m twine upload dist/* --repository-url https://upload.pypi.org/legacy/

package: package-upload

clean:  ## Clean the package directory
	rm -rf metsrw.egg-info/
	rm -rf build/
	rm -rf dist/

pip-compile:  ## Compile pip requirements
	pip-compile --allow-unsafe --output-file=requirements.txt pyproject.toml
	pip-compile --allow-unsafe --extra=dev --output-file=requirements-dev.txt pyproject.toml

pip-upgrade:  ## Upgrade pip requirements
	pip-compile --allow-unsafe --upgrade --output-file=requirements.txt pyproject.toml
	pip-compile --allow-unsafe --upgrade --extra=dev --output-file=requirements-dev.txt pyproject.toml

help:  ## Print this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
