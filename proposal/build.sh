#!/usr/bin/env bash
# Compile the proposal. Needs pdflatex + bibtex (TeX Live). acl.sty / acl_natbib.bst are in this folder.
set -e
cd "$(dirname "$0")"
pdflatex -interaction=nonstopmode -halt-on-error proposal.tex
bibtex proposal
pdflatex -interaction=nonstopmode proposal.tex
pdflatex -interaction=nonstopmode proposal.tex
pdfinfo proposal.pdf 2>/dev/null | grep Pages || true
