# levGTAA — Momentum-GTAA (Signalbot)

Discord- und ntfy-Signalbot (GitHub Actions) für die freigegebene **levGTAA**-Strategie
(Stand 29.09.2026, Backtest-Runde 16; Anleihe-Baustein ab 17.10.2026: **3x IEF statt 5x TLT**, Signal weiter TLT).
**KEINE ANLAGEBERATUNG.**

## Strategie
| Baustein | Signal (1x-Kurs, Yahoo) | Rendite/Vola (Yahoo) | Währung | Invest-Produkt (ISIN) |
|---|---|---|---|---|
| Nasdaq 100 | `^NDX` (Index) | `QQQ` | USD | 3x — WisdomTree NASDAQ 100 3x Daily Leveraged (IE00BLRPRL42) |
| Bitcoin | `BTC-USD` | `BTC-USD` | USD | 1x Bitcoin-ETP |
| US-Treasury 7-10y | `TLT` (adjustiert) | `IEF` (adjustiert) | USD | 3x — WisdomTree US Treasuries 10Y 3x Daily Leveraged (IE00BKT09032) |
| Gold | `GC=F` (Front-Future) | `GLD` | USD | 3x — WisdomTree Gold 3x Daily Leveraged (IE00B8HGT870) |

Die Signalreihen sind **exakt die des Backtests** (p5data.sig_px: `^NDX`, `BTC-USD`, `TLT`, `GC=F`; alle USD).
**Anleihe:** investiert wird 3x IEF (7–10 Jahre), das Signal (Momentum/SMA-Rangliste) bleibt bewusst auf `TLT`:
Backtest-Runde 33 zeigt Signal TLT und Signal IEF bei 3x-IEF-Invest als statistisch gleichwertig (Sortino 1,23 vs 1,22,
z31 3,30 vs 3,28, Bootstrap P 0,33); TLT ist das freigegebene Signal, auf dem alle Parameter bestimmt wurden.

- **Zeitplan:** Signal = Schlusskurse des **letzten Handelstags** des Monats, Handel am **1. Handelstag** des Folgemonats (NYSE-Kalender).
- **Zwei Ranglisten:** (a) MoM 1/3/6/9 Monate, (b) MoM 3/6/12 Monate (je Mittel der Monatsrenditen, 1 Monat = 21 Handelstage).
- **Je Rangliste und je L = 125, 126, …, 225:** zulässig, wenn MoM > 0 **und** SMA30 > SMA_L.
  Platz 1 = 40 %, Platz 2 = 60 %; ist nur ein Asset zulässig → 50 %; Rest Cash. Mittel über alle 101 Längen.
- **Endgewicht** = ½ · (a) + ½ · (b).
- **Vol-Target 55 %:** Faktor = Mittel über die Fenster 42/63/84 Tage von min(1; 0,55 / Vola des gehebelten Portfolios).
  Zielgewicht = Gewicht × Faktor, Rest Cash. Zum Monatswechsel wird immer auf die neuen Zielgewichte umgeschichtet.
- Die Vola für das Vol-Target wird aus den Tagesrenditen von `QQQ`, `BTC-USD`, `IEF`, `GLD` mal Produkthebel berechnet
  (= die tatsächlich gehandelten Produkte, also 3x IEF statt 5x TLT).

Backtest 1993+ mit **3x IEF / Signal TLT** (Mittel über alle 21 möglichen Handelstage, korrigierte Anleihedaten):
CAGR 31,9 %, MaxDD −43 %, Sortino 1,23, z31 3,30, z4 3,73, P(DD<−50 %) 6 %, P(DD<−75 %) 0 %
(BTC ohne Drift: CAGR 27,0 %, Sortino 1,09). Nur letzter Handelstag: CAGR 35,1 %, MaxDD −47 %, Sortino 1,33, z31 3,39,
z4 4,06, P(DD<−50 %) 7 %, P(DD<−75 %) 0 %. Zum Vergleich 5x TLT im selben Zeitraum: CAGR 34,6 %, MaxDD −48 %,
Sortino 1,26, P(DD<−50 %) 17 %. Die Langhistorie ab 1987 ist nur mit 5x TLT rechenbar (IEF-Vorläufer erst ab 1991/93):
CAGR 28,1 %, MaxDD −62 %, Sortino 1,05, z31 1,93, z4 2,60, P(DD<−50 %) 31 %, P(DD<−75 %) 1,3 %.

**Geprüft:** Der Bot-Kern reproduziert die Backtest-Engine (Monatsentscheidungen 2003–2026, Konfiguration 3x IEF /
Signal TLT): Gewichte vor Vol-Target identisch, Vol-Faktor max. 0,003 Prozentpunkte Abweichung (Finanzierungskosten
im Backtest-Vola). History beginnt 08/2003 (IEF/TLT bei Yahoo ab 30.07.2002 + 12-Monats-Momentum).

