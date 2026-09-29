# -*- coding: utf-8 -*-
"""
levGTAA — Strategie-Kern (reine Funktionen, ohne I/O, testbar).

Exakte Nachbildung der freigegebenen Backtest-Regel (Runde 16, r16m / r14lib):
  fuer jede Rangliste r in (MoM 1/3/6/9, MoM 3/6/12) und jedes L in 125..225 (1er):
      MoM_r   = Mittel der Renditen ueber 21*m Handelstage (m in Rangliste)
      zulaessig, wenn MoM_r > 0 UND SMA30/SMA_L - 1 > 0 (fehlende Werte = nicht zulaessig)
      Top 2 nach MoM_r (absteigend, bei Gleichstand Spaltenreihenfolge):
          Platz 1 -> 40 %, Platz 2 -> 60 % (jeweils nur, wenn zulaessig)
          genau ein Asset zulaessig -> max(40 %, 50 %) = 50 %  (Slotfloor)
  Gewicht = Mittel ueber alle L (je Rangliste), dann 1/2*(a) + 1/2*(b)
  Vol-Target 55 %: fuer die Fenster 42/63/84 Handelstage
      Vola = Std(Tagesrenditen des gehebelten Portfolios mit diesen Gewichten) * sqrt(252)
      Faktor = Mittel ueber die Fenster von min(1, 0.55 / Vola)
  Zielgewicht = Gewicht * Faktor, Rest Cash.
Entscheidung am letzten Handelstag des Monats (Schlusskurse), Handel am 1. Handelstag danach.
"""
import numpy as np
import pandas as pd

MONTH = 21


def mom_score(P, months):
    """Mittel der m-Monats-Renditen (m*21 Handelstage) — wie C.feat('mom', months)."""
    return sum(P / P.shift(MONTH * m) - 1 for m in months) / len(months)


def decision_weights(P, rows, rankings, Ls, K, tilt):
    """P: DataFrame 1x-Signalkurse (Spalten = Assets in fester Reihenfolge) auf dem US-Gitter.
    rows: Zeilen-Indizes der Entscheidungstage.
    Gibt (W, detail) zurueck: W (len(rows) x n) gemittelte Gewichte VOR Vol-Target;
    detail: dict mit je Rangliste Gewicht, Platz-1-Anteil und Kennzahlen je Asset."""
    rows = np.asarray(rows, int)
    n = P.shape[1]
    t0, t1 = float(tilt[0]), float(tilt[1])
    smaK = P.rolling(K).mean().values[rows]
    W_all = np.zeros((len(rows), n))
    P1_all = np.zeros((len(rows), n))
    detail = {"per_ranking": {}}
    for name, months in rankings.items():
        MO = mom_score(P, months).values[rows]
        MOn = np.nan_to_num(MO, nan=-1.0)
        Wr = np.zeros((len(rows), n)); P1r = np.zeros((len(rows), n)); ELr = np.zeros((len(rows), n))
        for L in Ls:
            smaL = P.rolling(L).mean().values[rows]
            cross = np.nan_to_num(smaK / smaL - 1.0, nan=-1.0)
            el = (MOn > 0) & (cross > 0)
            ELr += el
            key = np.where(el, MO, -np.inf)
            order = np.argsort(-key, axis=1, kind="stable")[:, :2]
            ii = np.arange(len(rows))
            ok0 = el[ii, order[:, 0]]; ok1 = el[ii, order[:, 1]]
            W = np.zeros((len(rows), n))
            W[ii[ok0], order[ok0, 0]] += t0
            W[ii[ok1], order[ok1, 1]] += t1
            one = ok0 & ~ok1                                  # genau ein zulaessiges Asset
            W[ii[one], order[one, 0]] = max(t0, 0.5)
            Wr += W
            P1r[ii[ok0], order[ok0, 0]] += 1.0
        Wr /= len(Ls); P1r /= len(Ls); ELr /= len(Ls)
        detail["per_ranking"][name] = dict(W=Wr, P1=P1r, EL=ELr, MOM=MO)
        W_all += Wr / len(rankings)
        P1_all += P1r / len(rankings)
    detail["P1"] = P1_all
    return W_all, detail


def vt_scale(R, rows, W, target, windows):
    """R: ndarray (T x n) gehebelte Tagesrenditen (NaN -> 0). Wie r9lib.vt_scale."""
    R = np.nan_to_num(np.asarray(R, float), nan=0.0)
    s = np.ones(len(rows))
    for i, d in enumerate(rows):
        if W[i].sum() <= 0 or d < max(windows):
            continue
        acc = []
        for L in windows:
            v = (R[d - L + 1:d + 1] @ W[i]).std() * np.sqrt(252)
            acc.append(min(1.0, target / v) if v > 0 else 1.0)
        s[i] = float(np.mean(acc))
    return s


def port_vols(R, d, w, windows):
    """Annualisierte Vola (ddof 0, wie vt_scale) des Portfolios w (gehebelte Tagesrenditen R) je Fenster, Stand Tag d."""
    R = np.nan_to_num(np.asarray(R, float), nan=0.0)
    w = np.asarray(w, float)
    if w.sum() <= 0 or d < max(windows):
        return [0.0 for _ in windows]
    return [float((R[d - L + 1:d + 1] @ w).std() * np.sqrt(252)) for L in windows]


def signature(assets, w, eps=1e-9):
    parts = [f"{a}:{round(float(x), 4)}" for a, x in zip(assets, w) if x > eps]
    return "|".join(sorted(parts)) if parts else "CASH"
