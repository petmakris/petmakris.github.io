# Transaction playground — build helpers.
.DEFAULT_GOAL := help
.PHONY: build test serve help

build:   ## bake src/ + index.template.html -> index.html
	python3 build.py

test:    ## run the engine, renderer and scenario tests
	node --test tests/

serve:   ## serve this folder locally on :8090
	python3 -m http.server 8090

help:    ## list targets
	@grep -E '^[a-z]+:.*##' $(MAKEFILE_LIST) | sed -E 's/:[^#]*## / - /'
