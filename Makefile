PROJECT = git_blackhole

.PHONY: test clean clean-pycache cog upload

## Testing
test: cog
	tox

clean: clean-pycache
	rm -rf *.egg-info .tox MANIFEST

clean-pycache:
	find $(PROJECT) -name __pycache__ -o -name '*.pyc' -print0 \
		| xargs --null rm -rf

## Update files using cog.py
cog: $(PROJECT)/__init__.py
$(PROJECT)/__init__.py: README.rst
	cd $(PROJECT) && cog.py -r __init__.py

## Upload to PyPI
upload: cog
	python setup.py register sdist upload
