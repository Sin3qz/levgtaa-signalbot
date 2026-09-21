# levGTAA (offensiv, reale Hebel + BTC 1x)

Discord- + ntfy-Signalbot (GitHub Actions) fuer die **levGTAA (offensiv, reale Hebel + BTC 1x)**-Strategie.
Gleiche, bewaehrte Infrastruktur wie der 3xSpyTips-Bot (`letsgo-signalbot`) — alle
Bugfixes B1–B12/F1–F4 uebernommen. Der Strategie-Kern ist unabhaengig gegen den
verifizierten v6-Backtest geprueft (0 Abweichung auf 5517 Handelstagen).

## Strategie
7 Core-Bausteine **inkl. 1x-BTC** (normales Asset im Ranking), Top-2 nach Momentum, **33/67-Tilt** (Platz-2-UEbergewicht). **Aequivola-Invest-Hebel**: QQQ 3,0x · EuroStoxx50 2,6x · EM 2,4x · TLT 4,5x · Gold 3,5x · WTI 1,7x · **BTC 1,0x**. Trend **SMA8 > SMA150** (auf 1x), Momentum 1/3/6/9-M (auf 1x). Verifiziert: CAGR 50,5 / Sortino 1,43 / MaxDD −50,2 / mm5 1,30 / schlechtestes Jahr −18,0.

- **Signale:** ausschliesslich auf zuverlaessigen **USD-1x-Kursen** (Yahoo), Entscheidung
  von gestern wirkt heute (`.shift(1)`, kein Look-Ahead). Momentum-Fenster = 21/42/63/126/189 Handelstage.
- **Rebalancing:** **Monatlich** — erster Handelstag des Monats. Taeglich Discord/Dashboard, ntfy zum Monatswechsel (immer, auch ohne Aenderung).
- **ntfy (Handy-Push):** NUR bei echtem Handelswechsel am 1. Handelstag des Monats (immer; „keine Aenderung“ mit aktueller Top-2). Taeglich laeuft eine
  Discord-Statusmeldung.

## Signal-Ticker
`QQQ` · `FEZ` EuroStoxx50-USD · `EEM` EM · `TLT` Treasury20y+ · `GLD` · `USO` WTI · `BTC-USD` Bitcoin. **Alle Signale (Momentum/SMA) auf 1x-USD-Kursen**; Invest mit Aequivola-Hebel.

## Dateien
```
main.py                      # Einstieg (Vertrag: run_strategy -> (signal, None, text))
send_ntfy.py                 # ntfy-Push, wirft nie (F1/B10)
strategies/constants.py      # ALLE Parameter (Single Source of Truth, B4/B11)
strategies/gtaa_botcore.py   # verifizierter Strategie-Kern (identisch in allen 3 Bots)
strategies/runner.py         # Download + Frische + History + Nachricht + status_*.json
.github/workflows/notify.yaml
history_levgtaa.txt            # Allokations-Historie (committet, fuer Dashboard)
status_levgtaa.json            # aktueller Stand (committet, fuer Dashboard)
```

## Setup (Kurz — Details im GTAA_Signalbots_Setup.md)
1. Repo **public** anlegen, Dateien am **exakten Pfad** ablegen (v.a. `.github/workflows/notify.yaml`, B12).
2. Secrets: `DISCORD_WEBHOOK_URL`, `NTFY_TOPIC` (langer, geheimer Name; optional `NTFY_SERVER`).
3. **Settings → Actions → General → Workflow permissions → „Read and write permissions"** (B8!).
4. Actions-Tab → „Run workflow" testen. Cron: `17 5 * * *` (07:17 Berlin).

KEINE ANLAGEBERATUNG.
