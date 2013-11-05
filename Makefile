
#
# Build settings
#

# Programming language implementations to build, dist etc
IMPL = python 

# Translations (human languages)
LANGUAGES = sv


#
# Tools etc
#

PYTHON = python


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

.PHONY: all dist 

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

