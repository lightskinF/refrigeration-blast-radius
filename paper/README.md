# Paper

- `en/` — English version, one-column layout based on the CEUR-WS class (`ceurart`).
  - `main.tex`, `references.bib`: sources
  - `main.pdf`: compiled paper
  - `ceurart.cls`: template class from <https://github.com/yamadharma/ceurart> (LPPL 1.3c)
- The Italian version is kept as an editable document outside this repository.

The figures are not duplicated here: `main.tex` reads them from `../../figures/en/`,
so re-running `python run_all.py` updates the paper too.

## Build

```bash
cd paper/en
latexmk -pdf main.tex
```

To build the arXiv source bundle (flat folder with `main.tex`, `main.bbl`, class and figures):

```bash
python paper/make_arxiv.py      # writes paper/arxiv-submission.zip
```

Requires a TeX Live installation with the `libertinus`, `fontawesome5` and
`ccicons` packages (all in `texlive-fonts-extra` on Debian/Ubuntu). Overleaf
works out of the box: upload `paper/en/` plus the five PNG files from `figures/en/`
and change `\graphicspath` in `main.tex` to `{./}`.

## License

The paper text and figures are released under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The code in `src/`
is under the MIT license (see `../LICENSE`).
