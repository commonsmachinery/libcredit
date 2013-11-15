
#
# Build settings
#

# Programming language implementations to build, dist etc
IMPL = python javascript

# Translations (human languages)
LANGUAGES = sv


#
# Tools etc
#

PYTHON = python
PO2JSON = $(top-dir)/tools/po2json
NPM = npm


#
# Internal variables
#

top-dir := $(shell pwd)
build-dir := $(top-dir)/build
dist-dir := $(top-dir)/dist
po-dir := $(top-dir)/po


#
# Main rules
#


all: build-common $(IMPL:%=build-%)

dist: dist-prepare-common $(IMPL:%=dist-%) dist-finish-common

clean:
	rm -r $(build-dir) $(dist-dir)

.PHONY: all dist clean

build-common:


dist-prepare-common:

dist-finish-common:


#
# Python
#

build-python:
	$(PYTHON) ./setup.py build

dist-python:
	$(PYTHON) ./setup.py sdist


#
# Javascript
#

js-locales-dir := $(top-dir)/javascript/locales
js-build-dir := $(build-dir)/libcredit.js
js-build-locales-dir := $(js-build-dir)/locales
js-dist-files = package.json libcredit.js README.md

build-javascript: $(js-locales-dir) $(LANGUAGES:%=$(js-locales-dir)/%.json)

test-javascript: build-javascript
	@$(MAKE) -C $(js-build-dir) dotest

$(js-locales-dir):
	mkdir -p $@

$(js-locales-dir)/%.json: $(po-dir)/%.po
	$(PO2JSON) $< > $@


dist-javascript: build-javascript
	rm -rf $(js-build-dir)
	mkdir -p $(js-build-dir) $(js-build-locales-dir)
	@for f in $(js-dist-files); do cp -v $(top-dir)/javascript/$$f $(js-build-dir)/$$f; done
	@for f in $(LANGUAGES:%=$(js-locales-dir)/%.json); do cp -v $$f $(js-build-locales-dir); done
	cd $(js-build-dir) && $(NPM) pack && mv libcredit.js-*.*.*.tgz $(dist-dir)
