# -*- coding: utf-8 -*-
"""
levGTAA — LIVE-Runner.

Vertrag fuer main.py:  run_strategy() -> (signal, ntfy_text, discord_text)
    signal None            -> nur Discord-Tagesstatus (kein ntfy)
    signal "BUY"/"SELL"/"SWITCH"/"HOLD"/"NOCHANGE" -> Monatswechsel-Meldung (ntfy IMMER, auch ohne Aenderung)
        BUY = aus Cash investiert, SELL = alles Cash, SWITCH = andere Bausteine,
        HOLD = gleiche Bausteine, Gewichte aendern sich um >= 0,5 Pp., NOCHANGE = nichts zu tun
    signal "Error"         -> Fehlertext

ntfy-Zeitpunkt: am 1. NYSE-Handelstag des Monats (morgens), Entscheidung auf den Schluss-
kursen des letzten Handelstags des Vormonats. Genau EINE Meldung je Monat (Zustand in
notify_state_levgtaa.json). Nur mit frischen Daten; fehlen Daten, holt der naechste Lauf
die Meldung nach (max. NTFY_LATE_DAYS Tage, als "verspaetet" gekennzeichnet).
"""
import numpy as np
import pandas as pd

from . import common as U
from . import momentum_core as MC
from .constants import (STRAT_NAME, STRAT_LONG, STRAT_KEY, ASSETS, RANKINGS, SMA_SHORT, SMA_LONG,
                        TILT, VT_TARGET, VT_WINDOWS, GRID_START, HISTORY_START, TRY_COUNT,
                        NTFY_LATE_DAYS, INFO_FOOTER, MIN_ROWS)

STATUS_FILE = f"status_{STRAT_KEY}.json"
NOTIFY_FILE = f"notify_state_{STRAT_KEY}.json"
HISTORY_FILE = f"history_{STRAT_KEY}.txt"
AL = list(ASSETS.keys())
PENDING_STATE = {}


def mark_error(e):
    """Lauf fehlgeschlagen: Status als needsRetry markieren (letzter gueltiger Stand bleibt)."""
    U.mark_status_error(STATUS_FILE, e)


def commit_notify_state():
    """Nach erfolgreichem ntfy-Push aufrufen: Monatsmeldung als gesendet markieren."""
    if PENDING_STATE:
        U.save_json(NOTIFY_FILE, dict(PENDING_STATE))
LEV = np.array([ASSETS[a]["leverage"] for a in AL], float)


# ==========================================================================
#  Daten
# ==========================================================================
def load_data(fetch=U.fetch_close):
    tickers = sorted({m["signal"] for m in ASSETS.values()} | {m["ret"] for m in ASSETS.values()})
    return {t: fetch(t, TRY_COUNT) for t in tickers}


def prepare(raw):
    prev_first = U.load_json(STATUS_FILE).get("firstDates", {})         # Erkennung abgeschnittener Yahoo-Antworten
    grid = U.build_grid(GRID_START, us_series=[raw[ASSETS[a]["signal"]] for a in AL if not ASSETS[a].get("crypto")])
    P = pd.DataFrame({a: U.oncal(raw[ASSETS[a]["signal"]], grid) for a in AL})
    RET = pd.DataFrame({a: U.oncal(raw[ASSETS[a]["ret"]], grid).pct_change() * ASSETS[a]["leverage"] for a in AL})
    fresh, warns, fr = True, [], {}
    for a in AL:
        m = ASSETS[a]
        for t in {m["signal"], m["ret"]}:
            f, last, w = U.check_series(f"{m['short']} ({t})", raw[t], grid,
                                        us_market=not m.get("crypto", False), crypto=m.get("crypto", False),
                                        index_level=t.startswith("^"), min_rows=MIN_ROWS, prev_first=prev_first.get(t))
            fr[t] = {"last": last, "fresh": f}
            fresh &= f
            warns += w
    return grid, P, RET, (not fresh), sorted(set(warns)), fr


