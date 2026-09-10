# Cartes du Soir — χάρτινο παιχνίδι γαλλικών, με σελίδα προφοράς.
# Διαβάζει επιτόπου τον κατάλογο συχνότητας του frequence, δεν αντιγράφει τίποτα.
.DEFAULT_GOAL := aide
.PHONY: aide lexique check cartes audio web tout propre

aide:      ## οι στόχοι
	@grep -E '^[a-z]+:.*##' $(MAKEFILE_LIST) | sed -E 's/:[^#]*## / — /'

lexique:   ## data/lexique.json από το ../fr_50k.txt
	python3 bin/build_lexicon.py

check:     ## το φράγμα A1 — τρέχει πριν από κάθε cartes
	python3 bin/check_scenes.py

cartes: check  ## out/cartes/*.pdf, τρεις σελίδες ανά σκηνή
	python3 bin/build_cards.py

audio:     ## web/audio/*.m4a, μία ηχογράφηση ανά μοναδική ατάκα
	python3 bin/build_audio.py

web: audio ## ../../cartes/index.html — η ενότητα του blog
	python3 bin/build_web.py

pack: cartes ## ../../cartes/cartes-du-soir.pdf — όλες οι κάρτες σε ένα τυπώσιμο
	python3 bin/build_pack.py

autonome:  ## out/autonome.html — ένα αρχείο με τον ήχο μέσα, για δοκιμή με link
	python3 bin/build_web.py --embarque

gemini:    ## ξαναηχογράφησε τα πάντα με τις φωνές του Gemini
	TTS=gemini python3 bin/build_audio.py --refaire
	python3 bin/build_web.py
	python3 bin/build_web.py --embarque

servir:    ## σέρβιρε την ενότητα στο 8791 για δοκιμή από κινητό
	@echo "http://$$(ipconfig getifaddr en0 2>/dev/null || hostname):8791/"
	python3 -m http.server 8791 --directory ../../cartes

tout: lexique check cartes pack web  ## όλα

propre:    ## σβήσε τα PDF
	rm -f out/cartes/*.pdf
