"""
PASSO 5 - Il modello in forma ISU, i risultati in forma chiusa e il costo
========================================================================

1) MODELLO ISU (ingresso-stato-uscita), come in Teoria dei Sistemi:

     stato     x(t) = T(t)
     ingressi  u(t) = [u_c(t), u_s(t)]   compressore, resistenze (0 o 1)
     disturbo  w(t) = T_amb
     uscita    y(t) = x(t)

     dx/dt = -(UA/C) x + (UA/C) w - (P_f/C) u_c + (P_s/C) u_s
     y     = x

   cioe' dx/dt = A x + B u + E w, con A = -1/tau, B = [-P_f/C, P_s/C],
   E = 1/tau (matrici 1x1 e 1x2, perche' lo stato e' uno solo).

   E' lineare, tempo-invariante, del primo ordine. L'unico autovalore e'
   -UA/C = -1/tau < 0: il sistema e' asintoticamente stabile. Con ingressi
   costanti la temperatura tende in modo esponenziale all'equilibrio

     x_eq = T_amb + (P_s u_s - P_f u_c) / UA

   e la soluzione (risposta libera + forzata) e'

     x(t) = x_eq + (x0 - x_eq) * exp(-t / tau)

2) FORMA CHIUSA. Durante uno sbrinamento (u_c = 0, u_s = 1) l'equilibrio e'
   T_s = 52 °C; durante il recupero (u_c = 1, u_s = 0) e' T_c = -58 °C.
   Da qui, senza simulare:

     tempo per superare la soglia   t1 = tau * ln((T_s - T0) / (T_s - T_th))
     picco dopo d minuti            Tp = T_s + (T0 - T_s) * exp(-d / tau)
     tempo di rientro               tr = tau * ln((Tp - T_c) / (T_th - T_c))
     minuti sopra soglia            M(d) = d - t1 + tr        (se d > t1)

   La durata massima ammissibile e' la d per cui M(d) = 60 minuti.
   Vale perche' durante il rientro il termostato tiene il compressore acceso
   (T > -17 °C). T0 e' la temperatura alle 02:00, presa dalla simulazione,
   perche' dipende dalla fase del termostato.

3) LIMITI DI PROGETTO PER BANCHI DIVERSI. Le stesse formule, con UA o P_s
   cambiati e T0 ricalcolata ogni volta con la simulazione della notte
   normale: la durata massima e il tempo massimo di risposta non sono valori
   universali, si ricavano per ciascun banco.

4) COSTO. Una protezione da c euro all'anno per negozio conviene se la
   perdita media annua che evita, p * DeltaL, e' maggiore di c. La
   probabilita' annua di attacco riuscito oltre cui conviene e' quindi
   p* = c / DeltaL; qui la protezione evita tutta la perdita (DeltaL = L).
   I costi usati qui sono ESEMPI, non prezzi reali.
"""

import math

import passo1_banco_frigo as p1
import passo3_difese as p3
import passo4_sensibilita as p4
from passo2_negozi import TOLLERANZA_MIN, VALORE_SURGELATI_PER_NEGOZIO

T_TH = p1.T_SOGLIA


def costanti(ua=p1.UA, ps=p1.P_SBRINAMENTO):
    """Costante di tempo (minuti) ed equilibri in sbrinamento e con compressore acceso."""
    tau = p1.C / ua / 60
    t_s = p1.T_AMBIENTE + ps / ua
    t_c = p1.T_AMBIENTE - p1.P_FREDDO / ua
    return tau, t_s, t_c


TAU_MIN, T_S, T_C = costanti()


def temperatura_alle_02():
    """T0: temperatura del banco all'inizio dell'attacco, notte normale.

    Si prende dalla simulazione (con i parametri correnti del passo 3) perche'
    dipende dalla fase del termostato.
    """
    tempi, temperature, _, _ = p3.simula_notte([], False)
    indice = min(range(len(tempi)), key=lambda i: abs(tempi[i] - p3.ORE_ALL_ATTACCO))
    return temperature[indice]


def tempo_superamento(T0, ua=p1.UA, ps=p1.P_SBRINAMENTO):
    tau, t_s, _ = costanti(ua, ps)
    return tau * math.log((t_s - T0) / (t_s - T_TH))


def minuti_sopra_soglia(d, T0, ua=p1.UA, ps=p1.P_SBRINAMENTO):
    """Minuti sopra soglia per uno sbrinamento di d minuti, in forma chiusa."""
    tau, t_s, t_c = costanti(ua, ps)
    t1 = tempo_superamento(T0, ua, ps)
    if d <= t1:
        return 0.0
    picco = t_s + (T0 - t_s) * math.exp(-d / tau)
    rientro = tau * math.log((picco - t_c) / (T_TH - t_c))
    return d - t1 + rientro