## Benachrichtigungen
- **Discord:** jeden Tag (Tagesstatus mit aktuellen Zielgewichten, Signalen und dem nächsten Termin).
- **ntfy:** **immer genau einmal pro Monat**, am 1. Handelstag morgens (07:17 Berlin im Sommer, 06:17 im Winter), mit den
  Schlusskursen des Monatsletzten — auch wenn sich nichts ändert (Titel „keine Aenderung“). Die Meldung enthält die neuen
  Zielgewichte und die Änderung gegenüber dem Vormonat.
- Sind die Kursdaten an dem Morgen veraltet, versucht der Workflow es 2× im Abstand von 30 Minuten; klappt es nicht, holt
  der nächste **Handelstag** die Meldung nach (als „verspätet“ gekennzeichnet, max. 7 Tage) — nie am Wochenende/Feiertag.
  Doppelte Meldungen verhindert `notify_state_levgtaa.json` (wird erst nach erfolgreichem Push gespeichert).
- Gewichte mit **einer Nachkommastelle** (inkl. Cash), Hebel = echter Invest-Hebel (3x Nasdaq, 1x BTC, 3x US-Treasury 7-10y, 3x Gold).
- **Vola-Cap-Anzeige:** Vola des gehebelten Signal-Portfolios (42/63/84 Tage) zum Entscheidungstag → Faktor
  = Ø min(1; 55 % / Vola); zusätzlich die aktuelle Vola des gehaltenen Ziel-Portfolios (nur Info — gehandelt wird
  nur monatlich).

## Datenprüfung vor jeder Berechnung
Datum des letzten Kurses (muss die zuletzt erwartete US-Sitzung sein), fehlende Handelstage und Tagessprünge über 30 %
(außer Bitcoin) werden geprüft und in der Nachricht gemeldet.

## Dateien
```
main.py                        Einstieg: Discord-Text schreiben, ntfy senden
send_ntfy.py                   ntfy-Push (wirft nie)
strategies/constants.py        ALLE Parameter (Single Source of Truth)
strategies/momentum_core.py    Strategie-Kern (reine Funktionen)
strategies/runner.py           Download, Prüfung, Nachricht, status_levgtaa.json, History
strategies/common.py           Kalender, Download, Datenprüfung (gleich in allen Bots)
.github/workflows/notify.yaml  täglicher Lauf 05:17 UTC
status_levgtaa.json            wird vom Bot geschrieben (Dashboard)
history_levgtaa.txt            alle Monatsentscheidungen (wird vom Bot geschrieben)
notify_state_levgtaa.json      ntfy-Zustand (wird vom Bot geschrieben)
```

## Einrichtung
Secrets: `DISCORD_WEBHOOK_URL`, `NTFY_TOPIC` (optional `NTFY_SERVER`), `PAT_PUSH`.
Settings → Actions → General → Workflow permissions → „Read and write permissions“.

## Ausfallsicherheit und Datenprüfung (Stand 29.09.2026)
- **Vor jeder Berechnung** je Kursreihe: Datum des letzten Kurses (US: zuletzt erwartete NYSE-Sitzung; Sensex/Xetra/FX:
  max. 4 Kalendertage alt), fehlende Handelstage, Sprünge > 30 %, Mindestlänge der Historie und Vergleich des
  Historienbeginns mit dem letzten Lauf (abgeschnittene Yahoo-Antwort), bei Indizes Schluss = Vortag (Platzhalter).
- **Keine Entscheidung und keine ntfy**, wenn eine Prüfung fehlschlägt (veraltet, abgeschnitten, unplausibler Sprung am
  jüngsten Tag, Kalender nicht ladbar): `needsRetry` → 2 Wiederholungen im Abstand von 30 Min, zusätzlich
  **Sicherheitslauf 11:47 UTC** (läuft nur, wenn der Morgenlauf nicht erfolgreich war). Fehlt bei einem US-Signal der
  jüngste Tag, rechnet der Bot nur bis zum letzten gemeinsamen Tag (keine fortgeschriebenen Kurse als Entscheidungsbasis).
- **Download fehlgeschlagen**: kein Handel, keine ntfy; letzter gültiger Stand bleibt im Dashboard (Handelsanweisung wird
  entfernt), Discord meldet den Fehler. Der nächste erfolgreiche Lauf rechnet alles aus der vollen Historie neu (auch den
  Cooldown) und holt eine fällige ntfy-Meldung am nächsten Handelstag nach („verspätet“).
- **Workflow-Fehler** (Installation/Start): Discord bekommt eine Fehlermeldung; Discord- und Commit-Schritt laufen immer
  (`if: always()`), Push mit 3 Versuchen — der ntfy-Zustand geht nicht verloren (keine Doppelmeldung).
- **Erststart/verlorener Zustand**: Ist ein Wechsel noch nicht gehandelt, wird er trotzdem gemeldet.
- Ist dauerhaft kein `NTFY_TOPIC` gesetzt, gilt die Meldung als erledigt (nur Discord), statt täglich „verspätet“ zu wiederholen.
