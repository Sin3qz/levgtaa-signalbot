# ============================================================================
#  levGTAA — offensiv, reale Hebelprodukte, 7 Core-Bausteine (inkl. 1x-BTC).
#  MONATLICH (erster Handelstag/Monat), Top-2 nach Momentum, 33/67-Tilt (Platz-2-
#  UEbergewicht, 1/3:2/3). Cash-Fallback: nur 1 Asset qualifiziert -> 50% + 50% Cash.
#  Trend SMA8 > SMA150. Momentum = Summe 1/3/6/9-Monats-Returns. Kein Look-Ahead.
#  INVEST-HEBEL = AEQUIVOLA (Vola-paritaetisch zu 3x-QQQ, ungecappt): QQQ 3.0x,
#  EuroStoxx50 2.6x, EM 2.4x, TLT 4.5x, Gold 3.5x, WTI 1.7x, BTC 1.0x. BTC ist ein
#  ganz normales Asset: Ranking nach 1/3/6/9-M-Momentum, Trend SMA8/150, Signal+Invest 1x.
#  Momentum/SMA werden IMMER auf 1x-USD-Kursen gerechnet; Hebel nur fuers Invest.
#  Verifiziert (v6-Engine, botcore halfcash-Modell): CAGR 50.5 / Sortino 1.43 /
#  MaxDD -50.2 / mm5 1.30 / WorstYear -18.0 (Aequivola-Hebel auf TLT/Gold hebt Sortino
#  1.38 -> 1.43 ggue. 3x-Cap).
# ============================================================================
STRAT_NAME = "levGTAA (offensiv, Aequivola-Hebel + BTC 1x)"
STRAT_ASCII = "levGTAA"
STRAT_KEY  = "levgtaa"
REBALANCE_LABEL = "erster Handelstag des Monats"
SIGNAL_CURRENCY_NOTE = "Signale auf zuverlaessigen USD-1x-Kursen (Yahoo); kein Xetra-Lag (B1)."
INFO_FOOTER = ("Gehebelte ETPs: Pfad-/Emittentenrisiko. BTC 1x. "
               "KEINE ANLAGEBERATUNG.")
NTFY_MODE = "monthly"         # ntfy zum Monatswechsel IMMER (auch ohne Aenderung)
NOTIFY_DAYS = ["monthly_first"]   # 1. Handelstag; Bezug = 1. Handelstag Vormonat

# leverage = AEQUIVOLA-Invest-Hebel (1 Nachkommastelle). Momentum/SMA IMMER auf 1x.
ASSETS = {
 "NASDAQ100":   dict(ticker="QQQ", leverage=3.0, display="Nasdaq 100",
                     product="3x-Nasdaq-100-ETP (Aequivola 3.0x)", isin=""),
 "EUROSTOXX50": dict(ticker="FEZ", leverage=2.6, display="EuroStoxx 50",
                     product="EuroStoxx-50-ETP (Aequivola 2.6x)", isin=""),
 "EM":          dict(ticker="EEM", leverage=2.4, display="Emerging Markets",
                     product="EM-ETP (Aequivola 2.4x)", isin=""),
 "TLT_LONG":    dict(ticker="TLT", leverage=4.5, display="US-Treasury 20y+",
                     product="Long-Treasury-ETP (Aequivola 4.5x)", isin=""),
 "GOLD":        dict(ticker="GLD", leverage=3.5, display="Gold",
                     product="Gold-ETP (Aequivola 3.5x)", isin=""),
 "WTI_OIL":     dict(ticker="USO", leverage=1.7, display="WTI Rohoel",
                     product="WTI-ETP (Aequivola 1.7x)", isin=""),
 "BTC":         dict(ticker="BTC-USD", leverage=1.0, display="Bitcoin",
                     product="1x-Bitcoin-ETP (USD)", isin=""),
}
CFG = dict(mode="gtaa", rebalance="monthly_first", cooldown_days=0,
           S=8, L=150, N=2, lookbacks=(1,3,6,9), trend_mode="smax",
           weights=[1/3, 2/3], fallback="halfcash", try_count=3)   # 33/67; Fallback: 1 Asset -> 50% + Cash
