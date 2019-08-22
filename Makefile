.PHONY: clean package package-deps package-source package-upload package-wheel

package-deps:
	pip install --upgrade twine wheel

package-source:
	python setup.py sdist

package-wheel: package-deps
	python setup.py bdist_wheel --universal

package-check: package-source package-wheel     ## Check the distribution is valid
	twine check dist/*

package-upload: package-deps package-check
	twine upload dist/* --repository-url https://upload.pypi.org/legacy/

package: package-upload

clean:
	rm -rf metsrw.egg-info/
	rm -rf build/
	rm -rf dist/
