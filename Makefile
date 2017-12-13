PYTHON = python

.PHONY: test clean* test* upload

## Testing
test: test-man test-sdist-man
	tox

test-man: clean-man
	${PYTHON} setup.py generate_man
	test -e git-blackhole.1
	test -e git-blackhole-basic-usage.5

test-sdist-man: clean-man clean-notox
	${PYTHON} setup.py sdist
	[ $$(ls -1 dist/*.tar.gz | wc -l) = 1 ]
	tar tzf dist/*.tar.gz | grep '/git-blackhole\.1$$'
	tar tzf dist/*.tar.gz | grep '/git-blackhole-basic-usage\.5$$'

clean: clean-man clean-notox
	rm -rf .tox

clean-notox:
	rm -rf *.pyc __pycache__ build dist *.egg-info MANIFEST

clean-man:
	rm -f git-blackhole.1 git-blackhole-basic-usage.5

## Man
preview-git-blackhole.1 preview-git-blackhole-basic-usage.5: preview-%:
	misc/$*.sh - | man --local-file -

preview-git-blackhole.rst preview-git-blackhole-basic-usage.rst: preview-%:
	misc/$*.sh - | pygmentize -l rst | less -R

README.rst: misc/README.rst.sh misc/git-blackhole.rst.sh \
misc/readme-pre.rst misc/readme-post.rst git_blackhole.py
	$< > $@

## Upload to PyPI
upload: clean-man clean-notox
	python setup.py sdist
	twine upload dist/*
