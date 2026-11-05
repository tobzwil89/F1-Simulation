"""Aufgabe 1: optimales Setup und Referenz-Rundenzeit für Spanien vorhersagen.

Liest simulator_data und track_data. Schreibt results/setup_model_report.md und
results/spain_prediction_tobit.json. Lauf: python3 setup_model.py (etwa 3 bis 10 Minuten)
"""
import json
import warnings

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin, TransformerMixin, clone
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LassoCV, LinearRegression
from sklearn.model_selection import KFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures, SplineTransformer, StandardScaler

from tobit import Tobit

warnings.filterwarnings("ignore", category=UserWarning)

SIM_FILE = "simulator_data (1).csv"
TRACK_FILE = "track_data (1).csv"
TRACK = "Spain"
SETUPS = ["Rear Wing", "Engine", "Front Wing", "Brake Balance", "Differential", "Suspension"]
LOW, HIGH = 1, 500
SEED = 1
MIN_COEF = 5  # Merkmal zählt, wenn 1 Standardabweichung den Setup-Wert um mindestens 5 Punkte verschiebt
SIMPLER_IF_WITHIN = 0.5  # einfacheres Modell gewinnt, wenn sein Fehler höchstens so viel schlechter ist
N_BOOT = 100


class LassoSelect(BaseEstimator, TransformerMixin):
    """Behält nur Merkmale mit genügend großem Lasso-Koeffizienten (in jedem Fold neu)."""

    def fit(self, X, y):
        lasso = make_pipeline(StandardScaler(), LassoCV(cv=3, random_state=SEED)).fit(X, y)
        self.keep_ = np.abs(lasso[-1].coef_) >= MIN_COEF
        return self

    def transform(self, X):
        return np.asarray(X)[:, self.keep_]


class InteriorOnly(BaseEstimator, RegressorMixin):
    """Lernt nur aus Zeilen, die nicht an einer Grenze liegen."""

    def __init__(self, model):
        self.model = model

    def fit(self, X, y):
        y = np.asarray(y)
        keep = (y > LOW) & (y < HIGH)
        self.fitted_ = clone(self.model).fit(np.asarray(X)[keep], y[keep])
        return self

    def predict(self, X):
        return self.fitted_.predict(np.asarray(X))


def gb():
    return HistGradientBoostingRegressor(learning_rate=0.05, max_iter=300, max_leaf_nodes=15,
                                         min_samples_leaf=30, random_state=SEED)


def quad():
    return [StandardScaler(), PolynomialFeatures(2, include_bias=False)]


MODELS = {
    "Linear": lambda: LinearRegression(),
    "Lasso": lambda: make_pipeline(StandardScaler(), LassoCV(cv=3, random_state=SEED)),
    "Quadratisch": lambda: make_pipeline(*quad(), LinearRegression()),
    "Gradient Boosting": gb,
    "Linear schlank": lambda: make_pipeline(LassoSelect(), LinearRegression()),
    "Tobit": lambda: Tobit(),
    "Tobit schlank": lambda: make_pipeline(LassoSelect(), Tobit()),
    "Tobit quadratisch": lambda: make_pipeline(*quad(), Tobit()),
    "Tobit quadr. schlank": lambda: make_pipeline(LassoSelect(), *quad(), Tobit()),
    "Linear nur Innenzeilen": lambda: InteriorOnly(LinearRegression()),
    "GB nur Innenzeilen": lambda: InteriorOnly(gb()),
}
# Wahl nur unter Modellen, die das Abschneiden berücksichtigen oder frei anpassen; einfachste zuerst
CANDIDATES = ["Tobit schlank", "Tobit", "Tobit quadr. schlank", "Tobit quadratisch", "Gradient Boosting"]


def table(rows, head):
    lines = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    lines += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(lines) + "\n"


