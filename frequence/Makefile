# Fréquence — build helpers (web game + French PDF reference).
# Override the PDF band with BAND=N, e.g.  make build BAND=2
BAND ?= 1

.DEFAULT_GOAL := help
.PHONY: game build slice clean help

game:    ## bake the web game -> ../index.html (the GitHub Pages root)
	python3 build_game.py

build:   ## render French PDF sheet BAND (default 1) -> out/french_XXXX-YYYY.pdf
	python3 build_pdf.py --band $(BAND)

slice:   ## write data/bandNN_words.txt for sheet BAND's data passes
	python3 slice_band.py $(BAND)

clean:   ## remove generated PDFs
	rm -f out/*.pdf

help:    ## list targets
	@grep -E '^[a-z]+:.*##' $(MAKEFILE_LIST) | sed -E 's/:[^#]*## / - /'
