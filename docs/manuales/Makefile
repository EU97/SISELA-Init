# Manuales de práctica SISELA — compilación LaTeX
#
#   make          -> compila todos los pN.tex a build/pN.pdf
#   make p4       -> compila solo p4
#   make clean    -> borra los archivos auxiliares
#   make distclean-> borra también los PDF
#
# Requiere una distribución TeX con: libertinus, helvet, babel-spanish,
# siunitx, booktabs, tikz, pgfplots, listings, fancyhdr, titlesec, enumitem,
# microtype, hyperref  (TeX Live completo o MiKTeX con instalación bajo demanda).

TEX      := pdflatex
TEXFLAGS := -interaction=nonstopmode -halt-on-error -output-directory=build
# pN.tex de práctica (excluye preamble.tex, que es una inclusión, no un documento)
SOURCES  := $(filter-out preamble.tex,$(wildcard p*.tex))
PDFS     := $(patsubst %.tex,build/%.pdf,$(SOURCES))

.PHONY: all clean distclean $(basename $(SOURCES))

all: $(PDFS)

# objetivo corto:  make p4
$(basename $(SOURCES)): %: build/%.pdf

build/%.pdf: %.tex preamble.tex | build
	$(TEX) $(TEXFLAGS) $< > build/$*.log 2>&1 || (tail -n 20 build/$*.log; exit 1)
	$(TEX) $(TEXFLAGS) $< > build/$*.log 2>&1   # segunda pasada: TOC + pageref
	@echo "  -> $@ ($$(pdfinfo $@ | awk '/^Pages/{print $$2}') páginas)"

build:
	mkdir -p build

clean:
	rm -f build/*.aux build/*.log build/*.toc build/*.out build/*.lof build/*.lot

distclean: clean
	rm -f build/*.pdf
