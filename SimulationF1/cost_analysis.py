"""Punkt 1: Form der Kostenkurve, Grafik, Kosten der Unsicherheit, Rundenbedarf.

Liest results/joint_model.json und results/joint_cost_data.npz (aus joint_model.py).
Schreibt results/cost_curves.png, results/cost_report.md, results/cost_curves.json, results/spain_prediction.json.
"""
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np
import pandas as pd
from scipy.optimize import least_squares
from sklearn.model_selection import KFold

from power import direct_delta, flank_delta, laps_per_setting
from tobit import Tobit, LOW, HIGH
from sklearn.linear_model import LassoCV
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

SETUPS = ["Rear Wing", "Engine", "Front Wing", "Brake Balance", "Differential", "Suspension"]
FOCUS = ["Brake Balance", "Differential"]
TEXT, MUTED, GRID, SURFACE, BLUE, ORANGE = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb", "#2a78d6", "#eb6834"

J = json.load(open("results/joint_model.json"))
T = json.load(open("results/spain_prediction_tobit.json"))
D = np.load("results/joint_cost_data.npz")
sim = pd.read_csv("simulator_data (1).csv")
tracks = pd.read_csv("track_data (1).csv")
feats = [c for c in sim.columns if c not in SETUPS + ["Lap Time"]]
spain = tracks[tracks.Track == "Spain"]
KM, LAPS = float(spain["Lap Distance"].iloc[0]), int(spain["N. Laps"].iloc[0])
y, V, Q = D["y"], D["V"], D["Q"]
R = V - np.clip(D["mu_joint"], LOW, HIGH)
amp, w = D["amp_joint"], np.exp(D["logw_joint"])
P = J["per_param"]


def bell(r, wj):
    return 1 - np.exp(-(r**2) / (2 * wj**2))


H = np.column_stack([amp[j] * bell(R[:, j], w[j]) for j in range(6)])
base = Q @ D["beta_joint"]
folds = list(KFold(5, shuffle=True, random_state=1).split(Q))

# Formvergleich je Parameter: nur dieser Parameter bekommt die andere Form, die übrigen bleiben Glocke
FORMS = {"gleichmäßig (V)": lambda r, _: np.abs(r), "quadratisch": lambda r, _: r**2 / 1e4, "sättigend (Glocke)": bell}
form_rows, asym_rows = [], []
for j, s in enumerate(SETUPS):
    row = [s]
    for name, f in FORMS.items():
        mse = 0.0
        for tr, te in folds:
            others = [i for i in range(6) if i != j]
            Z = np.c_[Q, H[:, others], f(R[:, j], w[j])]
            b = np.linalg.lstsq(Z[tr], y[tr], rcond=None)[0]
            mse += ((y[te] - Z[te] @ b) ** 2).sum()
        row.append(f"{np.sqrt(mse / len(y)):.5f}")
    form_rows.append(row)
    others = [i for i in range(6) if i != j]
    Z = np.c_[Q, H[:, others], bell(R[:, j], w[j]) * (R[:, j] < 0), bell(R[:, j], w[j]) * (R[:, j] > 0)]
    b = np.linalg.lstsq(Z, y, rcond=None)[0]
    asym_rows.append([s, f"{b[-2] * KM:.2f}", f"{b[-1] * KM:.2f}"])

