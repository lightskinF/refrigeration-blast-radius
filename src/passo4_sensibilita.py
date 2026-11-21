"""
PASSO 4 - Analisi di sensibilita': quanto sono robusti i risultati del passo 3?
==============================================================================

Nel passo 3 il filtro completo resta entro il criterio con 53 minuti sopra
soglia, contro una tolleranza di 60: un margine piccolo. Qui cambiamo UN
parametro alla volta e guardiamo se le conclusioni restano vere.

  A. Allarme: entro quanti minuti deve arrivare l'intervento?
  B. Filtro completo: fino a quale durata massima di sbrinamento regge?
  C. Filtro completo: quale intervallo minimo R2 serve?
  D. Inerzia termica del banco (C) dimezzata o raddoppiata: cambia qualcosa?
  E. Orario d'attacco spostato lungo un ciclo del termostato (02:00-02:25)
  F. Conduttanza termica UA (dispersione verso il negozio) da 0.5 a 1.5 volte
  G. Potenza delle resistenze di sbrinamento P_s da 0.5 a 2 volte

Per UA ci fermiamo a 1.5 volte: con UA = 40 W/°C (2 volte) il compressore
sempre acceso porterebbe il banco solo a 22 - 1600/40 = -18 °C, quindi non
raggiungerebbe mai i -19 °C a cui il termostato lo spegne. Sarebbe un banco
sottodimensionato, che non tiene il setpoint nemmeno senza attacco.

Lo script riusa le funzioni del passo 3 e ne modifica i parametri
temporaneamente. Tutti i valori restano ILLUSTRATIVI.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import passo3_difese as p3
from passo1_banco_frigo import CARTELLA_FIGURE
from passo2_negozi import TOLLERANZA_MIN

VALORI_ORIGINALI = {
    "TEMPO_INTERVENTO_MIN": p3.TEMPO_INTERVENTO_MIN,
    "DURATA_MAX_MIN": p3.DURATA_MAX_MIN,
    "INTERVALLO_MIN_ORE": p3.INTERVALLO_MIN_ORE,
    "C": p3.C,
    "ORE_ALL_ATTACCO": p3.ORE_ALL_ATTACCO,
    "UA": p3.UA,
    "P_SBRINAMENTO": p3.P_SBRINAMENTO,
}

FATTORI_UA = [0.5, 0.75, 1.0, 1.25, 1.5]
FATTORI_PS = [0.5, 0.75, 1.0, 1.5, 2.0]


def temperatura_alle_02():
    """Temperatura del banco all'inizio dell'attacco, notte normale, parametri correnti."""
    tempi, temperature, _, _ = p3.simula_notte([], False)
    indice = min(range(len(tempi)), key=lambda i: abs(tempi[i] - p3.ORE_ALL_ATTACCO))
    return temperature[indice]


def tre_difese():
    """Minuti sopra soglia per filtro completo, allarme con tecnico, protezione automatica."""
    return (prova(True, True, False)[0], prova(False, False, True)[0],
            prova(False, False, True, 0)[0])


def ripristina():
    """Rimette i parametri del passo 3 ai valori originali."""
    for nome, valore in VALORI_ORIGINALI.items():
        setattr(p3, nome, valore)


def prova(regola_durata, regola_intervallo, con_allarme, tempo_intervento_min=None):
    """Esegue uno scenario del passo 3: restituisce minuti sopra soglia e T massima."""
    comandi = p3.comandi_attaccante()  # lo script usa il limite di durata in vigore
    accettati = p3.command_guard(comandi, regola_durata, regola_intervallo)
    _, temperature, minuti, _ = p3.simula_notte(accettati, con_allarme, tempo_intervento_min)
    return minuti, max(temperature)


def esito(minuti):
    return "entro il criterio" if minuti <= TOLLERANZA_MIN else "oltre il criterio"


def sensibilita_intervento():
    """A. Minuti sopra soglia al variare del tempo tra allarme e intervento."""
    tempi = list(range(0, 65, 5))   # 0 minuti = protezione automatica
    risultati = [prova(False, False, True, t) for t in tempi]
    return tempi, risultati


def sensibilita_durata():
    """B. Minuti sopra soglia al variare della durata massima consentita (R1 + R2)."""
    durate = list(range(10, 65, 5))
    risultati = []
    for d in durate:
        p3.DURATA_MAX_MIN = d
        risultati.append(prova(True, True, False))
    ripristina()
    return durate, risultati


def sensibilita_intervallo():
    """C. Minuti sopra soglia al variare dell'intervallo minimo R2 (R1 + R2)."""
    intervalli = [1, 2, 3, 4, 4.5, 4.75, 5, 6, 8]   # comandi ogni 30 min: confine a 4,5 h
    risultati = []
    for h in intervalli:
        p3.INTERVALLO_MIN_ORE = h
        risultati.append(prova(True, True, False))
    ripristina()
    return intervalli, risultati


