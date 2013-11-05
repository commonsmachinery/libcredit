
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

js-build-dir := $(build-dir)/libcredit.js
js-build-locales-dir := $(js-build-dir)/locales
js-build-test-dir := $(js-build-dir)/test
js-dist-files = package.json libcredit.js Makefile test/common.js test/tests.js

build-javascript: $(js-build-locales-dir) $(js-build-test-dir) $(LANGUAGES:%=$(js-build-locales-dir)/%.json)
	@for f in $(js-dist-files); do cp -v javascript/$$f $(js-build-dir)/$$f; done

$(js-build-locales-dir) $(js-build-test-dir):
	mkdir -p $@

$(js-build-locales-dir)/%.json: $(po-dir)/%.po
	$(PO2JSON) $< > $@


dist-javascript: build-javascript 
	cd $(js-build-dir) && $(NPM) pack && mv libcredit.js-*.*.*.tgz $(dist-dir)
