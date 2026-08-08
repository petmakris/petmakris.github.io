# Common French phrases — build helpers.
# Override the sheet with BAND=N, e.g.  make build BAND=2
BAND ?= 1

.DEFAULT_GOAL := help
.PHONY: build all clean help

build:   ## render sheet BAND (default 1) -> out/phrases_sheet_NN.pdf
	python3 build_phrases.py --band $(BAND)

all:     ## render every sheet into one printable PDF -> out/phrases_all.pdf
	python3 build_phrases.py --all

clean:   ## remove generated PDFs
	rm -f out/*.pdf

help:    ## list targets
	@grep -E '^[a-z]+:.*##' $(MAKEFILE_LIST) | sed -E 's/:[^#]*## / - /'
