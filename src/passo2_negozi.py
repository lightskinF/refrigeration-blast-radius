"""
PASSO 2 - Da un banco a una catena: il "raggio d'azione" di un nodo compromesso
==============================================================================

Domanda: se un attaccante compromette UN SOLO nodo di telegestione,
quanti negozi riesce a colpire? Dipende da come e' organizzata la telegestione.

Confrontiamo tre architetture:

  A. Centralizzata   -> un solo nodo raggiunge tutti i negozi
  B. Per provincia   -> un nodo per provincia (5 nodi)
  C. Per negozio     -> ogni negozio ha il suo accesso separato

Ogni architettura e' descritta in modo semplicissimo: una lista con la
dimensione dei gruppi di negozi raggiungibili da ciascun nodo.
Esempio: [8, 5, 4, 2, 1] = cinque nodi, il primo raggiunge 8 negozi, ecc.

Il passo 1 serve a rispondere a una domanda sola: un negozio colpito perde
la merce? Si', se il banco resta sopra soglia piu' a lungo di una tolleranza.

ATTENZIONE: la catena e' IPOTETICA e i valori economici sono ILLUSTRATIVI.
Ipotesi del modello: l'attaccante compromette un solo nodo.
"""

import matplotlib.pyplot as plt

# Riuso il modello del passo 1 (deve stare nella stessa cartella)
from passo1_banco_frigo import simula, T_SOGLIA, ORE_ALL_ATTACCO, CARTELLA_FIGURE

# ---------------------------------------------------------------------------
# LA CATENA IPOTETICA: 20 negozi nelle cinque province campane
# ---------------------------------------------------------------------------
CATENA = {
    "Napoli": 8,
    "Salerno": 5,
    "Caserta": 4,
    "Avellino": 2,
    "Benevento": 1,
}
NUMERO_NEGOZI = sum(CATENA.values())

VALORE_SURGELATI_PER_NEGOZIO = 30_000   # euro, illustrativo (ordine di grandezza)
TOLLERANZA_MIN = 60                     # minuti sopra soglia (in totale) oltre i
                                        # quali la merce si considera persa: e' un
                                        # CRITERIO CONVENZIONALE dello studio, non
                                        # un limite di legge

# ---------------------------------------------------------------------------
# LE TRE ARCHITETTURE: per ogni nodo, quanti negozi raggiunge
# ---------------------------------------------------------------------------
ARCHITETTURE = {
    "A. Centralizzata": [NUMERO_NEGOZI],
    "B. Per provincia": list(CATENA.values()),
    "C. Per negozio": [1] * NUMERO_NEGOZI,
}


def minuti_sopra_soglia():
    """Minuti sopra soglia nella finestra simulata (fino alle 08:00).

    Stessa metrica del passo 3, cosi' i numeri dei due passi sono confrontabili.
    """
    tempi, temperature = simula(con_attacco=True)
    passo_min = (tempi[1] - tempi[0]) * 60
    minuti = 0.0
    for t_ore, T in zip(tempi, temperature):
        if t_ore >= ORE_ALL_ATTACCO and T > T_SOGLIA:
            minuti += passo_min
    return minuti


def analizza(gruppi, merce_persa):
    """Negozi colpiti e perdita nel caso peggiore e nel caso medio."""
    # Caso peggiore: viene compromesso il nodo che raggiunge piu' negozi
    negozi_peggiore = max(gruppi)
    # Caso medio: ogni nodo ha la stessa probabilita' di essere compromesso
    negozi_medio = sum(gruppi) / len(gruppi)

    euro_per_negozio = VALORE_SURGELATI_PER_NEGOZIO if merce_persa else 0
    return {
        "nodi": len(gruppi),
        "negozi_peggiore": negozi_peggiore,
        "negozi_medio": negozi_medio,
        "perdita_peggiore": negozi_peggiore * euro_per_negozio,
        "perdita_media": negozi_medio * euro_per_negozio,
    }


if __name__ == "__main__":
    minuti = minuti_sopra_soglia()
    merce_persa = minuti > TOLLERANZA_MIN

    print(f"Banco sopra soglia per {minuti:.0f} minuti (finestra simulata, fino alle 08:00)")
    print(f"Tolleranza: {TOLLERANZA_MIN} minuti -> merce persa: {'SI' if merce_persa else 'NO'}")
    print()
    print(f"{'Architettura':<20}{'Nodi':>6}{'Negozi (peggiore)':>20}{'Negozi (medio)':>17}"
          f"{'Perdita peggiore':>19}{'Perdita media':>16}")

    risultati = {}
    for nome, gruppi in ARCHITETTURE.items():
        r = analizza(gruppi, merce_persa)
        risultati[nome] = r
        print(f"{nome:<20}{r['nodi']:>6}{r['negozi_peggiore']:>20}{r['negozi_medio']:>17.1f}"
              f"{r['perdita_peggiore']:>17,.0f} €{r['perdita_media']:>14,.0f} €")

    # Grafico: perdita nel caso peggiore e nel caso medio, per architettura
    nomi = list(risultati.keys())
    peggiore = [risultati[n]["perdita_peggiore"] / 1000 for n in nomi]
    medio = [risultati[n]["perdita_media"] / 1000 for n in nomi]
    posizioni = range(len(nomi))
    larghezza = 0.38

    plt.figure(figsize=(8, 4.5))
    barre_p = plt.bar([p - larghezza / 2 for p in posizioni], peggiore, larghezza,
                      label="Caso peggiore", color="tab:red")
    barre_m = plt.bar([p + larghezza / 2 for p in posizioni], medio, larghezza,
                      label="Caso medio", color="tab:orange")
    plt.bar_label(barre_p, fmt="%.0f")
    plt.bar_label(barre_m, fmt="%.0f")
    plt.xticks(list(posizioni), nomi)
    plt.ylabel("Perdita stimata (migliaia di €)")
    plt.title(f"Un nodo compromesso, {NUMERO_NEGOZI} negozi: perdita per architettura")
    plt.legend()
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(CARTELLA_FIGURE / "passo2_grafico.png", dpi=150)
    print("\nGrafico salvato in figures/passo2_grafico.png")
