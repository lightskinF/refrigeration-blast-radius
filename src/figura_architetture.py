"""
Figura delle tre architetture di telegestione (per il report)
=============================================================

Disegna nodi (quadrati, in alto) e negozi (cerchi, in basso, colorati per
provincia). In rosso il nodo compromesso nel caso peggiore e i negozi che
raggiunge: e' il "raggio d'azione".
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from passo1_banco_frigo import CARTELLA_FIGURE
from passo2_negozi import CATENA, NUMERO_NEGOZI, ARCHITETTURE

COLORI_PROVINCE = {
    "Napoli": "tab:blue",
    "Salerno": "tab:green",
    "Caserta": "tab:purple",
    "Avellino": "tab:olive",
    "Benevento": "tab:brown",
}
# Provincia di ogni negozio, nell'ordine in cui sono disegnati
PROVINCIA_NEGOZIO = [p for p, n in CATENA.items() for _ in range(n)]

fig, assi = plt.subplots(1, 3, figsize=(13, 4))

for ax, (nome, gruppi) in zip(assi, ARCHITETTURE.items()):
    indice_peggiore = gruppi.index(max(gruppi))  # il nodo che raggiunge piu' negozi
    dimensione_nodo = 140 if len(gruppi) <= 5 else 35
    colpiti = set()
    inizio = 0
    for i, g in enumerate(gruppi):
        membri = list(range(inizio, inizio + g))
        x_nodo = sum(membri) / g
        compromesso = i == indice_peggiore
        for m in membri:
            ax.plot([x_nodo, m], [1, 0], color="tab:red" if compromesso else "lightgray",
                    linewidth=1.2 if compromesso else 0.8, zorder=1)
            if compromesso:
                colpiti.add(m)
        ax.scatter([x_nodo], [1], marker="s", s=dimensione_nodo,
                   color="tab:red" if compromesso else "dimgray", zorder=3)
        inizio += g

    for m in range(NUMERO_NEGOZI):
        ax.scatter([m], [0], s=45, color=COLORI_PROVINCE[PROVINCIA_NEGOZIO[m]], zorder=3,
                   edgecolors="tab:red" if m in colpiti else "white", linewidths=1.8)

    nodi = f"{len(gruppi)} nodo" if len(gruppi) == 1 else f"{len(gruppi)} nodi"
    negozi = f"{max(gruppi)} negozio colpito" if max(gruppi) == 1 else f"{max(gruppi)} negozi colpiti"
    ax.set_title(f"{nome}\n{nodi}, caso peggiore: {negozi}", fontsize=10)
    ax.text(-1.2, 1, "nodi", ha="right", va="center", fontsize=8, color="dimgray")
    ax.text(-1.2, 0, "negozi", ha="right", va="center", fontsize=8, color="dimgray")
    ax.set_xlim(-4, NUMERO_NEGOZI)
    ax.set_ylim(-0.3, 1.3)
    ax.axis("off")

legenda = [Line2D([0], [0], marker="o", linestyle="", color=c, label=p) for p, c in COLORI_PROVINCE.items()]
legenda.append(Line2D([0], [0], marker="s", linestyle="", color="tab:red",
                      label="Nodo compromesso e negozi raggiunti"))
fig.legend(handles=legenda, loc="lower center", ncol=6, fontsize=8, frameon=False)
fig.tight_layout(rect=(0, 0.08, 1, 1))
fig.savefig(CARTELLA_FIGURE / "figura_architetture.png", dpi=150)
print("Figura salvata in figures/figura_architetture.png")