# ==========================================================================
#  Berechnung
# ==========================================================================
def compute(P, RET):
    idx = P.index
    flags = U.month_end_flags(idx)
    rows = np.where(flags & (idx >= pd.Timestamp(HISTORY_START)))[0]
    W, det = MC.decision_weights(P, rows, RANKINGS, SMA_LONG, SMA_SHORT, TILT)
    sc = MC.vt_scale(RET.values, rows, W, VT_TARGET, VT_WINDOWS)
    WF = W * sc[:, None]
    return rows, W, sc, WF, det


def live_indicators(P, i):
    """Anzeige-Kennzahlen am Tag i: MoM je Rangliste und Mittel, Trend = Mittel SMA30/SMA_L-1."""
    out = {}
    for a in AL:
        p = P[a].values[: i + 1]
        moms = []
        for months in RANKINGS.values():
            v = np.mean([p[-1] / p[-1 - 21 * m] - 1 if len(p) > 21 * m else np.nan for m in months])
            moms.append(v)
        smaK = np.mean(p[-SMA_SHORT:]) if len(p) >= SMA_SHORT else np.nan
        tr = [smaK / np.mean(p[-L:]) - 1 for L in SMA_LONG if len(p) >= L]
        out[a] = dict(mom_a=moms[0], mom_b=moms[1], mom=np.nanmean(moms) if not all(np.isnan(moms)) else np.nan,
                      trend=float(np.mean(tr)) if tr else np.nan)
    return out


# ==========================================================================
#  Nachricht
# ==========================================================================
def _alloc_lines(w, bullet="•"):
    lines = []
    for k in np.argsort(-w):
        if w[k] > U.W_EPS:
            a = AL[k]
            lines.append(f"{bullet} {U.w1(w[k]):>5}  {ASSETS[a]['leverage']}x {ASSETS[a]['display']}")
    cash = 1 - w[w > U.W_EPS].sum()
    if cash > 0.0005:
        lines.append(f"{bullet} {U.w1(cash):>5}  Cash")
    return lines


def _delta_lines(w_new, w_old):
    out = []
    for k in np.argsort(-(np.abs(w_new - w_old))):
        d = w_new[k] - w_old[k]
        if abs(d) >= 0.005:
            out.append(f"  {ASSETS[AL[k]]['short']}: {U.w1(w_old[k])} -> {U.w1(w_new[k])}")
    c_old, c_new = 1 - w_old.sum(), 1 - w_new.sum()
    if abs(c_new - c_old) >= 0.005:
        out.append(f"  Cash: {U.w1(c_old)} -> {U.w1(c_new)}")
    return out


def _sig_rows(ind, w):
    order = sorted(AL, key=lambda a: -(ind[a]["mom"] if ind[a]["mom"] == ind[a]["mom"] else -9))
    rows = [[ASSETS[a]["short"], U.pct0(ind[a]["mom"]), U.pct0(ind[a]["trend"]),
             (U.w1(w[AL.index(a)]) if w[AL.index(a)] > U.W_EPS else "–")] for a in order]
    return order, rows


def _change_type(w_new, w_old):
    s_new = {a for a, x in zip(AL, w_new) if x > U.W_EPS}
    s_old = {a for a, x in zip(AL, w_old) if x > U.W_EPS}
    if s_new == s_old:
        return "HOLD"
    if not s_new:
        return "SELL"
    if not s_old:
        return "BUY"
    return "SWITCH"


HEAD = {"BUY": "🟢 BUY — neu investiert", "SELL": "🔴 SELL — alles in Cash", "SWITCH": "🔄 UMSCHICHTUNG",
        "HOLD": "🔁 Gleiche Bausteine — Gewichte anpassen", "NOCHANGE": "⚪ KEINE ÄNDERUNG zum Vormonat"}


