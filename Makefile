.PHONY: clean package package-deps package-source package-upload package-wheel

package-deps:
	pip install --upgrade twine wheel

package-source:
	python setup.py sdist

package-wheel: package-deps
	python setup.py bdist_wheel

package-check: package-source package-wheel     ## Check the distribution is valid
	twine check dist/*

package-upload: package-deps package-check
	twine upload dist/* --repository-url https://upload.pypi.org/legacy/

package: package-upload

clean:
	rm -rf metsrw.egg-info/
	rm -rf build/
	rm -rf dist/

pip-compile:
	pip-compile --allow-unsafe --output-file=requirements.txt pyproject.toml
	pip-compile --allow-unsafe --extra=dev --output-file=requirements-dev.txt pyproject.toml

pip-upgrade:
	pip-compile --allow-unsafe --upgrade --output-file=requirements.txt pyproject.toml
	pip-compile --allow-unsafe --upgrade --extra=dev --output-file=requirements-dev.txt pyproject.toml