if __name__ == "__main__":
    print("A. Allarme: minuti tra allarme e intervento (0 = protezione automatica)")
    tempi_intervento, ris_A = sensibilita_intervento()
    for t, (m, tmax) in zip(tempi_intervento, ris_A):
        print(f"   intervento {t:>2} min -> {m:>4.0f} min sopra soglia, T max {tmax:>5.1f} °C, {esito(m)}")

    print("\nB. Filtro completo: durata massima dello sbrinamento consentita")
    durate, ris_B = sensibilita_durata()
    for d, (m, tmax) in zip(durate, ris_B):
        print(f"   durata max {d:>2} min -> {m:>4.0f} min sopra soglia, T max {tmax:>5.1f} °C, {esito(m)}")

    print("\nC. Filtro completo: intervallo minimo R2 tra due sbrinamenti")
    print("   (il personale arriva alle 07:00: da li' i comandi remoti sono ignorati)")
    intervalli, ris_C = sensibilita_intervallo()
    for h, (m, tmax) in zip(intervalli, ris_C):
        print(f"   intervallo {h} h -> {m:>4.0f} min sopra soglia, T max {tmax:>5.1f} °C, {esito(m)}")

    print("\nD. Inerzia termica del banco (C x fattore)")
    for f in [0.5, 0.75, 1.0, 1.5, 2.0]:
        p3.C = VALORI_ORIGINALI["C"] * f
        m2, _ = prova(True, True, False)
        m3, _ = prova(False, False, True)
        m4, _ = prova(False, False, True, 0)
        print(f"   C x {f:<4} -> filtro completo {m2:>4.0f} min ({esito(m2)}), "
              f"allarme con tecnico {m3:>4.0f} min ({esito(m3)}), "
              f"protezione automatica {m4:>4.0f} min ({esito(m4)})")
    ripristina()

    print("\nE. Orario d'attacco lungo un ciclo del termostato")
    for k in range(0, 30, 5):
        p3.ORE_ALL_ATTACCO = VALORI_ORIGINALI["ORE_ALL_ATTACCO"] + k / 60
        m2, _ = prova(True, True, False)
        m3, _ = prova(False, False, True)
        m4, _ = prova(False, False, True, 0)
        print(f"   attacco alle 02:{k:02d} -> filtro completo {m2:>4.0f} min, "
              f"allarme con tecnico {m3:>4.0f} min, protezione automatica {m4:>4.0f} min")
    ripristina()

    print("\nF. Conduttanza termica UA (x fattore; T0 = temperatura alle 02:00)")
    for f in FATTORI_UA:
        p3.UA = VALORI_ORIGINALI["UA"] * f
        m2, m3, m4 = tre_difese()
        print(f"   UA x {f:<4} (T0 {temperatura_alle_02():6.2f} °C) -> filtro completo {m2:>4.0f} min ({esito(m2)}), "
              f"allarme con tecnico {m3:>4.0f} min ({esito(m3)}), "
              f"protezione automatica {m4:>4.0f} min ({esito(m4)})")
    ripristina()

    print("\nG. Potenza di sbrinamento P_s (x fattore; T0 = temperatura alle 02:00)")
    for f in FATTORI_PS:
        p3.P_SBRINAMENTO = VALORI_ORIGINALI["P_SBRINAMENTO"] * f
        m2, m3, m4 = tre_difese()
        print(f"   P_s x {f:<4} (T0 {temperatura_alle_02():6.2f} °C) -> filtro completo {m2:>4.0f} min ({esito(m2)}), "
              f"allarme con tecnico {m3:>4.0f} min ({esito(m3)}), "
              f"protezione automatica {m4:>4.0f} min ({esito(m4)})")
    ripristina()

    # Grafico: tempo di intervento, durata massima, intervallo minimo
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(14, 4))
    pannelli = [
        (ax1, tempi_intervento, ris_A, "tab:orange",
         "Minuti tra allarme e intervento", "A. Allarme indipendente"),
        (ax2, durate, ris_B, "tab:green",
         "Durata massima di sbrinamento consentita (min)", "B. Filtro completo: durata"),
        (ax3, intervalli, ris_C, "tab:blue",
         "Intervallo minimo R2 (ore)", "C. Filtro completo: intervallo"),
    ]
    for ax, x, ris, colore, etichetta, titolo in pannelli:
        ax.plot(x, [m for m, _ in ris], marker="o", color=colore)
        ax.axhline(TOLLERANZA_MIN, color="gray", linestyle="--", label=f"Tolleranza {TOLLERANZA_MIN} min")
        ax.set_xlabel(etichetta)
        ax.set_ylabel("Minuti sopra soglia")
        ax.set_title(titolo)
        ax.legend()
        ax.grid(alpha=0.3)

    fig.tight_layout()
    fig.savefig(CARTELLA_FIGURE / "passo4_grafico.png", dpi=150)
    print("\nGrafico salvato in figures/passo4_grafico.png")
