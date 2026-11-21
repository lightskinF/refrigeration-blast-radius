"""
PASSO 3 - Le difese: filtro dei comandi, allarme e protezione automatica
========================================================================

Nel passo 2 abbiamo visto che un nodo compromesso puo' colpire molti negozi.
Qui ci chiediamo: se il nodo e' compromesso, cosa limita comunque il danno?

Le difese stanno tutte DENTRO IL NEGOZIO (a valle del nodo compromesso,
altrimenti l'attaccante le aggira):

  1. FILTRO DEI COMANDI: controlla ogni comando di sbrinamento prima che
     arrivi al banco. Due regole:
       R1 - durata massima dello sbrinamento
       R2 - intervallo minimo tra gli INIZI di due sbrinamenti accettati
  2. ALLARME INDIPENDENTE: un sensore separato dal sistema di controllo.
     Se la temperatura resta sopra soglia per alcuni minuti avvisa un tecnico,
     che arriva e rimette il banco in funzionamento locale.
  3. PROTEZIONE AUTOMATICA: lo stesso sensore, ma senza attendere il tecnico:
     quando scatta, il dispositivo stesso blocca lo sbrinamento (intervento
     dopo 0 minuti).

L'attaccante usa uno SCRIPT FISSO e conosce il limite di durata che un filtro
potrebbe imporre. Non sa quali comandi vengono accettati, quindi li invia
tutti: alle 02:00 uno sbrinamento di 600 minuti e, sempre a partire dalle
02:00 e poi ogni 30 minuti fino alle 07:30, lo sbrinamento piu' lungo
consentito (30 minuti): 1 + 12 = 13 comandi. Se piu' comandi si
sovrappongono non hanno effetto in piu': per questo la tabella riporta i
MINUTI DI SBRINAMENTO DAVVERO ESEGUITI, non il numero di comandi.

Senza allarme, alle 07:00 arriva il personale e rimette il banco in
funzionamento locale: da quel momento i comandi remoti sono ignorati, e anche
uno sbrinamento remoto gia' in corso viene interrotto (il controllo torna al
termostato). Il
passaggio al funzionamento locale delle 07:00 ha la precedenza su un comando
che arriva nello stesso istante (per esempio con R2 = 5 ore).

ATTENZIONE: tutti i parametri sono ILLUSTRATIVI (vedi passo 1 e passo 2).
"""

import matplotlib.pyplot as plt

# Riuso parametri e ipotesi dei passi precedenti (stessa cartella)
from passo1_banco_frigo import (
    T_AMBIENTE, SETPOINT, ISTERESI, T_SOGLIA, UA, C, P_FREDDO, P_SBRINAMENTO,
    ORA_INIZIO, DURATA_ORE, ORE_ALL_ATTACCO, ORE_ALL_ARRIVO, DT, CARTELLA_FIGURE,
)
from passo2_negozi import NUMERO_NEGOZI, VALORE_SURGELATI_PER_NEGOZIO, TOLLERANZA_MIN

# ---------------------------------------------------------------------------
# PARAMETRI DELLE DIFESE (illustrativi)
# ---------------------------------------------------------------------------
DURATA_MAX_MIN = 30          # R1: uno sbrinamento non puo' durare piu' di 30 minuti
INTERVALLO_MIN_ORE = 6       # R2: almeno 6 ore tra uno sbrinamento e il successivo

RITARDO_ALLARME_MIN = 10     # l'allarme scatta dopo 10 minuti consecutivi sopra soglia
TEMPO_INTERVENTO_MIN = 60    # il tecnico arriva 60 minuti dopo l'allarme


def comandi_attaccante():
    """I comandi inviati dallo script dell'attaccante: lista di (ora, durata in minuti)."""
    comandi = [(ORE_ALL_ATTACCO, 600)]            # uno sbrinamento di 10 ore
    ora = ORE_ALL_ATTACCO
    while ora < DURATA_ORE:                       # poi, ogni 30 minuti, il comando
        comandi.append((ora, DURATA_MAX_MIN))     # piu' lungo consentito
        ora += DURATA_MAX_MIN / 60
    return comandi


def command_guard(comandi, regola_durata, regola_intervallo):
    """Il filtro dei comandi: restituisce solo quelli accettati."""
    accettati = []
    ora_ultimo_accettato = None
    for ora, durata in comandi:
        # R1: durata massima
        if regola_durata and durata > DURATA_MAX_MIN:
            continue
        # R2: intervallo minimo dall'ultimo sbrinamento accettato
        if (regola_intervallo and ora_ultimo_accettato is not None
                and ora - ora_ultimo_accettato < INTERVALLO_MIN_ORE):
            continue
        accettati.append((ora, durata))
        ora_ultimo_accettato = ora
    return accettati


