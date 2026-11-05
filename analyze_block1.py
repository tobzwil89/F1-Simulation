"""Wertet den ersten Trainingsblock aus (Plan: plans/block1_stints.csv).

Lauf: python3 analyze_block1.py [csv]. Ohne Angabe nimmt es die neueste Datei aus data/tests/.
Schreibt results/block1_estimates.json.

Modell: Rundenzeit = Grundzeit + Aufschlag * Sprit + Reifeneffekt * verbrauchter Reifen (Prozentpunkte)
Sprit und Reifen sind jeweils der Stand zu Rundenbeginn.
Der Spritaufschlag kommt aus den Einzelrunden mit 20/60/100 l. Innerhalb des 8-Runden-Stints fallen
Sprit und Reifen gleichzeitig, dort allein ließen sie sich nicht trennen.

Jede Runde hat einen Zufallsanteil. Zuerst wird dessen Größe geschätzt, aus den zwei identischen Stints
und aus den Abweichungen im 8-Runden-Stint. Daraus folgt die Rundenzahl, um 50 Setup-Punkte zu erkennen.
"""
import glob
import json
import sys

import numpy as np
import pandas as pd
from scipy import stats

from power import direct_delta, flank_delta, laps_per_setting

PLAN = "plans/block1_stints.csv"
PREDICTION = "results/spain_prediction.json"
COSTS = "results/cost_curves.json"
POWER_PARAMS = ["Brake Balance", "Differential", "Engine"]
OUT = "results/block1_estimates.json"
SETUP_COLS = ["Rear Wing", "Front Wing", "Engine", "Brake", "Differential", "Suspension"]
WEATHER = ["Temperature", "Humidity", "Wind (Avg. Speed)", "Wind (Gusts)", "Air Density", "Air Pressure"]


def ols(X, y):
    """Kleinste Quadrate mit Standardfehlern und 95-%-Intervallen."""
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    res = y - X @ b
    df = len(y) - X.shape[1]
    if df <= 0 or np.linalg.matrix_rank(X) < X.shape[1]:
        return None
    s2 = (res**2).sum() / df
    se = np.sqrt(np.diag(s2 * np.linalg.inv(X.T @ X)))
    t = stats.t.ppf(0.975, df)
    return {"b": b, "se": se, "lo": b - t * se, "hi": b + t * se, "sd": np.sqrt(s2), "df": df, "res": res}


def ci_sd(ss, df_):
    """95-%-Intervall einer Standardabweichung aus Quadratsumme und Freiheitsgraden."""
    return np.sqrt(ss / stats.chi2.ppf(0.975, df_)), np.sqrt(ss / stats.chi2.ppf(0.025, df_))


