# levGTAA (offensiv, 3x-Aequivola)

Discord- + ntfy-Signalbot (GitHub Actions) fuer die **levGTAA (offensiv, 3x-Aequivola)**-Strategie.
Gleiche, bewaehrte Infrastruktur wie der 3xSpyTips-Bot (`letsgo-signalbot`) — alle
Bugfixes B1–B12/F1–F4 uebernommen. Der Strategie-Kern ist unabhaengig gegen den
verifizierten v6-Backtest geprueft (0 Abweichung auf 5517 Handelstagen).

## Strategie
6 Core-Bausteine, Top-2 nach Momentum, **33/67-Tilt** (Platz-2-UEbergewicht, 1/3:2/3), 3x-Aequivola cap3. Trend **SMA8 > SMA150**, Momentum 1/3/6/9-M. Verifiziert (SMA8/33-67): CAGR 44,9 / Sortino 1,36 / MaxDD −54,3 / mm5 0,96.

- **Signale:** ausschliesslich auf zuverlaessigen **USD-1x-Kursen** (Yahoo), Entscheidung
  von gestern wirkt heute (`.shift(1)`, kein Look-Ahead). Momentum-Fenster = 21/42/63/126/189 Handelstage.
- **Rebalancing:** **Monatlich** — erster Handelstag des Monats. Taeglich Discord/Dashboard, ntfy nur zum Monatswechsel bei tatsaechlicher Aenderung.
- **ntfy (Handy-Push):** NUR bei echtem Handelswechsel am Monatsanfang, nur wenn sich die Allokation ggue. Vormonat aendert. Taeglich laeuft eine
  Discord-Statusmeldung.

## Signal-Ticker
`QQQ` · `FEZ` EuroStoxx50-USD · `EEM` EM · `TLT` Treasury20y+ · `GLD` · `USO` WTI. **Hinweis:** real sind EM & TLT nur 1x verfuegbar (1x-Naeherung).

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
