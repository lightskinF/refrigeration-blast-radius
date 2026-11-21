"""
Run every simulation in order and save what each script prints.

    python run_all.py

Figures go to figures/, printed results to results/. The numbers in results/
are the ones reported in the paper: after a run, `git diff results/` shows
whether anything changed.
"""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPTS = [
    "passo1_banco_frigo.py",     # one freezer cabinet under attack (Figure 2)
    "passo2_negozi.py",          # blast radius of three architectures (Table 4, Figure 3)
    "passo3_difese.py",          # in-store defences vs an adaptive attacker (Table 5, Figure 4)
    "passo4_sensibilita.py",     # sensitivity analysis (Table 6, Figure 5)
    "figura_architetture.py",    # architecture diagram (Figure 1)
    "passo5_forma_chiusa.py",    # state-space model, closed form, break-even (Table 7)
    "figures_en.py",             # English versions of all figures (paper, README)
]


def main():
    results = ROOT / "results"
    results.mkdir(exist_ok=True)
    env = {**os.environ, "MPLBACKEND": "Agg"}  # no display needed

    for script in SCRIPTS:
        print(f"== {script}")
        run = subprocess.run(
            [sys.executable, str(ROOT / "src" / script)],
            capture_output=True, text=True, env=env, cwd=ROOT,
        )
        if run.returncode != 0:
            print(run.stderr)
            sys.exit(f"{script} failed")
        print(run.stdout)
        (results / script.replace(".py", ".txt")).write_text(run.stdout, encoding="utf-8")

    print("Done: figures in figures/, outputs in results/")


if __name__ == "__main__":
    main()
