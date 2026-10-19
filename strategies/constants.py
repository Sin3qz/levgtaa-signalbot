# ============================================================================
#  levGTAA — Momentum-GTAA (freigegeben 29.09.2026, Stand Backtest-Runde 16; Anleihe ab 17.10.2026: 3x IEF statt 5x TLT)
#  Single Source of Truth fuer alle Parameter und Anzeigen.
#
#  Korb: Nasdaq 100, Bitcoin, US-Staatsanleihen, Gold — kein WTI.
#  Invest-Hebel (Produkt): 3x Nasdaq 100, 1x Bitcoin, 3x US-Treasury 7-10y (IEF), 3x Gold.
#  Signale IMMER auf 1x-Kursen (wie im Backtest: ^NDX, BTC-USD, TLT, GC=F). Das Anleihe-Signal bleibt TLT
#  (Runde 33: Signal TLT und Signal IEF bei 3x IEF statistisch gleichwertig, Bootstrap P 0,33; TLT = freigegebenes
#  Signal, auf dem alle Parameter bestimmt wurden). Vola fuer das Vol-Target aus IEF x 3 (= gehandeltes Produkt).
#
#  Zeitplan: Signal = Schlusskurse des LETZTEN Handelstags des Monats,
#            Handel  = 1. Handelstag des Folgemonats (NYSE-Kalender).
#
#  Regel (je Rangliste a/b und je L = 125..225 in 1er-Schritten):
#     zulaessig, wenn MoM > 0 UND SMA30 > SMA_L
#     Platz 1 = 40 %, Platz 2 = 60 %; nur ein Asset zulaessig -> 50 %; Rest Cash
#     Mittel ueber alle L;  Endgewicht = 1/2 * (a) + 1/2 * (b)
#     (a) MoM 1/3/6/9 Monate, (b) MoM 3/6/12 Monate (je Mittel der Monatsrenditen)
#  Vol-Target 55 %: Faktor = Mittel ueber 42/63/84 Tage von min(1, 0.55 / Vola des
#     gehebelten Portfolios); Zielgewicht = Gewicht * Faktor, Rest Cash.
#
#  Backtest 1993+ mit 3x IEF / Signal TLT (21 Tranchen, korrigierte Daten): CAGR 31,9 %, MaxDD -43 %,
#     Sortino 1,23, z31 3,30, z4 3,73, P(DD<-50 %) 6 %, P(DD<-75 %) 0 %; BTC ohne Drift 27,0 % / Sortino 1,09.
#  Nur letzter Handelstag: CAGR 35,1 %, MaxDD -47 %, Sortino 1,33, z31 3,39, z4 4,06, P(DD<-50 %) 7 %.
#  Zum Vergleich 5x TLT 1993+: CAGR 34,6 %, MaxDD -48 %, Sortino 1,26, P(DD<-50 %) 17 %.
#  (Langhistorie 1987+ nur mit 5x TLT rechenbar: CAGR 28,1 %, MaxDD -62 %, Sortino 1,05.)   KEINE ANLAGEBERATUNG.
# ============================================================================
STRAT_NAME = "levGTAA"
STRAT_LONG = "levGTAA (Momentum, monatlich)"
STRAT_ASCII = "levGTAA"                 # ntfy-Titel (Header muessen ASCII sein)
STRAT_KEY = "levgtaa"

# Reihenfolge = Spaltenreihenfolge im Backtest (bestimmt Gleichstands-Regel)
ASSETS = {
    "NASDAQ100": dict(signal="^NDX", ret="QQQ", leverage=3, display="Nasdaq 100", short="Nasdaq",
                      product="WisdomTree NASDAQ 100 3x Daily Leveraged", isin="IE00BLRPRL42"),
    "BTC":       dict(signal="BTC-USD", ret="BTC-USD", leverage=1, display="Bitcoin", short="Bitcoin",
                      product="1x-Bitcoin-ETP", isin="", crypto=True),
    "UST_IEF":   dict(signal="TLT", ret="IEF", leverage=3, display="US-Treasury 7-10y", short="UST",
                      product="WisdomTree US Treasuries 10Y 3x Daily Leveraged", isin="IE00BKT09032"),
    "GOLD":      dict(signal="GC=F", ret="GLD", leverage=3, display="Gold", short="Gold",
                      product="WisdomTree Gold 3x Daily Leveraged", isin="IE00B8HGT870"),
}

RANKINGS = {"MoM 1/3/6/9": (1, 3, 6, 9), "MoM 3/6/12": (3, 6, 12)}
SMA_SHORT = 30
SMA_LONG = list(range(125, 226))        # 125..225, 1er-Schritte (101 Laengen)
TILT = (0.40, 0.60)                     # Platz 1, Platz 2
SLOTFLOOR = 0.50                        # nur ein Asset zulaessig -> max(40 %, 50 %)
VT_TARGET = 0.55
VT_WINDOWS = (42, 63, 84)

GRID_START = "1999-01-04"               # US-Gitter (Warmup); History ab HISTORY_START
HISTORY_START = "2003-08-01"               # ab hier vollständige TLT/IEF-Historie (Yahoo ab 30.07.2002 + 12M-Momentum)
TRY_COUNT = 3

NTFY_LATE_DAYS = 7                      # verspaetete Monatsmeldung max. 7 Kalendertage nach dem Handelstag
INFO_FOOTER = "Hebel-ETPs: Pfad-/Emittentenrisiko. KEINE ANLAGEBERATUNG."

# Datenpruefung: Mindestanzahl Kurse je Signalreihe (Strategie braucht SMA/Momentum-Fenster + Reserve). Beginnt eine Reihe
# spaeter als beim letzten Lauf (abgeschnittene Yahoo-Antwort), wird ebenfalls nicht entschieden (Retry).
MIN_ROWS = 600
