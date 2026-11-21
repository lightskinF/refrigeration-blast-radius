"""
Build the arXiv source bundle of the English paper.

    python paper/make_arxiv.py

arXiv compiles LaTeX itself and does not run BibTeX, so the bundle contains
main.tex, the compiled bibliography main.bbl, the class file and the figures,
all in one flat folder. The result is paper/arxiv-submission.zip.
"""

import re
import shutil
import subprocess
import zipfile
from pathlib import Path

PAPER = Path(__file__).resolve().parent / "en"
FIGURES = PAPER.parent.parent / "figures" / "en"
OUT_DIR = PAPER.parent / "arxiv"
OUT_ZIP = PAPER.parent / "arxiv-submission.zip"


def compile_paper():
    """pdflatex + bibtex + pdflatex x2, so that main.bbl is up to date."""
    for cmd in (["pdflatex", "-interaction=nonstopmode", "main.tex"],
                ["bibtex", "main"],
                ["pdflatex", "-interaction=nonstopmode", "main.tex"],
                ["pdflatex", "-interaction=nonstopmode", "main.tex"]):
        subprocess.run(cmd, cwd=PAPER, check=True, capture_output=True)


def main():
    compile_paper()
    tex = (PAPER / "main.tex").read_text(encoding="utf-8")
    figures = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", tex)
    # In the bundle the figures sit next to main.tex
    tex = tex.replace(r"\graphicspath{{../../figures/en/}}", r"\graphicspath{{./}}")

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir()
    (OUT_DIR / "main.tex").write_text(tex, encoding="utf-8")
    for name in ("main.bbl", "ceurart.cls"):
        shutil.copy(PAPER / name, OUT_DIR / name)
    for fig in figures:
        shutil.copy(FIGURES / fig, OUT_DIR / fig)

    with zipfile.ZipFile(OUT_ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(OUT_DIR.iterdir()):
            z.write(f, f.name)
    print(f"{OUT_ZIP} ({len(figures)} figures)")


if __name__ == "__main__":
    main()