def simula_notte(comandi, con_allarme, tempo_intervento_min=None):
    """Simula la notte con i comandi accettati. Stesso modello del passo 1.

    tempo_intervento_min: minuti tra allarme e intervento. None = valore di
    TEMPO_INTERVENTO_MIN (tecnico); 0 = protezione automatica.
    Restituisce: tempi, temperature, minuti sopra soglia, minuti di sbrinamento eseguiti.
    """
    if tempo_intervento_min is None:
        tempo_intervento_min = TEMPO_INTERVENTO_MIN

    numero_passi = int(DURATA_ORE * 3600 / DT)
    T = SETPOINT
    compressore_acceso = False
    tempi, temperature = [], []

    # Senza allarme, qualcuno interviene solo all'arrivo del personale (07:00)
    ora_intervento = ORE_ALL_ARRIVO
    allarme_scattato = False
    minuti_sopra_soglia = 0.0
    minuti_consecutivi = 0.0
    minuti_sbrinamento = 0.0

    for passo in range(numero_passi + 1):
        t_ore = passo * DT / 3600
        tempi.append(t_ore)
        temperature.append(T)

        # C'e' un comando di sbrinamento attivo in questo istante?
        comando_attivo = any(inizio <= t_ore < inizio + durata / 60
                             for inizio, durata in comandi)
        # Dopo l'intervento il banco e' in funzionamento locale: ignora i comandi remoti
        sbrinamento = comando_attivo and t_ore < ora_intervento

        if sbrinamento:
            compressore_acceso = False
            resistenze_accese = True
            minuti_sbrinamento += DT / 60
        else:
            resistenze_accese = False
            if T > SETPOINT + ISTERESI:
                compressore_acceso = True
            elif T < SETPOINT - ISTERESI:
                compressore_acceso = False

        potenza_netta = UA * (T_AMBIENTE - T)
        if compressore_acceso:
            potenza_netta -= P_FREDDO
        if resistenze_accese:
            potenza_netta += P_SBRINAMENTO
        T += potenza_netta / C * DT

        # Conto i minuti sopra soglia
        if T > T_SOGLIA:
            minuti_sopra_soglia += DT / 60
            minuti_consecutivi += DT / 60
        else:
            minuti_consecutivi = 0.0

        # Allarme indipendente: scatta e fissa l'ora dell'intervento
        if con_allarme and not allarme_scattato and minuti_consecutivi >= RITARDO_ALLARME_MIN:
            allarme_scattato = True
            ora_intervento = min(ora_intervento, t_ore + tempo_intervento_min / 60)

    return tempi, temperature, minuti_sopra_soglia, minuti_sbrinamento


# ---------------------------------------------------------------------------
# I CINQUE SCENARI: (regola R1, regola R2, allarme, minuti tra allarme e intervento)
# ---------------------------------------------------------------------------
SCENARI = {
    "0. Nessuna difesa": (False, False, False, None),
    "1. Filtro: solo durata max": (True, False, False, None),
    "2. Filtro: durata + intervallo": (True, True, False, None),
    "3. Solo allarme (tecnico)": (False, False, True, None),
    "4. Protezione automatica": (False, False, True, 0),
}
STILI = {
    "0. Nessuna difesa": ("tab:red", "-"),
    "1. Filtro: solo durata max": ("black", "--"),
    "2. Filtro: durata + intervallo": ("tab:green", "-"),
    "3. Solo allarme (tecnico)": ("tab:orange", "-"),
    "4. Protezione automatica": ("tab:purple", "--"),
}


def esegui_scenario(nome):
    """Esegue uno scenario: restituisce tempi, temperature, minuti sopra soglia, minuti di sbrinamento."""
    regola_durata, regola_intervallo, con_allarme, intervento = SCENARI[nome]
    accettati = command_guard(comandi_attaccante(), regola_durata, regola_intervallo)
    return simula_notte(accettati, con_allarme, intervento)


if __name__ == "__main__":
    print(f"Lo script dell'attaccante invia {len(comandi_attaccante())} comandi dalle 02:00 in poi")
    print(f"Merce persa = piu' di {TOLLERANZA_MIN} minuti sopra {T_SOGLIA:.0f} °C (criterio dello studio)\n")
    print(f"{'Scenario':<32}{'Sbrinamento':>12}{'T max':>10}{'Min. sopra soglia':>19}"
          f"{'Merce persa':>13}{'Perdita (20 negozi)':>21}")

    plt.figure(figsize=(9, 4.8))
    for nome in SCENARI:
        tempi, temperature, minuti, sbrinamento = esegui_scenario(nome)

        merce_persa = minuti > TOLLERANZA_MIN
        # Catena centralizzata: il nodo compromesso raggiunge tutti i negozi,
        # ma ogni negozio ha le proprie difese
        perdita = NUMERO_NEGOZI * VALORE_SURGELATI_PER_NEGOZIO if merce_persa else 0

        print(f"{nome:<32}{sbrinamento:>8.0f} min{max(temperature):>8.1f} °C{minuti:>19.0f}"
              f"{'SI' if merce_persa else 'NO':>13}{perdita:>19,.0f} €")

        colore, tratto = STILI[nome]
        plt.plot(tempi, temperature, color=colore, linestyle=tratto, label=nome)

    print("\nNota: negli scenari 0 e 1 alle 08:00 il banco e' ancora sopra soglia,")
    print("quindi i minuti sopra soglia sono un valore minimo.")

    plt.axhline(T_SOGLIA, color="gray", linestyle=":", label=f"Soglia {T_SOGLIA:.0f} °C")
    tacche = range(0, int(DURATA_ORE) + 1, 2)
    plt.xticks(list(tacche), [f"{int((ORA_INIZIO + h) % 24):02d}:00" for h in tacche])
    plt.xlabel("Ora")
    plt.ylabel("Temperatura nel banco (°C)")
    plt.title("Stesso attacco, difese diverse")
    plt.legend(loc="upper left", fontsize=8)
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(CARTELLA_FIGURE / "passo3_grafico.png", dpi=150)
    print("\nGrafico salvato in figures/passo3_grafico.png")
