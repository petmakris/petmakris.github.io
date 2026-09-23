# Vocabulaire illustré — build the textbook.
.DEFAULT_GOAL := help
.PHONY: livre check clean publish help

livre:   ## build out/livre.html and out/livre.pdf
	python3 build.py

check:   ## run the test suite
	python3 -m pytest tests -q

clean:   ## remove generated output
	rm -rf out

publish: livre  ## copy the HTML to the site root for GitHub Pages
	mkdir -p ../../livre
	cp out/livre.html ../../livre/index.html
	@echo "published -> blog/livre/index.html"

help:    ## list targets
	@grep -E '^[a-z]+:.*##' $(MAKEFILE_LIST) | sed -E 's/:[^#]*## / - /'