def build_messages(ctx):
    c = ctx
    L = []
    if c["signal"]:
        late = f" (verspätet; regulär {U.de(c['trade'])})" if c["late"] else ""
        dl = _delta_lines(c["w"], c["w_prev"])
        head = HEAD[c["signal"]]
        L += [f"🔔 {STRAT_NAME} — MONATSWECHSEL{late}", head,
              (f"Heute handeln ({U.de(c['today'])}), Signal: Schluss {U.de(c['dec'])}" if c["late"] else f"Handeln am {U.de(c['trade'])} (Signal: Schluss {U.de(c['dec'])})"), ""]
        L += ["Neue Zielgewichte:"] + _alloc_lines(c["w"])
        L += ["Änderung ggü. Vormonat:"] + (dl if dl else ["  keine (< 0,5 Pp.)"])
    else:
        if c.get("pend_dec"):
            L += [f"⏳ Monatssignal (Schluss {U.de(c['pend_dec'])}) AUSSTEHEND — Kursdaten fehlen/veraltet, Retry läuft.",
                  f"Handel regulär am {U.de(c['pend_trade'])}; die ntfy-Meldung kommt, sobald die Daten da sind (ggf. „verspätet“).",
                  "Bis dahin gilt noch:", ""]
        L += [f"📊 {STRAT_LONG} — Tagesstatus", f"Ziel {'ab' if c['today'] < c['trade'] else 'seit'} {U.de(c['trade'])} (Signal {U.de_short(c['dec'])}):"]
        L += _alloc_lines(c["w"])
    vw = "/".join(str(x) for x in VT_WINDOWS)
    L += [f"Vola-Cap {VT_TARGET*100:.0f}% (gehebelt, {vw} T):",
          f"  Signal-Portfolio {'/'.join(f'{v*100:.0f}' for v in c['vol_pre'])}% → Faktor {c['vt']:.2f}",
          f"  Ist-Portfolio heute {'/'.join(f'{v*100:.0f}' for v in c['vol_now'])}% (Ø {np.mean(c['vol_now'])*100:.0f}%)",
          f"Nächstes Signal: Schluss {U.de_short(c['next_dec'])} → Handel {U.de(c['next_trade'])}" if c["next_dec"] else ""]
    order, rows = _sig_rows(c["ind"], c["w"])
    tab = U.table(["Asset", "MoM", "Trend", "Ziel"], rows, "lrrr")
    disc = L + ["", f"Signale (1x-Kurse, Stand {U.de_short(c['asof'])}):", "```"] + tab + ["```",
                "MoM = Ø der Ranglisten 1/3/6/9 & 3/6/12 M", f"Trend = Ø SMA{SMA_SHORT}/SMA{SMA_LONG[0]}–{SMA_LONG[-1]}"]
    ntfy = L + ["", f"Signale (Stand {U.de_short(c['asof'])}):"] + [
        f"{r[0]}: MoM {r[1]}, Trend {r[2]}, Ziel {r[3]}" for r in rows]
    tail = []
    if c["stale"]:
        tail += ["", "⚠️ Kursdaten evtl. veraltet — Retry läuft; ntfy erst mit frischen Daten."]
    if c["warns"]:
        tail += ["", "⚠️ Datenprüfung:"] + [f"• {w}" for w in c["warns"][:6]]
    if c["no_new_day"]:
        tail += [f"ℹ️ Kein neuer US-Handelstag seit {U.de_short(c['asof'])} (Wochenende/Feiertag)"]
    tail += ["", INFO_FOOTER]
    disc = [x for x in disc if x is not None] + tail
    ntfy = [x for x in ntfy if x is not None] + tail
    return "\n".join(ntfy).replace("\n\n\n", "\n\n"), "\n".join(disc).replace("\n\n\n", "\n\n")