# Grafik -------------------------------------------------------------------------------------------
plt.rcParams.update({"font.family": "Helvetica Neue", "font.size": 10, "text.color": TEXT, "axes.edgecolor": GRID,
                     "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED})
fig, axes = plt.subplots(2, 3, figsize=(11, 6.6), sharex=True, sharey=True, facecolor=SURFACE)
x = np.linspace(-260, 260, 521)
edges = np.arange(-260, 261, 20)
for j, (s, ax) in enumerate(zip(SETUPS, axes.ravel())):
    others = [i for i in range(6) if i != j]
    partial = (y - base - H[:, others].sum(1)) * KM
    a_lap, wj = amp[j] * KM, w[j]
    mid, mean, ci = [], [], []
    for lo, hi in zip(edges, edges[1:]):
        m = (R[:, j] >= lo) & (R[:, j] < hi) & (R[:, j] != 0)
        if m.sum() >= 30:
            mid.append((lo + hi) / 2)
            mean.append(partial[m].mean())
            ci.append(1.96 * partial[m].std() / np.sqrt(m.sum()))
    ax.set_facecolor(SURFACE)
    ax.grid(True, color=GRID, linewidth=0.7)
    ax.set_axisbelow(True)
    ax.plot(x, a_lap * bell(x, wj), color=BLUE, linewidth=2, label="Glocke (bestes Modell)", zorder=2)
    ax.plot(x, a_lap * x**2 / (2 * wj**2), color=ORANGE, linewidth=2, linestyle=(0, (4, 3)), label="Quadratisch, gleiche Krümmung bei 0", zorder=2)
    ax.errorbar(mid, mean, yerr=ci, fmt="o", markersize=4, color=TEXT, ecolor=MUTED, elinewidth=1, label="Daten: Mittel je 20 Punkte, 95 %", zorder=3)
    ax.set_ylim(-0.15, 1.45)
    ax.set_xlim(-260, 260)
    ax.set_title(f"{s}: 50 Punkte = {a_lap * bell(50, wj):.2f} s, höchstens {a_lap:.2f} s".replace(".", ","), loc="left", fontsize=10.5, color=TEXT)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.2f}".replace(".", ",")))
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
for ax in axes[1]:
    ax.set_xlabel("Abweichung vom Optimum (Setup-Punkte)")
for ax in axes[:, 0]:
    ax.set_ylabel(f"Zeitverlust je Runde in s ({KM} km)".replace(".", ","))
handles, labels = axes[0, 0].get_legend_handles_labels()
fig.legend(handles, labels, loc="upper left", bbox_to_anchor=(0.055, 0.915), ncol=3, frameon=False, fontsize=10)
fig.suptitle("Nahe am Optimum quadratisch, ab etwa 100 Punkten flacht der Zeitverlust ab", x=0.06, ha="left", fontsize=14, color=TEXT, y=0.975)
fig.tight_layout(rect=(0, 0, 1, 0.89))
fig.savefig("results/cost_curves.png", dpi=160)

# Lokale Gegenprobe nahe Spanien -------------------------------------------------------------------
X = sim[feats].to_numpy(float)
near = (sim["Cornering"] >= 80) & (sim["Width"] <= 30)
local = {}
for s in SETUPS:
    t = sim[s].to_numpy(float)
    las = make_pipeline(StandardScaler(), LassoCV(cv=3, random_state=1)).fit(X, t)
    keep = np.abs(las[-1].coef_) >= 5
    m = make_pipeline(StandardScaler(), Tobit()).fit(X[near][:, keep], t[near])
    local[s] = float(np.clip(m.predict(spain[feats].to_numpy(float)[:, keep])[0], LOW, HIGH))

# Kosten der Unsicherheit ---------------------------------------------------------------------------
rng = np.random.default_rng(1)
final = {s: int(round(P[s]["spain_joint"])) for s in SETUPS}
cost_rows, un = [], {}
for j, s in enumerate(SETUPS):
    a_lap, wj, v = amp[j] * KM, w[j], P[s]["spain_joint"]
    sd = P[s]["boot_joint_sd"]
    expected = (a_lap * bell(rng.normal(0, sd, 200000), wj)).mean() * LAPS if sd > 0 else 0.0
    alt = {"zweistufig": P[s]["spain_two"], "lokal": local[s], "Tobit einfach": T["spain_by_model"]["Tobit schlank"][s], "GB": T["spain_by_model"]["Gradient Boosting"][s]}
    cost_alt = {k: float(a_lap * bell(q - v, wj) * LAPS) for k, q in alt.items()}
    un[s] = {"sd": sd, "expected_s": expected, "alt": alt, "cost_alt_s": cost_alt}
    cost_rows.append([s, final[s], f"{sd:.0f}", f"{expected:.2f}"] + [f"{alt[k]:.0f} ({cost_alt[k]:.1f} s)" for k in alt])

# Rundenbedarf für verschiedene Zufallsgrößen -------------------------------------------------------
sigmas = [0.05, 0.1, 0.2, 0.3, 0.4]
power_rows = []
info = {}
for s in FOCUS:
    j = SETUPS.index(s)
    a_lap, wj = amp[j] * KM, w[j]
    dd = direct_delta(a_lap, wj)
    fd, k = flank_delta(a_lap, wj, P[s]["spain_joint"])
    info[s] = {"amp_s_lap": float(a_lap), "w": float(wj), "direct_delta_s": dd, "flank_delta_s": fd, "flank_k": k}
    for sg in sigmas:
        power_rows.append([s, f"{sg:.2f}", laps_per_setting(sg, dd) * 2, laps_per_setting(sg, fd) * 2])

fmt = lambda v: f"{v:.5f}"
o = ["# Kosten der Setup-Abweichung\n\nErzeugt von `cost_analysis.py`. Grafik: `results/cost_curves.png`.\n"]
o.append("\n## Form je Parameter\n\nKreuzvalidierte RMSE der Zeit je km; nur dieser Parameter bekommt die jeweilige Form.\n\n")
head = ["Parameter"] + list(FORMS)
o.append("| " + " | ".join(head) + " |\n|" + "---|" * len(head) + "\n" + "".join("| " + " | ".join(map(str, r)) + " |\n" for r in form_rows))
o.append(f"\n## Symmetrie\n\nGrenze der Kurve (s je Runde, {KM} km) links und rechts des Optimums.\n\n| Parameter | links | rechts |\n|---|---|---|\n" + "".join("| " + " | ".join(r) + " |\n" for r in asym_rows))
o.append(f"\n## Kosten der Unsicherheit über {LAPS} Runden\n\nErwartung: Bootstrap-Streuung um den Modellwert. Spalten dahinter: anderes Schätzverfahren und Zeitverlust, falls dieses recht hätte.\n\n")
h2 = ["Parameter", "Wert gemeinsam", "Bootstrap Std.", "Erwartet (s/Rennen)", "zweistufig", "lokal nahe Spanien", "Tobit einfach", "GB"]
o.append("| " + " | ".join(h2) + " |\n|" + "---|" * len(h2) + "\n" + "".join("| " + " | ".join(map(str, r)) + " |\n" for r in cost_rows))
o.append(f"\nGesamt erwartet über alle sechs: {sum(u['expected_s'] for u in un.values()):.1f} s/Rennen.\n")
o.append("\n## Runden für 50 Punkte (5 % Fehlalarm, 90 % Trefferquote), gesamt für den Vergleich zweier Einstellungen\n\n| Parameter | Zufall je Runde (s) | am Boden: Optimum gegen +50 | Flanken: -k gegen +k |\n|---|---|---|---|\n" + "".join("| " + " | ".join(map(str, r)) + " |\n" for r in power_rows))
o.append("\nFlanken-Parameter: " + "; ".join(f"{s}: k = {v['flank_k']}, Unterschied {v['flank_delta_s']:.2f} s statt {v['direct_delta_s']:.2f} s" for s, v in info.items()) + ".\n")
o.append(f"\nObergrenze aus `simulator_data` (Rest des gemeinsamen Modells bei langen Strecken): {J['resid_sd_s_long']['gemeinsam']:.2f} s. Das enthält auch Modellfehler; den echten Zufall misst erst Block 1.\n")
open("results/cost_report.md", "w").write("".join(o))
json.dump({"params": {s: {"amp_s_lap": float(amp[j] * KM), "w": float(w[j])} for j, s in enumerate(SETUPS)}, "focus": info,
           "noise_upper_bound_s": J["resid_sd_s_long"]["gemeinsam"], "laps_in_race": LAPS}, open("results/cost_curves.json", "w"), indent=1, ensure_ascii=False)
json.dump({"track": "Spain", "round": int(spain["Round"].iloc[0]), "lap_distance_km": KM, "n_laps": LAPS, "method": "gemeinsames Modell (joint_model.py)",
           "setup": final, "lap_time_reference_s": round(J["spain_lap_time_s"]["gemeinsam"], 2), "lap_time_reference_boot_sd_s": round(J["spain_lap_time_boot_sd_s"], 2)},
          open("results/spain_prediction.json", "w"), indent=1, ensure_ascii=False)
print("".join(o))
print(final)