sim = pd.read_csv(SIM_FILE)
tracks = pd.read_csv(TRACK_FILE)
FEATURES = [c for c in sim.columns if c not in SETUPS + ["Lap Time"]]
spain_row = tracks[tracks["Track"] == TRACK]
assert len(spain_row) == 1
spain = spain_row[FEATURES].astype(float)
X = sim[FEATURES].astype(float)
folds = KFold(5, shuffle=True, random_state=SEED)
fold_ids = np.zeros(len(sim), int)
for i, (_, test) in enumerate(folds.split(X)):
    fold_ids[test] = i

mae, mae_in, mae_bd, fold_sd, oof, spain_pred = {}, {}, {}, {}, {}, {}
for name, build in MODELS.items():
    print("Modell:", name, flush=True)
    for s in SETUPS:
        y = sim[s].values
        p = cross_val_predict(build(), X, y, cv=folds)
        clipped = np.clip(p, LOW, HIGH)
        err = np.abs(clipped - y)
        inside = (y > LOW) & (y < HIGH)
        mae[name, s], mae_in[name, s], mae_bd[name, s] = err.mean(), err[inside].mean(), err[~inside].mean()
        fold_sd[name, s] = np.std([err[fold_ids == k].mean() for k in range(5)], ddof=1)
        oof[name, s] = clipped
        spain_pred[name, s] = float(np.clip(build().fit(X, y).predict(spain)[0], LOW, HIGH))

chosen = {}
for s in SETUPS:
    best = min(mae[m, s] for m in CANDIDATES)
    chosen[s] = next(m for m in CANDIDATES if mae[m, s] <= best + SIMPLER_IF_WITHIN)

print("Wichtigkeiten", flush=True)
imp_rows, lasso_rows, slim_sets = [], [], {}
for s in SETUPS:
    y = sim[s].values
    lasso = make_pipeline(StandardScaler(), LassoCV(cv=5, random_state=SEED)).fit(X, y)
    coef = pd.Series(lasso[-1].coef_, FEATURES)
    imp = pd.Series(0.0, FEATURES)
    for train, test in folds.split(X):
        m = gb().fit(X.iloc[train], y[train])
        imp += permutation_importance(m, X.iloc[test], y[test], scoring="neg_mean_absolute_error",
                                      n_repeats=3, random_state=SEED).importances_mean / 5
    slim_sets[s] = coef[coef.abs() >= MIN_COEF].index.tolist()
    lasso_rows.append([s] + [f"{coef[f]:+.0f}" if abs(coef[f]) >= 0.5 else "0" for f in FEATURES])
    imp_rows.append([s] + [f"{imp[f]:.1f}" for f in FEATURES])

print("Unsicherheit", flush=True)
rng = np.random.default_rng(SEED)
final, unc_rows = {}, []
for s in SETUPS:
    y = sim[s].values
    build = MODELS[chosen[s]]
    pred = spain_pred[chosen[s], s]
    boot = []
    for _ in range(N_BOOT):
        idx = rng.integers(0, len(sim), len(sim))
        boot.append(np.clip(build().fit(X.iloc[idx], y[idx]).predict(spain)[0], LOW, HIGH))
    near = np.abs(oof[chosen[s], s] - pred) <= 40
    local = y[near]
    final[s] = int(round(pred))
    spread = [spain_pred[m, s] for m in CANDIDATES]
    latent = make_pipeline(LassoSelect(), Tobit()).fit(X, y).predict(spain)[0]
    unc_rows.append([s, final[s], chosen[s], f"{latent:.0f}", f"{min(spread):.0f} bis {max(spread):.0f}", f"{mae[chosen[s], s]:.1f}", f"{np.abs(local - oof[chosen[s], s][near]).mean():.1f}",
                     f"{np.percentile(local, 10):.0f} bis {np.percentile(local, 90):.0f}",
                     f"{np.percentile(boot, 5):.0f} bis {np.percentile(boot, 95):.0f}", f"{(local <= LOW).mean() + (local >= HIGH).mean():.0%}"])

# Rundenzeit --------------------------------------------------------------------------------------
print("Rundenzeit", flush=True)
T = sim["Lap Time"].values
dist = sim["Lap Distance"].values
y_km = T / dist
dev = pd.DataFrame({s: sim[s].values - oof[chosen[s], s] for s in SETUPS})


