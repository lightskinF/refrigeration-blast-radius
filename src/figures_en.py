"""
English versions of the five figures, for the paper and the README
==================================================================

The step-by-step scripts (passo1 ... passo4, figura_architetture) keep their
Italian labels because they were written as a learning path. This script
reuses their simulation functions and redraws the same figures with English
labels into figures/en/. It computes nothing new.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

import passo1_banco_frigo as p1
import passo2_negozi as p2
import passo3_difese as p3
import passo4_sensibilita as p4

OUT = p1.CARTELLA_FIGURE / "en"
OUT.mkdir(exist_ok=True)

ARCH_EN = {
    "A. Centralizzata": "A. Centralised",
    "B. Per provincia": "B. One node per province",
    "C. Per negozio": "C. One node per store",
}
PROVINCE_EN = {"Napoli": "Naples", "Salerno": "Salerno", "Caserta": "Caserta",
               "Avellino": "Avellino", "Benevento": "Benevento"}


def hour_ticks(ax):
    ticks = range(0, int(p1.DURATA_ORE) + 1, 2)
    ax.set_xticks(list(ticks))
    ax.set_xticklabels([f"{int((p1.ORA_INIZIO + h) % 24):02d}:00" for h in ticks])
    ax.set_xlabel("Time")


def figure_architectures():
    colours = {"Napoli": "tab:blue", "Salerno": "tab:green", "Caserta": "tab:purple",
               "Avellino": "tab:olive", "Benevento": "tab:brown"}
    province_of = [p for p, n in p2.CATENA.items() for _ in range(n)]
    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    for ax, (name, groups) in zip(axes, p2.ARCHITETTURE.items()):
        worst = groups.index(max(groups))
        node_size = 140 if len(groups) <= 5 else 35
        hit, start = set(), 0
        for i, g in enumerate(groups):
            members = list(range(start, start + g))
            x_node = sum(members) / g
            compromised = i == worst
            for m in members:
                ax.plot([x_node, m], [1, 0], color="tab:red" if compromised else "lightgray",
                        linewidth=1.2 if compromised else 0.8, zorder=1)
                if compromised:
                    hit.add(m)
            ax.scatter([x_node], [1], marker="s", s=node_size,
                       color="tab:red" if compromised else "dimgray", zorder=3)
            start += g
        for m in range(p2.NUMERO_NEGOZI):
            ax.scatter([m], [0], s=45, color=colours[province_of[m]], zorder=3,
                       edgecolors="tab:red" if m in hit else "white", linewidths=1.8)
        nodes = "1 node" if len(groups) == 1 else f"{len(groups)} nodes"
        stores = "1 store hit" if max(groups) == 1 else f"{max(groups)} stores hit"
        ax.set_title(f"{ARCH_EN[name]}\n{nodes}, worst case: {stores}", fontsize=10)
        ax.text(-1.2, 1, "nodes", ha="right", va="center", fontsize=8, color="dimgray")
        ax.text(-1.2, 0, "stores", ha="right", va="center", fontsize=8, color="dimgray")
        ax.set_xlim(-4, p2.NUMERO_NEGOZI)
        ax.set_ylim(-0.3, 1.3)
        ax.axis("off")
    legend = [Line2D([0], [0], marker="o", linestyle="", color=c, label=PROVINCE_EN[p])
              for p, c in colours.items()]
    legend.append(Line2D([0], [0], marker="s", linestyle="", color="tab:red",
                         label="Compromised node and stores reached"))
    fig.legend(handles=legend, loc="lower center", ncol=6, fontsize=8, frameon=False)
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    fig.savefig(OUT / "architectures.png", dpi=150)
    plt.close(fig)


def figure_cabinet():
    t, normal = p1.simula(con_attacco=False)
    _, attack = p1.simula(con_attacco=True)
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(t, normal, label="Normal operation", color="tab:blue")
    ax.plot(t, attack, label="Forced defrost (attack)", color="tab:red")
    ax.axhline(p1.T_SOGLIA, color="gray", linestyle="--", label=f"Threshold {p1.T_SOGLIA:.0f} °C")
    ax.axvline(p1.ORE_ALL_ATTACCO, color="black", linestyle=":", label="Attack starts (02:00)")
    ax.axvline(p1.ORE_ALL_ARRIVO, color="green", linestyle=":", label="Staff arrive (07:00)")
    hour_ticks(ax)
    ax.set_ylabel("Cabinet temperature (°C)")
    ax.set_title("One freezer cabinet: normal night and forced defrost")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT / "cabinet.png", dpi=150)
    plt.close(fig)


def figure_loss():
    lost = p2.minuti_sopra_soglia() > p2.TOLLERANZA_MIN
    names = list(p2.ARCHITETTURE)
    res = [p2.analizza(p2.ARCHITETTURE[n], lost) for n in names]
    worst = [r["perdita_peggiore"] / 1000 for r in res]
    avg = [r["perdita_media"] / 1000 for r in res]
    x = range(len(names))
    w = 0.38
    fig, ax = plt.subplots(figsize=(8, 4.5))
    b1 = ax.bar([i - w / 2 for i in x], worst, w, label="Worst case", color="tab:red")
    b2 = ax.bar([i + w / 2 for i in x], avg, w, label="Average case", color="tab:orange")
    ax.bar_label(b1, fmt="%.0f")
    ax.bar_label(b2, fmt="%.0f")
    ax.set_xticks(list(x))
    ax.set_xticklabels([ARCH_EN[n] for n in names])
    ax.set_ylabel("Estimated loss (thousand €)")
    ax.set_title(f"One compromised node, {p2.NUMERO_NEGOZI} stores: loss by architecture")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT / "loss.png", dpi=150)
    plt.close(fig)


def figure_defences():
    labels = {
        "0. Nessuna difesa": "0. No defence",
        "1. Filtro: solo durata max": "1. Filter: max duration only (R1)",
        "2. Filtro: durata + intervallo": "2. Filter: duration + interval (R1 + R2)",
        "3. Solo allarme (tecnico)": "3. Alarm, technician responds",
        "4. Protezione automatica": "4. Automatic protection",
    }
    assert set(labels) == set(p3.SCENARI), "scenario names changed in passo3"
    fig, ax = plt.subplots(figsize=(9, 4.8))
    for name in p3.SCENARI:
        t, temps, _, _ = p3.esegui_scenario(name)
        colour, style = p3.STILI[name]
        ax.plot(t, temps, color=colour, linestyle=style, label=labels[name])
    ax.axhline(p1.T_SOGLIA, color="gray", linestyle=":", label=f"Threshold {p1.T_SOGLIA:.0f} °C")
    hour_ticks(ax)
    ax.set_ylabel("Cabinet temperature (°C)")
    ax.set_title("Same attack, different defences")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT / "defences.png", dpi=150)
    plt.close(fig)


def figure_sensitivity():
    response_times, res_a = p4.sensibilita_intervento()
    durations, res_b = p4.sensibilita_durata()
    intervals, res_c = p4.sensibilita_intervallo()

    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    tol = p2.TOLLERANZA_MIN
    panels = [
        (response_times, res_a, "tab:orange", "Minutes from alarm to response",
         "A. Independent alarm"),
        (durations, res_b, "tab:green", "Maximum allowed defrost duration (min)",
         "B. Full filter: duration (R1)"),
        (intervals, res_c, "tab:blue", "Minimum interval R2 (hours)",
         "C. Full filter: interval (R2)"),
    ]
    for ax, (x, res, colour, xlabel, title) in zip(axes, panels):
        ax.plot(x, [m for m, _ in res], marker="o", color=colour)
        ax.axhline(tol, color="gray", linestyle="--", label=f"Tolerance {tol} min")
        ax.set_xlabel(xlabel)
        ax.set_ylabel("Minutes above threshold")
        ax.set_title(title)
        ax.legend()
        ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT / "sensitivity.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    figure_architectures()
    figure_cabinet()
    figure_loss()
    figure_defences()
    figure_sensitivity()
    print("English figures saved in figures/en/")