def durata_massima(T0, ua=p1.UA, ps=p1.P_SBRINAMENTO, tolleranza=TOLLERANZA_MIN):
    """Durata di sbrinamento per cui i minuti sopra soglia valgono la tolleranza (bisezione)."""
    basso, alto = tempo_superamento(T0, ua, ps), 600.0
    for _ in range(100):
        medio = (basso + alto) / 2
        if minuti_sopra_soglia(medio, T0, ua, ps) > tolleranza:
            alto = medio
        else:
            basso = medio
    return (basso + alto) / 2


def limiti_per_parametro(nome, fattori):
    """Limiti di progetto quando un parametro del banco cambia (T0 ricalcolata ogni volta)."""
    righe = []
    for f in fattori:
        setattr(p3, nome, getattr(p4, "VALORI_ORIGINALI")[nome] * f)
        ua, ps = p3.UA, p3.P_SBRINAMENTO
        T0 = temperatura_alle_02()
        t1 = tempo_superamento(T0, ua, ps)
        d_max = durata_massima(T0, ua, ps)
        m30_chiusa = minuti_sopra_soglia(30, T0, ua, ps)
        m30_sim, _ = p4.prova(True, True, False)
        righe.append((f, T0, t1, m30_chiusa, m30_sim, d_max, d_max - t1 - p3.RITARDO_ALLARME_MIN))
        p4.ripristina()
    return righe


if __name__ == "__main__":
    T0 = temperatura_alle_02()
    print("1) MODELLO ISU")
    print(f"   autovalore -1/tau = {-1 / TAU_MIN:.4f} 1/min (tau = {TAU_MIN:.0f} min): stabile")
    print(f"   equilibri: sbrinamento {T_S:.0f} °C, compressore acceso {T_C:.0f} °C, "
          f"tutto spento {p1.T_AMBIENTE:.0f} °C")

    print("\n2) FORMA CHIUSA CONTRO SIMULAZIONE")
    print(f"   T0 alle 02:00 = {T0:.2f} °C")
    print(f"   tempo per superare {T_TH:.0f} °C: {tempo_superamento(T0):.1f} min")
    print(f"   {'durata d':>10}{'forma chiusa':>15}{'simulazione':>14}")
    for d in [20, 25, 30, 35, 40]:
        p3.DURATA_MAX_MIN = d
        simulato, _ = p4.prova(True, True, False)
        p4.ripristina()
        print(f"   {d:>7} min{minuti_sopra_soglia(d, T0):>12.1f} min{simulato:>11.1f} min")
    d_max = durata_massima(T0)
    print(f"   durata massima ammissibile (M = {TOLLERANZA_MIN} min): {d_max:.1f} min")

    # Allarme: lo sbrinamento dura t1 + ritardo dell'allarme + tempo di risposta
    t1 = tempo_superamento(T0)
    d_auto = t1 + p3.RITARDO_ALLARME_MIN
    print(f"   protezione automatica: sbrinamento di {d_auto:.1f} min -> "
          f"{minuti_sopra_soglia(d_auto, T0):.1f} min sopra soglia")
    # In simulazione l'allarme vede il superamento sulla griglia di 10 s (8.0 min
    # invece di 7.9), quindi lo sbrinamento dura un po' di piu'.
    accettati = p3.command_guard(p3.comandi_attaccante(), False, False)
    _, _, minuti_sim, sbrinamento_sim = p3.simula_notte(accettati, True, 0)
    print(f"   (simulazione, passo di 10 s: sbrinamento di {sbrinamento_sim:.1f} min -> "
          f"{minuti_sim:.1f} min sopra soglia)")
    print(f"   allarme con tecnico: tempo di risposta massimo = "
          f"{d_max:.1f} - {t1:.1f} - {p3.RITARDO_ALLARME_MIN} = {d_max - d_auto:.1f} min")

    print("\n3) LIMITI DI PROGETTO AL VARIARE DEL BANCO (T0 ricalcolata per ogni banco)")
    print("   Un r_max negativo vuol dire che nemmeno la protezione automatica (risposta 0)")
    print("   resta entro il criterio.")
    for nome, etichetta, fattori in [("UA", "UA ", p4.FATTORI_UA),
                                     ("P_SBRINAMENTO", "P_s", p4.FATTORI_PS)]:
        print(f"   {'':>11}{'T0':>9}{'t1':>7}{'M(30) chiusa':>14}{'M(30) sim.':>12}{'d_max':>8}{'r_max':>8}")
        for f, T0, t1, mc, ms, dmax, rmax in limiti_per_parametro(nome, fattori):
            print(f"   {etichetta} x {f:<4}{T0:>9.2f}{t1:>7.1f}{mc:>14.1f}{ms:>12.1f}{dmax:>8.1f}{rmax:>8.1f}")

    print("\n4) SOGLIA DI CONVENIENZA DI UNA PROTEZIONE (costi d'esempio)")
    L = VALORE_SURGELATI_PER_NEGOZIO
    for costo in [50, 100, 200, 300, 500]:
        print(f"   {costo:>4} € all'anno per negozio -> conviene se p > {costo / L:.2%} all'anno")