def spline_block(values, fitted=None):
    """Glatte Kurve für die Abweichung je Setup-Wert."""
    v = np.clip(values, -250, 250)
    fitted = fitted or SplineTransformer(n_knots=7, degree=3, include_bias=False).fit(np.linspace(-250, 250, 501).reshape(-1, 1))
    return np.column_stack([fitted.transform(v[:, [j]]) for j in range(v.shape[1])]), fitted


time_rows = []
pkm = {}
scale = make_pipeline(StandardScaler(), PolynomialFeatures(2, include_bias=False)).fit(X)
Q = scale.transform(X)
Qs = scale.transform(spain)
D, spl = spline_block(dev.values)
Ds, _ = spline_block(np.zeros((1, 6)), spl)
d_s = float(spain["Lap Distance"].iloc[0])


def report_time(label, model, Xfit, Xs, per_km):
    target = y_km if per_km else T
    p = cross_val_predict(model(), Xfit, target, cv=folds)
    sec = p * dist if per_km else p
    s_pred = model().fit(Xfit, target).predict(Xs)[0] * (d_s if per_km else 1)
    time_rows.append([label, f"{np.abs(sec - T).mean():.3f}", f"{np.std(sec - T):.3f}", f"{s_pred:.2f}"])
    return s_pred, np.std(sec - T)


report_time("Linear", LinearRegression, X.values, spain.values, False)
report_time("Lasso", lambda: make_pipeline(StandardScaler(), LassoCV(cv=3, random_state=SEED)), X.values, spain.values, False)
report_time("Quadratisch", lambda: make_pipeline(*quad(), LinearRegression()), X.values, spain.values, False)
report_time("Gradient Boosting", gb, X.values, spain.values, False)
track_only, track_sd = report_time("Quadratisch auf s/km", LinearRegression, Q, Qs, True)
no_dev, dev_sd = report_time("Quadratisch auf s/km + Setup-Abweichung (Referenz bei Abweichung 0)", LinearRegression, np.c_[Q, D], np.c_[Qs, Ds], True)

# Kosten einer Abweichung: Kurve aus dem Modell mit Abweichung
cost_model = LinearRegression().fit(np.c_[Q, D], y_km)
coef_dev = cost_model.coef_[Q.shape[1]:]
n_basis = D.shape[1] // 6
grid = [-150, -100, -50, 0, 50, 100, 150]
Bg = spl.transform(np.array(grid, float).reshape(-1, 1))
cost_rows = []
for j, s in enumerate(SETUPS):
    curve = Bg @ coef_dev[j * n_basis:(j + 1) * n_basis]
    curve = (curve - curve[3]) * d_s
    fine = np.arange(-200, 201, 5.0)
    fine_curve = spl.transform(fine.reshape(-1, 1)) @ coef_dev[j * n_basis:(j + 1) * n_basis]
    cost_rows.append([s] + [f"{c:+.2f}" for c in curve] + [f"{fine[fine_curve.argmin()]:+.0f}"])

r2 = lambda p: 1 - ((y_km - p) ** 2).sum() / ((y_km - y_km.mean()) ** 2).sum()
r2_track = r2(cross_val_predict(LinearRegression(), Q, y_km, cv=folds))
r2_dev = r2(cross_val_predict(LinearRegression(), np.c_[Q, D], y_km, cv=folds))