# ==========================================================================
#  Hauptfunktion
# ==========================================================================
def run_strategy(raw=None, write_files=True):
    if raw is None:
        try:
            raw = load_data()
        except Exception as e:
            mark_error(e)
            return ("Error", None, f"{STRAT_NAME}: Daten konnten nicht geladen werden: {e}" + "\n" + U.ERROR_HINT)
    grid, P, RET, stale, warns, fr = prepare(raw)
    rows, W, sc, WF, det = compute(P, RET)
    idx = P.index
    i_last = len(idx) - 1
    k = len(rows) - 1                                        # juengste Monatsentscheidung
    dec = idx[rows[k]].date()
    trade = U.next_session_after(dec)
    w, w_prev = WF[k], (WF[k - 1] if k > 0 else np.zeros(len(AL)))
    nd = [d for d in U.nyse_sessions(trade, trade + pd.Timedelta(days=45)) if (d.month, d.year) != (trade.month, trade.year)]
    next_trade = nd[0] if nd else None
    next_dec = max(d for d in U.nyse_sessions(trade, next_trade) if d < next_trade) if next_trade else None

    # ---- ntfy: genau einmal je Monatsentscheidung, am/ab dem Handelstag ----
    # Fehlt der Schlusskurs des juengsten Monatsletzten noch (veraltete Daten), ist das neue Monatssignal ausstehend
    me = U.last_month_end_session(U.expected_session_date())
    pend_dec = me if (me is not None and me > dec) else None
    pend_trade = U.next_session_after(pend_dec) if pend_dec else None
    today = U.berlin_today()
    state = U.load_json(NOTIFY_FILE)
    signal, late = None, False
    if state.get("lastDecision") != dec.isoformat():
        if today > trade + pd.Timedelta(days=NTFY_LATE_DAYS):
            state["lastDecision"] = dec.isoformat(); state["skipped"] = today.isoformat()   # Erststart mitten im Monat
            if write_files:
                U.save_json(NOTIFY_FILE, state)
        elif today >= trade and not stale and U.ntfy_allowed(today):   # nur an NYSE-Handelstagen
            signal = _change_type(w, w_prev)
            if signal == "HOLD" and not _delta_lines(w, w_prev):
                signal = "NOCHANGE"
            late = today > trade
            state.update(lastDecision=dec.isoformat(), sentOn=today.isoformat(), signal=signal)
            PENDING_STATE.clear(); PENDING_STATE.update(state)       # wird erst nach erfolgreichem Push gespeichert

    ind = live_indicators(P, i_last)
    Rv = RET.values
    vol_pre = MC.port_vols(Rv, rows[k], W[k], VT_WINDOWS)          # Signal-Portfolio vor VT, Stand Entscheidung
    vol_now = MC.port_vols(Rv, i_last, w, VT_WINDOWS)              # gehaltenes Ziel-Portfolio (nach VT), Stand heute
    vol_asset = {a: U.num(float(np.nan_to_num(Rv[i_last - 62:i_last + 1, AL.index(a)]).std() * np.sqrt(252)), 4) for a in AL}
    ctx = dict(signal=signal, late=late, today=today, dec=dec, trade=trade, w=w, w_prev=w_prev, pend_dec=pend_dec, pend_trade=pend_trade, vt=sc[k], next_dec=next_dec,
               vol_pre=vol_pre, vol_now=vol_now,
               next_trade=next_trade, ind=ind, asof=idx[-1].date(), stale=stale, warns=warns,
               no_new_day=(not stale) and idx[-1].date() < U.berlin_yesterday())
    ntfy_text, disc_text = build_messages(ctx)

    # ---- History / Status (Dashboard) ----
    hist = []
    for j in range(len(rows)):
        dj = idx[rows[j]].date()
        p1 = det["P1"][j]
        lead = AL[int(np.argmax(p1))] if p1.max() > 0 else "CASH"
        hist.append(dict(date=dj.isoformat(), trade=(U.next_session_after(dj).isoformat() if j == len(rows) - 1 else idx[min(rows[j] + 1, len(idx) - 1)].date().isoformat()),
                         allocation=MC.signature(AL, WF[j], eps=U.W_EPS), lead=lead, vt=round(float(sc[j]), 4)))
    order, trows = _sig_rows(ind, w)
    status = {
        "strategy": STRAT_LONG, "name": STRAT_NAME, "key": STRAT_KEY,
        "updated": pd.Timestamp.now(tz=U.TZ).isoformat(),
        "rebalance": "monthly", "rebalanceLabel": "Signal Monatsletzter → Handel 1. Handelstag",
        "asOf": idx[-1].date().isoformat(), "needsRetry": bool(stale), "dataWarnings": warns,
        "decisionDate": dec.isoformat(), "tradeDate": trade.isoformat(),
        "nextDecision": next_dec.isoformat() if next_dec else None,
        "nextRebalance": next_trade.isoformat() if next_trade else None,
        "changedToday": bool(signal in ("BUY", "SELL", "SWITCH", "HOLD")), "changeType": signal,
        "monthlyNotifyToday": bool(signal is not None), "late": bool(late), "pendingDecision": pend_dec.isoformat() if pend_dec else None,
        "pendingTrade": pend_trade.isoformat() if pend_trade else None,
        "vtFactor": round(float(sc[k]), 4), "cooldown": 0,
        "weightDecimals": 1,
        "vola": {"cap": VT_TARGET, "windows": list(VT_WINDOWS),
                 "signalPre": [U.num(v, 4) for v in vol_pre], "signalPreMean": U.num(float(np.mean(vol_pre)), 4),
                 "factor": round(float(sc[k]), 4), "decisionDate": dec.isoformat(),
                 "holdingNow": [U.num(v, 4) for v in vol_now], "holdingNowMean": U.num(float(np.mean(vol_now)), 4),
                 "asOf": idx[-1].date().isoformat(), "assetVol63": vol_asset},
        "allocation": ([{"asset": a, "display": ASSETS[a]["display"], "weight": round(float(w[AL.index(a)]), 4),
                         "leverage": ASSETS[a]["leverage"], "product": ASSETS[a]["product"], "isin": ASSETS[a]["isin"]}
                        for a in sorted(AL, key=lambda a: -w[AL.index(a)]) if w[AL.index(a)] > U.W_EPS]
                       or [{"asset": "CASH", "display": "Cash", "weight": 1.0, "leverage": 1, "product": "—", "isin": ""}]),
        "signals": {a: {"display": ASSETS[a]["display"], "leverage": ASSETS[a]["leverage"],
                        "momentum": U.num(ind[a]["mom"]), "momA": U.num(ind[a]["mom_a"]), "momB": U.num(ind[a]["mom_b"]),
                        "trend": U.num(ind[a]["trend"]), "target": U.num(w[AL.index(a)], 4)} for a in AL},
        "table": {"head": ["Baustein", "Ø-MoM", "Trend", "Vola", "Ziel"],
                  "note": (f"Ø-MoM = Mittel der Ranglisten MoM 1/3/6/9 M und 3/6/12 M · Trend = Ø über L={SMA_LONG[0]}–{SMA_LONG[-1]} "
                           f"von SMA{SMA_SHORT}/SMA_L − 1 · Vola = 63 Tage, annualisiert, gehebelt · Ziel = Zielquote nach Vol-Target"),
                  "rows": [[f"{ASSETS[a]['leverage']}x {ASSETS[a]['short']}", U.num(ind[a]["mom"]), U.num(ind[a]["trend"]),
                            vol_asset[a], U.num(w[AL.index(a)], 4)] for a in order],
                  "kinds": ["text", "spct", "spct", "pct1", "pct1"]},
        "timeline": {"span": "letzte 120 Monatsentscheidungen",
                     "what": "welches Asset auf Platz 1 lag (höchstes Momentum; Anteil über alle 202 Teilentscheidungen)",
                     "items": [{"date": h["date"], "lead": h["lead"], "allocation": h["allocation"]} for h in hist[-120:]]},
        "freshness": fr, "firstDates": U.merge_first(U.load_json(STATUS_FILE).get("firstDates"), {t: U.first_date(s) for t, s in raw.items()}),
    }
    if write_files:
        U.save_json(STATUS_FILE, status)
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                f.write("decision_date,trade_date,allocation,vt_factor,platz1\n")
                for h in hist:
                    f.write(f"{h['date']},{h['trade']},{h['allocation']},{h['vt']},{h['lead']}\n")
        except Exception as e:
            print(f"History-Schreibfehler (ignoriert): {e}")
    return signal, ntfy_text, disc_text
