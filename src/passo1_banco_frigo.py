"""
PASSO 1 - Modello termico di UN SOLO banco surgelati
=====================================================

Idea: il banco e' come una "scatola" con una sola temperatura T, la
temperatura media del banco CON IL SUO CONTENUTO (struttura, aria e prodotti
trattati come un unico blocco: modello "a parametri concentrati").
Tre cose la fanno cambiare:

  1. il calore che entra dal negozio (piu' il banco e' freddo, piu' ne entra)
  2. il compressore, che toglie calore quando e' acceso
  3. le resistenze di sbrinamento, che aggiungono calore quando sono accese

In formula (bilancio di energia):

    C * dT/dt = UA * (T_ambiente - T)  -  P_freddo  +  P_sbrinamento

In condizioni normali un termostato accende e spegne il compressore per
restare vicino al setpoint. Nell'attacco qualcuno forza lo sbrinamento:
compressore spento, resistenze accese, e nessuno se ne accorge fino a quando
arriva il personale (07:00), che rimette il banco in funzionamento locale.

ATTENZIONE: i parametri qui sotto sono ILLUSTRATIVI, scelti per ottenere un
comportamento plausibile. Non sono misure di un banco reale: nel report vanno
dichiarati come ipotesi, oppure calibrati su schede tecniche / letteratura.
Il modello ignora il calore latente di fusione: vale finche' T resta sotto 0 °C.
"""

import matplotlib
matplotlib.use("Agg")  # salva il grafico su file, senza aprire finestre
import matplotlib.pyplot as plt
from pathlib import Path

# Le figure vengono salvate nella cartella figures/ del repository
CARTELLA_FIGURE = Path(__file__).resolve().parent.parent / "figures"
CARTELLA_FIGURE.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# PARAMETRI (illustrativi)
# ---------------------------------------------------------------------------
T_AMBIENTE = 22.0       # °C  temperatura del negozio
SETPOINT = -18.0        # °C  temperatura desiderata nel banco
ISTERESI = 1.0          # °C  il termostato lavora tra setpoint-1 e setpoint+1
T_SOGLIA = -15.0        # °C  -18 °C + 3 °C: tolleranza massima ammessa nei banchi
                        #     di vendita (direttiva 89/108/CEE, art. 5;
                        #     D.Lgs. 110/1992, art. 4)

UA = 20.0               # W/°C  quanto calore entra per ogni grado di differenza
C = 300_000.0           # J/°C  "inerzia termica" del banco con il suo contenuto:
                        #       per esempio 120 kg di surgelati x 2000 J/(kg K)
                        #       = 240 000 J/°C, piu' circa 60 000 J/°C di
                        #       struttura (la sola aria varrebbe circa 600 J/°C)
P_FREDDO = 1600.0       # W     calore tolto dal compressore quando e' acceso
P_SBRINAMENTO = 600.0   # W     calore aggiunto dalle resistenze di sbrinamento

# ---------------------------------------------------------------------------
# SCENARIO: una notte, dalle 20:00 alle 08:00
# ---------------------------------------------------------------------------
ORA_INIZIO = 20.0       # la simulazione parte alle 20:00
DURATA_ORE = 12.0       # e dura 12 ore (fino alle 08:00)
ORE_ALL_ATTACCO = 6.0   # l'attacco parte 6 ore dopo l'inizio, cioe' alle 02:00
ORE_ALL_ARRIVO = 11.0   # il personale arriva 11 ore dopo l'inizio, alle 07:00
DT = 10.0               # s   passo di simulazione


