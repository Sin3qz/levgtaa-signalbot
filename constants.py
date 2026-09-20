# ============================================================================
#  levGTAA — offensiv, 3x-Aequivola (cap3), 6 Core-Bausteine.  MONATLICH (erster
#  Handelstag/Monat), Top-2 nach Momentum, 33/67-Tilt (P2-UEbergewicht, 1/3:2/3).
#  Cash-Fallback: Top-2-Auswahl beibehalten; nur 1 qualifiziert -> 50% + 50% Cash
#  (bester Kompromiss: CAGR 43.8/Sortino 1.36/MaxDD -48.1 vs. 100%-Konzentration 44.9/-54.3).
#  Trend SMA8 > SMA150 (von Patrick gewaehlt; im v6-Bericht als gleichwertige
#  Alternative zu SMA15 dokumentiert). Momentum = Summe 1/3/6/9-M. Kein Look-Ahead.
#  Verifiziert (v6-Engine, SMA8/150, 33/67, Fallback 50%+Cash): CAGR 43.8 /
#  Sortino 1.36 / MaxDD -48.1 / mm5 1.03 (flacherer Drawdown als 100%-Konzentration).
#  Hinweis: 'leverage' = Aequivola-ZIEL des Backtests. Real sind EM & TLT nur 1x
#  verfuegbar (1x-Naeherung) -> Produkt-String nennt die praktische Umsetzung.
# ============================================================================
STRAT_NAME = "levGTAA (offensiv, 3x-Aequivola cap3)"
STRAT_ASCII = "levGTAA"
STRAT_KEY  = "levgtaa"
REBALANCE_LABEL = "erster Handelstag des Monats"
SIGNAL_CURRENCY_NOTE = "Signale auf zuverlaessigen USD-1x-Kursen (Yahoo); kein Xetra-Lag (B1)."
INFO_FOOTER = ("3x-ETNs: Pfad-/Emittentenrisiko. Real EM/TLT nur 1x verfuegbar. "
               "KEINE ANLAGEBERATUNG.")
NTFY_MODE = "monthly"         # ntfy zum Monatswechsel IMMER (auch ohne Aenderung)
NOTIFY_DAYS = ["monthly_first"]   # 1. Handelstag; Bezug = 1. Handelstag Vormonat

ASSETS = {
 "NASDAQ100":   dict(ticker="QQQ", leverage=3.0, display="Nasdaq 100",
                     product="WisdomTree NASDAQ 100 3x", isin="IE00BLRPRL42"),
 "EUROSTOXX50": dict(ticker="FEZ", leverage=2.6, display="EuroStoxx 50",
                     product="WisdomTree EuroStoxx50 3x (o. Amundi 2x FR0010468983)",
                     isin="IE00B7SD4R47"),
 "EM":          dict(ticker="EEM", leverage=2.4, display="Emerging Markets",
                     product="iShares Core MSCI EM IMI 1x (1x-Naeherung, kein EM-Hebel)",
                     isin="IE00BKM4GZ66"),
 "TLT_LONG":    dict(ticker="TLT", leverage=3.0, display="US-Treasury 20y+",
                     product="iShares $ Treasury 20+y 1x (1x-Naeherung, kein 3x-Long)",
                     isin="IE00BSKRJZ44"),
 "GOLD":        dict(ticker="GLD", leverage=3.0, display="Gold",
                     product="WisdomTree Gold 3x", isin="IE00B8HGT870"),
 "WTI_OIL":     dict(ticker="USO", leverage=1.7, display="WTI Rohoel",
                     product="WisdomTree WTI Crude Oil 3x (~1.7x-Aequivola-Ziel)",
                     isin="IE00BMTM6B32"),
}
CFG = dict(mode="gtaa", rebalance="monthly_first", cooldown_days=0,
           S=8, L=150, N=2, lookbacks=(1,3,6,9), trend_mode="smax",
           weights=[1/3, 2/3], fallback="halfcash", try_count=3)   # 33/67; Fallback: 1 Asset -> 50% + Cash
