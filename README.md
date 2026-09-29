# levGTAA — Momentum-GTAA (Signalbot)

Discord- und ntfy-Signalbot (GitHub Actions) für die freigegebene **levGTAA**-Strategie
(Stand 29.09.2026, Backtest-Runde 16). **KEINE ANLAGEBERATUNG.**

## Strategie
| Baustein | Signal (1x-Kurs, Yahoo) | Währung | Invest-Produkt (ISIN) |
|---|---|---|---|
| Nasdaq 100 | `^NDX` (Index) | USD | 3x — WisdomTree NASDAQ 100 3x Daily Leveraged (IE00BLRPRL42) |
| Bitcoin | `BTC-USD` | USD | 1x Bitcoin-ETP |
| US-Treasury 20y+ | `TLT` (adjustiert) | USD | 5x — Leverage Shares 5x Long 20+ Year Treasury Bond (XS2595672036) |
| Gold | `GC=F` (Front-Future) | USD | 3x — WisdomTree Gold 3x Daily Leveraged (IE00B8HGT870) |

Die Signalreihen sind **exakt die des Backtests** (p5data.sig_px: `^NDX`, `BTC-USD`, `TLT`, `GC=F`; alle USD).

- **Zeitplan:** Signal = Schlusskurse des **letzten Handelstags** des Monats, Handel am **1. Handelstag** des Folgemonats (NYSE-Kalender).
- **Zwei Ranglisten:** (a) MoM 1/3/6/9 Monate, (b) MoM 3/6/12 Monate (je Mittel der Monatsrenditen, 1 Monat = 21 Handelstage).
- **Je Rangliste und je L = 125, 126, …, 225:** zulässig, wenn MoM > 0 **und** SMA30 > SMA_L.
  Platz 1 = 40 %, Platz 2 = 60 %; ist nur ein Asset zulässig → 50 %; Rest Cash. Mittel über alle 101 Längen.
- **Endgewicht** = ½ · (a) + ½ · (b).
- **Vol-Target 55 %:** Faktor = Mittel über die Fenster 42/63/84 Tage von min(1; 0,55 / Vola des gehebelten Portfolios).
  Zielgewicht = Gewicht × Faktor, Rest Cash. Zum Monatswechsel wird immer auf die neuen Zielgewichte umgeschichtet.
- Die Vola für das Vol-Target wird aus den Tagesrenditen von `QQQ`, `BTC-USD`, `TLT`, `GLD` mal Produkthebel berechnet.

Backtest 1987+ (Mittel über alle 21 möglichen Handelstage): CAGR 28,1 %, MaxDD −62 %, Sortino 1,05, z31 1,93, z4 2,60,
P(DD<−50 %) 31 %, P(DD<−75 %) 1,3 %. Nur letzter Handelstag: CAGR 30,0 %, MaxDD −70 %, Sortino 1,08, z31 1,88, z4 2,82,
P(DD<−50 %) 34 %, P(DD<−75 %) 3,0 %.

**Geprüft:** Der Bot-Kern reproduziert die Backtest-Engine exakt (248 Monatsentscheidungen 2006–2026:
Gewichte vor Vol-Target identisch, Zielgewichte max. 0,005 Prozentpunkte Abweichung durch die Finanzierungskosten im Backtest-Vola).

## Benachrichtigungen
- **Discord:** jeden Tag (Tagesstatus mit aktuellen Zielgewichten, Signalen und dem nächsten Termin).
- **ntfy:** **immer genau einmal pro Monat**, am 1. Handelstag morgens (07:17 Berlin im Sommer, 06:17 im Winter), mit den
  Schlusskursen des Monatsletzten — auch wenn sich nichts ändert (Titel „keine Aenderung“). Die Meldung enthält die neuen
  Zielgewichte und die Änderung gegenüber dem Vormonat.
- Sind die Kursdaten an dem Morgen veraltet, versucht der Workflow es 2× im Abstand von 30 Minuten; klappt es nicht, holt
  der nächste **Handelstag** die Meldung nach (als „verspätet“ gekennzeichnet, max. 7 Tage) — nie am Wochenende/Feiertag.
  Doppelte Meldungen verhindert `notify_state_levgtaa.json` (wird erst nach erfolgreichem Push gespeichert).
- Gewichte mit **einer Nachkommastelle** (inkl. Cash), Hebel = echter Invest-Hebel (3x Nasdaq, 1x BTC, 5x TLT, 3x Gold).
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