def load(path):
    df = pd.read_csv(path)
    if df.empty:
        sys.exit(f"{path} enthält keine Zeilen.")
    plan = pd.read_csv(PLAN)
    p = plan.iloc[0]
    df = df[(df["Round"] == p["Round"]) & (df["Track"] == p["Track"])]
    if "Qualifying" in df and pd.to_numeric(df["Qualifying"], errors="coerce").fillna(0).astype(bool).any():
        n = pd.to_numeric(df["Qualifying"], errors="coerce").fillna(0).astype(bool)
        print(f"Hinweis: {n.sum()} Zeilen mit gesetztem Qualifying ausgeschlossen.")
        df = df[~n]
    match = (df[SETUP_COLS] == p[SETUP_COLS].astype(float)).all(axis=1)
    if not match.any():
        sys.exit("Keine Runde mit dem geplanten Setup gefunden. Vorhandene Setups:\n" + df[SETUP_COLS].drop_duplicates().to_string())
    df = df[match]
    tyre = df["Tyre Choice"].astype(str).str.strip().str.lower()
    if not (tyre == "extra soft").any():
        sys.exit(f"Reifen nicht als Extra Soft erkannt. Vorhandene Werte: {sorted(tyre.unique())}. Bitte Zuordnung im Skript anpassen.")
    df = df[tyre == "extra soft"].sort_values(["Stint", "Lap"]).reset_index(drop=True)
    return df, plan


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else max(glob.glob("data/tests/practice_*.csv"), default=None)
    if path is None:
        sys.exit("Keine Datei in data/tests/. Erst fetch_practice_data.py ausführen.")
    print("Datei:", path)
    df, plan = load(path)
    ref = json.load(open(PREDICTION))
    remain = df["Tyre Remaining"] * (100 if df["Tyre Remaining"].max() <= 1.5 else 1)

    # Stints gegen Plan
    stints = df.groupby("Stint").agg(Runden=("Lap", "size"), Sprit_erste=("Fuel", "first"), Zeit_Mittel=("Lap Time", "mean"))
    print("\nStints\n", stints.round(3).to_string(), sep="")
    planned = sorted(zip(plan["Laps"], plan["Fuel"]))
    if len(stints) != len(plan) or sorted(stints["Runden"]) != sorted(plan["Laps"]):
        print(f"WARNUNG: Stints passen nicht zum Plan {planned}. Abgebrochener Stint oder weitere Daten?")
    for c in WEATHER:
        if c in df and df[c].nunique() > 1:
            print(f"WARNUNG: {c} schwankt im Block, das stört die Schätzung.")

    # Verbrauch und Verschleiß aus aufeinanderfolgenden Runden
    d_fuel = -df.groupby("Stint")["Fuel"].diff().dropna()
    d_tyre = -remain.groupby(df["Stint"]).diff().dropna()
    if d_fuel.empty:
        sys.exit("Kein Stint mit mehreren Runden, Verbrauch und Verschleiß nicht schätzbar.")
    fuel_per_lap, wear_per_lap = d_fuel.mean(), d_tyre.mean()
    print(f"\nVerbrauch: {fuel_per_lap:.3f} l/Runde (Streuung {d_fuel.std():.3f}, {len(d_fuel)} Differenzen)")
    print(f"Verschleiß: {wear_per_lap:.3f} Prozentpunkte/Runde (Streuung {d_tyre.std():.3f})")
    print(f"Reifenlimit daraus: etwa {100 / wear_per_lap:.0f} Runden")

    # Steht in Fuel der Stand zu Beginn oder am Ende der Runde?
    first = df.groupby("Stint").head(1)
    planned_fuels = plan["Fuel"].to_numpy(float)
    gap = np.mean([planned_fuels[np.abs(planned_fuels - f).argmin()] - f for f in first["Fuel"]])
    end_of_lap = bool(abs(gap - fuel_per_lap) < abs(gap))
    print(f"Spalte Fuel: Abstand erste Runde zum Plan {gap:.3f} l, gedeutet als Stand am {'Rundenende' if end_of_lap else 'Rundenbeginn'}.")
    fuel = df["Fuel"] + (fuel_per_lap if end_of_lap else 0)
    used = 100 - remain - (wear_per_lap if end_of_lap else 0)
    used = used - used.groupby(df["Stint"]).transform("min")  # frischer Reifen zu Stintbeginn = 0
    t = df["Lap Time"].to_numpy(float)
    one = np.ones(len(df))
    lap_in_stint = df.groupby("Stint").cumcount()

    # Hauptmodell
    fit = ols(np.c_[one, fuel, used], t)
    if fit is None:
        sys.exit("Zu wenige oder zu ähnliche Runden für das Modell.")
    base, per_l, per_pct = fit["b"]
    print(f"\nGrundzeit (leerer Tank, frischer Extra Soft): {base:.3f} s  [{fit['lo'][0]:.3f}; {fit['hi'][0]:.3f}]")
    print(f"Aufschlag je Liter: {per_l:.4f} s/l  [{fit['lo'][1]:.4f}; {fit['hi'][1]:.4f}]")
    print(f"Reifeneffekt: {per_pct:+.4f} s je Prozentpunkt  [{fit['lo'][2]:+.4f}; {fit['hi'][2]:+.4f}]")
    span = used.max()
    effect = fit["lo"][2] > 0 or fit["hi"][2] < 0
    print(f"  Beobachtet wurden nur {span:.1f} Prozentpunkte Verschleiß; ein Knick bei stärker abgefahrenen Reifen ist so nicht zu sehen.")
    print("  " + ("Reifenzustand beeinflusst die Zeit nachweisbar." if effect else f"Kein Effekt nachweisbar. Im Stint maximal möglich: {max(abs(fit['lo'][2]), abs(fit['hi'][2])) * span:.2f} s."))

    # Zufall je Runde: zwei Quellen, dann zusammengelegt
    a = df.loc[lap_in_stint == 0]
    twenty = a[a["Fuel"].sub(20).abs() < abs(gap) + 1]["Lap Time"].to_numpy(float)
    pair_ss = (twenty[0] - twenty[1]) ** 2 / 2 if len(twenty) >= 2 else None
    long_id = df.groupby("Stint")["Lap"].transform("size").idxmax()
    long_stint = df["Stint"] == df.loc[long_id, "Stint"]
    laps_long = lap_in_stint[long_stint].to_numpy(float)
    trend = np.polyfit(laps_long, t[long_stint.to_numpy()], 1) if long_stint.sum() >= 3 else None
    long_ss = ((t[long_stint.to_numpy()] - np.polyval(trend, laps_long)) ** 2).sum() if trend is not None else None
    long_df = int(long_stint.sum()) - 2

    def show(label, ss, df_):
        lo, hi = ci_sd(ss, df_)
        print(f"  {label}: {np.sqrt(ss / df_):.3f} s  (95 %: {lo:.3f} bis {hi:.3f}, {df_} Freiheitsgrade)")

    print("\nZufall je Runde (Standardabweichung)")
    if pair_ss is None or long_ss is None:
        sys.exit("Für die Zufallsschätzung fehlen die zwei 20-l-Stints oder der lange Stint.")
    show("Aus den zwei identischen Stints", pair_ss, 1)
    show("Aus dem langen Stint, um die Gerade bereinigt", long_ss, long_df)
    noise_ss, noise_df = pair_ss + long_ss, 1 + long_df
    noise = np.sqrt(noise_ss / noise_df)
    noise_lo, noise_hi = ci_sd(noise_ss, noise_df)
    show("Zusammengelegt (maßgeblich)", noise_ss, noise_df)
    show("Zur Kontrolle: Rest des Gesamtmodells", fit["sd"] ** 2 * fit["df"], fit["df"])
    ratio = pair_ss / (long_ss / long_df)
    p_ratio = 2 * min(stats.f.sf(ratio, 1, long_df), stats.f.cdf(ratio, 1, long_df))
    print(f"  Beide Quellen verträglich? p = {p_ratio:.2f}. Bei kleinem p könnten Stints einen eigenen Zufall haben. Mit einer Differenz ist der Test schwach.")

    # Rundenbedarf für 50 Punkte
    costs = json.load(open(COSTS))
    print("\nRunden, um 50 Punkte sicher zu erkennen (5 % Fehlalarm, 90 % Trefferquote; Modellkurve aus simulator_data)")
    print("  Runden gesamt: mit geschätztem Zufall / mit oberer 95-%-Grenze des Zufalls")
    need = {}
    for s in POWER_PARAMS:
        c = costs["params"][s]
        dd = direct_delta(c["amp_s_lap"], c["w"])
        fd, k = flank_delta(c["amp_s_lap"], c["w"], ref["setup"][s])
        n_d, n_d_hi = 2 * laps_per_setting(noise, dd), 2 * laps_per_setting(noise_hi, dd)
        n_f, n_f_hi = 2 * laps_per_setting(noise, fd), 2 * laps_per_setting(noise_hi, fd)
        need[s] = {"direct_laps": n_d, "direct_laps_upper": n_d_hi, "flank_laps": n_f, "flank_laps_upper": n_f_hi, "flank_k": k}
        print(f"  {s:15} am Boden {dd:.2f} s: {n_d:4d} / {n_d_hi:4d}   an den Flanken +-{k} ({fd:.2f} s): {n_f:3d} / {n_f_hi:3d}")
    print("  Flanken: Setup -k und +k vergleichen; gleiche Zeit heißt, das Optimum liegt in der Mitte.")
    print("  Die Kosten addieren sich, also können mehrere Parameter in einem Versuchsplan gemeinsam laufen, ohne die Rundenzahl zu vervielfachen.")
    print("  Block 2 erst mit diesen Zahlen festlegen: Die Stintlänge richtet sich nach den Runden je Einstellung.")

    # Ist die erste Runde eines Stints anders?
    first_lap = (lap_in_stint == 0).to_numpy(float)
    alt = ols(np.c_[one, fuel, used, first_lap], t)
    if alt is not None:
        print(f"Effekt erste Stintrunde: {alt['b'][3]:+.3f} s  [{alt['lo'][3]:+.3f}; {alt['hi'][3]:+.3f}]")

    # Abgleich mit Vorhersage
    r = ref["lap_time_reference_s"]
    print(f"\nVorhersage aus simulator_data bei Abweichung 0: {r:.2f} s (Modellunsicherheit {ref['lap_time_reference_boot_sd_s']:.2f} s)")
    print(f"Grundzeit minus Vorhersage: {base - r:+.3f} s, Schätzfehler der Grundzeit durch den Rundenzufall: {fit['se'][0]:.3f} s")
    if per_l > 0:
        print(f"Gleiche Zeit ergäbe sich mit {(r - base) / per_l:.1f} l Sprit. Mit welchem Sprit simulator_data entstand, ist unbekannt.")

    json.dump({"source": path, "base_s": base, "fuel_penalty_s_per_l": per_l, "tyre_effect_s_per_pct": per_pct,
               "fuel_per_lap_l": fuel_per_lap, "wear_per_lap_pct": wear_per_lap, "lap_noise_sd_s": noise,
               "lap_noise_ci_s": [noise_lo, noise_hi], "lap_noise_df": noise_df, "laps_needed_50_points": need,
               "minus_reference_s": base - r}, open(OUT, "w"), indent=2)
    print("\nGeschrieben:", OUT)


if __name__ == "__main__":
    main()
