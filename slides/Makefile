# Author: Huihuo Zheng, huihuo.zheng@anl.gov
# Copyright: Trinity Science 2026
#
# Slide decks for the "Hands-On: Agentic AI for AmSC" tutorial.
#
#   make              build the hands-on deck (the workshop deck)
#   make handson      same
#   make view         build and open it
#   make clean        remove LaTeX build artifacts (keeps the PDFs)
#
# Needs xelatex (fontspec). No -shell-escape and no Pygments: code is set with
# `listings`, not minted, so a plain TeX Live install is enough.
#
# NOTE: amsc_agentic_ai.tex (the senior-manager overview deck) is intentionally
# NOT a default target. It references images that are not in this repository
# (aurora.jpg, perlmutter.png, frontier.png, trinity-app-screenshot.png,
# logos/argonne_logo.pdf) and a \graphicspath outside it, so it cannot be built
# from a clean clone. Build it with `make overview` only if you have supplied
# those assets yourself.

HANDSON := amsc_agentic_ai_handson
OVERVIEW := amsc_agentic_ai
XELATEX := xelatex -interaction=nonstopmode -halt-on-error

# Rebuild when the logo changes too. Via $(wildcard ...) rather than a literal
# prerequisite: \decklogo guards the logo with \IfFileExists and falls back to a
# text lockup, so the deck must still build when the asset is absent. A literal
# prerequisite would turn that graceful fallback into a "No rule to make target".
LOGO := $(wildcard logos/*.pdf)

.PHONY: all handson overview view clean

all: handson

handson: $(HANDSON).pdf

$(HANDSON).pdf: $(HANDSON).tex $(LOGO)
	$(XELATEX) $(HANDSON).tex
	$(XELATEX) $(HANDSON).tex

overview:
	$(XELATEX) $(OVERVIEW).tex
	$(XELATEX) $(OVERVIEW).tex

view: handson
	xdg-open $(HANDSON).pdf >/dev/null 2>&1 &

clean:
	rm -f *.aux *.log *.nav *.out *.snm *.toc *.vrb *.fls *.fdb_latexmk
