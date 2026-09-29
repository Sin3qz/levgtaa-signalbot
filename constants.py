# ============================================================================
#  levGTAA — Momentum-GTAA (freigegeben 29.09.2026, Stand Backtest-Runde 16)
#  Single Source of Truth fuer alle Parameter und Anzeigen.
#
#  Korb: Nasdaq 100, Bitcoin, US-Treasury 20y+, Gold — kein WTI.
#  Invest-Hebel (Produkt): 3x Nasdaq 100, 1x Bitcoin, 5x TLT, 3x Gold.
#  Signale IMMER auf 1x-Kursen (wie im Backtest: ^NDX, BTC-USD, TLT, GC=F).
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
#  Backtest 1987+ (21 Tranchen): CAGR 28,1 %, MaxDD -62 %, Sortino 1,05, z31 1,93,
#     z4 2,60, P(DD<-50 %) 31 %, P(DD<-75 %) 1,3 %.
#  Nur letzter Handelstag: CAGR 30,0 %, MaxDD -70 %, Sortino 1,08, z31 1,88, z4 2,82,
#     P(DD<-50 %) 34 %, P(DD<-75 %) 3,0 %.   KEINE ANLAGEBERATUNG.
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
    "TLT_LONG":  dict(signal="TLT", ret="TLT", leverage=5, display="US-Treasury 20y+", short="TLT",
                      product="Leverage Shares 5x Long 20+ Year Treasury Bond", isin="XS2595672036"),
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
HISTORY_START = "2003-01-01"
TRY_COUNT = 3

NTFY_LATE_DAYS = 7                      # verspaetete Monatsmeldung max. 7 Kalendertage nach dem Handelstag
INFO_FOOTER = "Hebel-ETPs: Pfad-/Emittentenrisiko. KEINE ANLAGEBERATUNG."

# Datenpruefung: Mindestanzahl Kurse je Signalreihe (Strategie braucht SMA/Momentum-Fenster + Reserve). Beginnt eine Reihe
# spaeter als beim letzten Lauf (abgeschnittene Yahoo-Antwort), wird ebenfalls nicht entschieden (Retry).
MIN_ROWS = 600