# Bericht -----------------------------------------------------------------------------------------
fmt = lambda d, m, s: f"{d[m, s]:.1f}"
o = [f"# Setup-Modell {TRACK}\n\nErzeugt von `setup_model.py`. 5-fache Kreuzvalidierung, gleiche Folds für alle Modelle. Vorhersagen auf {LOW} bis {HIGH} begrenzt.\n"]
o.append("\n## Vorhersage\n\n" + table(unc_rows, ["Setup", "Wert", "Modell", "Tobit schlank vor Begrenzung", "Spanne der 5 Kandidaten", "MAE gesamt", "MAE nahe dieser Vorhersage", "80 % der verrauschten Datenwerte nahe dieser Vorhersage", "90 % Bootstrap der Vorhersage", "Anteil an Grenze nahe dieser Vorhersage"]))
o.append("\nDie beiden Spannen messen Verschiedenes: Die Datenspanne enthält das Rauschen der Trainingsdaten. Die Bootstrap-Spanne zeigt, wie genau das Modell den mittleren Wert trifft.\n")
o.append("\n## MAE je Parameter und Modell (alle Zeilen)\n\n" + table([[m] + [fmt(mae, m, s) for s in SETUPS] for m in MODELS], ["Modell"] + SETUPS))
o.append("\nStandardabweichung des MAE über die 5 Folds: " + ", ".join(f"{s} {fold_sd['Linear', s]:.1f}" for s in SETUPS) + " (Modell Linear).\n")
o.append("\n## Abschneiden: MAE auf Innenzeilen / Grenzzeilen\n\n" + table([[m] + [f"{mae_in[m, s]:.1f} / {mae_bd[m, s]:.1f}" for s in SETUPS] for m in MODELS], ["Modell"] + SETUPS))
o.append("\n## Spanien je Modell\n\n" + table([[m] + [f"{spain_pred[m, s]:.0f}" for s in SETUPS] for m in MODELS], ["Modell"] + SETUPS))
o.append("\n## Lasso-Koeffizienten\n\nSetup-Punkte je Standardabweichung des Merkmals.\n\n" + table(lasso_rows, ["Setup"] + FEATURES))
o.append("\n## Permutations-Wichtigkeit (Gradient Boosting)\n\nAnstieg des MAE in Punkten, wenn das Merkmal gemischt wird, auf den Test-Folds.\n\n" + table(imp_rows, ["Setup"] + FEATURES))
o.append(f"\n## Schlanke Merkmalssätze (Lasso, Betrag mindestens {MIN_COEF})\n\n" + table([[s, len(v), ", ".join(v)] for s, v in slim_sets.items()], ["Setup", "Anzahl", "Merkmale"]))
never = [f for f in FEATURES if not any(f in v for v in slim_sets.values())]
o.append(f"\nIn keinem Satz: {', '.join(never) or 'keins'}.\n")
o.append("\n## Rundenzeit Spanien\n\n" + table(time_rows, ["Modell", "MAE (s)", "Std.-Abw. Fehler (s)", f"{TRACK} (s)"]))
o.append(f"\n## Kosten einer Abweichung vom vorhergesagten Setup\n\nKreuzvalidiertes R² der Zeit je km: nur Strecke {r2_track:.3f}, mit Setup-Abweichung {r2_dev:.3f}. Zeitverlust in Sekunden pro Runde auf {TRACK} ({d_s} km) gegenüber Abweichung 0:\n\n" + table(cost_rows, ["Setup"] + [f"{g:+d}" for g in grid] + ["Minimum der Kurve bei"]))
o.append("\n## Sind die Setups nach Abzug der Strecke unabhängig?\n\nKorrelation der Abweichungen untereinander, größter Betrag: " + f"{np.abs(np.triu(dev.corr().values, 1)).max():.3f}.\n")
open("results/setup_model_report.md", "w").write("".join(o))

spain_by_model = {m: {s: round(spain_pred[m, s]) for s in SETUPS} for m in MODELS}
json.dump({"spain_by_model": spain_by_model, "track": TRACK, "round": int(spain_row["Round"].iloc[0]), "lap_distance_km": d_s, "n_laps": int(spain_row["N. Laps"].iloc[0]),
           "setup": final, "lap_time_reference_s": round(float(no_dev), 2), "lap_time_reference_sd_s": round(float(dev_sd), 2),
           "lap_time_track_only_s": round(float(track_only), 2)},
          open("results/spain_prediction_tobit.json", "w"), indent=2, ensure_ascii=False)
print(json.dumps(final), round(no_dev, 2), round(track_only, 2))