def simula(con_attacco):
    """Simula la notte e restituisce due liste: tempi (in ore) e temperature."""
    numero_passi = int(DURATA_ORE * 3600 / DT)
    T = SETPOINT
    compressore_acceso = False
    tempi, temperature = [], []

    for passo in range(numero_passi + 1):
        t_ore = passo * DT / 3600
        tempi.append(t_ore)
        temperature.append(T)

        # L'attacco dura dalle 02:00 all'arrivo del personale (07:00), che
        # rimette il banco in funzionamento locale (come nel passo 3)
        sotto_attacco = con_attacco and ORE_ALL_ATTACCO <= t_ore < ORE_ALL_ARRIVO

        if sotto_attacco:
            # Sbrinamento forzato: niente freddo, resistenze sempre accese
            compressore_acceso = False
            resistenze_accese = True
        else:
            # Funzionamento normale: termostato con isteresi
            resistenze_accese = False
            if T > SETPOINT + ISTERESI:
                compressore_acceso = True
            elif T < SETPOINT - ISTERESI:
                compressore_acceso = False

        # Bilancio di energia: quanta potenza netta entra nel banco (in W)
        potenza_netta = UA * (T_AMBIENTE - T)
        if compressore_acceso:
            potenza_netta -= P_FREDDO
        if resistenze_accese:
            potenza_netta += P_SBRINAMENTO

        # Aggiorno la temperatura: dT = potenza / inerzia * tempo
        T += potenza_netta / C * DT

    return tempi, temperature


def minuti_al_superamento_soglia(tempi, temperature):
    """Minuti trascorsi dall'attacco al primo superamento della soglia."""
    for t_ore, T in zip(tempi, temperature):
        if t_ore >= ORE_ALL_ATTACCO and T > T_SOGLIA:
            return (t_ore - ORE_ALL_ATTACCO) * 60
    return None


def temperatura_a(tempi, temperature, ore):
    """Temperatura nell'istante piu' vicino a 'ore' dall'inizio."""
    indice = min(range(len(tempi)), key=lambda i: abs(tempi[i] - ore))
    return temperature[indice]


if __name__ == "__main__":
    tempi, T_normale = simula(con_attacco=False)
    _, T_attacco = simula(con_attacco=True)

    minuti = minuti_al_superamento_soglia(tempi, T_attacco)
    T_arrivo = temperatura_a(tempi, T_attacco, ORE_ALL_ARRIVO)
    T_equilibrio = T_AMBIENTE + P_SBRINAMENTO / UA

    print("RISULTATI (parametri illustrativi)")
    print(f"- Soglia di {T_SOGLIA:.0f} °C superata dopo {minuti:.0f} minuti dall'attacco")
    print(f"- Temperatura all'arrivo del personale (07:00): {T_arrivo:.1f} °C")
    print(f"- Temperatura alle 08:00, dopo un'ora di funzionamento locale: {T_attacco[-1]:.1f} °C")
    print(f"- Temperatura a cui tenderebbe il banco se nessuno intervenisse: {T_equilibrio:.0f} °C")

    # Grafico
    plt.figure(figsize=(9, 4.5))
    plt.plot(tempi, T_normale, label="Funzionamento normale", color="tab:blue")
    plt.plot(tempi, T_attacco, label="Sbrinamento forzato (attacco)", color="tab:red")
    plt.axhline(T_SOGLIA, color="gray", linestyle="--", label=f"Soglia {T_SOGLIA:.0f} °C")
    plt.axvline(ORE_ALL_ATTACCO, color="black", linestyle=":", label="Inizio attacco (02:00)")
    plt.axvline(ORE_ALL_ARRIVO, color="green", linestyle=":", label="Arrivo personale (07:00)")

    tacche = range(0, int(DURATA_ORE) + 1, 2)
    etichette = [f"{int((ORA_INIZIO + h) % 24):02d}:00" for h in tacche]
    plt.xticks(list(tacche), etichette)
    plt.xlabel("Ora")
    plt.ylabel("Temperatura nel banco (°C)")
    plt.title("Un banco surgelati: notte normale e notte con sbrinamento forzato")
    plt.legend(loc="upper left", fontsize=8)
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(CARTELLA_FIGURE / "passo1_grafico.png", dpi=150)
    print("Grafico salvato in figures/passo1_grafico.png")
