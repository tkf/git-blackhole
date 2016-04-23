PYTHON = python

.PHONY: test clean clean-man upload

## Testing
test:
	tox

test-man: clean-man
	${PYTHON} setup.py generate_man
	test -e git-blackhole.1
	test -e git-blackhole-basic-usage.5

clean: clean-man
	rm -rf *.pyc __pycache__ build dist *.egg-info .tox MANIFEST

clean-man:
	rm -f git-blackhole.1 git-blackhole-basic-usage.5

## Man
preview-git-blackhole.1 preview-git-blackhole-basic-usage.5: preview-%:
	misc/$*.sh - | man --local-file -

preview-git-blackhole.rst preview-git-blackhole-basic-usage.rst: preview-%:
	misc/$*.sh - | pygmentize -l rst | less -R

## Upload to PyPI
upload:
	python setup.py register sdist upload
