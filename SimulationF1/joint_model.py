"""Gemeinsames Modell: Rundenzeit je km = Streckenanteil + Summe der Kosten der Setup-Abweichungen.

Kosten je Parameter: A * (1 - exp(-r^2 / (2 w^2))), r = Setup minus auf 1 bis 500 begrenztes Optimum.
Optimum je Parameter: quadratisch in den schlanken Streckenmerkmalen.
Vergleicht "zweistufig" (Optimum aus den Setups, Tobit) mit "gemeinsam" (Optimum aus der Rundenzeit).
Lauf: python3 joint_model.py  (schreibt results/joint_*.json, Laufzeit einige Minuten)
"""
import json
import sys
import time

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from scipy.optimize import least_squares
from sklearn.linear_model import LassoCV
from sklearn.model_selection import KFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler

from tobit import Tobit, LOW, HIGH

SETUPS = ["Rear Wing", "Engine", "Front Wing", "Brake Balance", "Differential", "Suspension"]
TRACK = "Spain"
MIN_COEF = 5
SEED = 1
N_BOOT = 100
N_TRUTH = 6


FEATS_DIST = 0  # Lap Distance ist die erste Merkmalsspalte


def load():
    sim = pd.read_csv("simulator_data (1).csv")
    feats = [c for c in sim.columns if c not in SETUPS + ["Lap Time"]]
    tracks = pd.read_csv("track_data (1).csv")
    spain = tracks.loc[tracks["Track"] == TRACK, feats].to_numpy(float)
    return sim, feats, spain


def bell(r, w):
    return 1 - np.exp(-(r**2) / (2 * w**2))


class Basis:
    """Streckenanteil und Merkmale des Optimums, nur aus Trainingszeilen gelernt."""

    def __init__(self, X, V):
        self.g = make_pipeline(StandardScaler(), PolynomialFeatures(2, include_bias=False)).fit(X)
        self.opt = []
        self.theta0 = []
        for j in range(6):
            lasso = make_pipeline(StandardScaler(), LassoCV(cv=3, random_state=SEED)).fit(X, V[:, j])
            keep = np.abs(lasso[-1].coef_) >= MIN_COEF
            pipe = make_pipeline(StandardScaler(), PolynomialFeatures(2, include_bias=False), Tobit()).fit(X[:, keep], V[:, j])
            self.opt.append((keep, pipe))
            self.theta0.append(pipe[-1].coef_.copy())
        self.sizes = [len(t) for t in self.theta0]

    def Q(self, X):
        return np.c_[np.ones(len(X)), self.g.transform(X)]

    def Phi(self, X):
        out = []
        for keep, pipe in self.opt:
            z = pipe[:-1].transform(X[:, keep])
            out.append(np.c_[np.ones(len(z)), (z - pipe[-1].mean_) / pipe[-1].std_])
        return out


def mu_from(phi, theta):
    return np.column_stack([p @ t for p, t in zip(phi, theta)])


def fit_shape(Q, V, mu, y, log_w=None):
    """Streckenanteil und Amplituden linear, Breiten w per Suche; Optimum bleibt fest."""
    R = V - np.clip(mu, LOW, HIGH)

    def design(lw):
        return np.c_[Q, *[bell(R[:, j], np.exp(lw[j])) for j in range(6)]]

    if log_w is None:
        def res(lw):
            Z = design(lw)
            return y - Z @ np.linalg.lstsq(Z, y, rcond=None)[0]
        log_w = least_squares(res, np.log(np.full(6, 65.0)), diff_step=0.02, max_nfev=12).x
    Z = design(log_w)
    b = np.linalg.lstsq(Z, y, rcond=None)[0]
    return b[:-6], b[-6:], log_w


def fit_joint(Q, Phi, V, y, beta, amp, log_w, theta, max_nfev=40):
    """Schätzt alles gemeinsam (nichtlineare kleinste Quadrate mit exakter Ableitung)."""
    sizes = [len(t) for t in theta]
    nq = Q.shape[1]

    def unpack(p):
        th, i = [], nq + 12
        for s in sizes:
            th.append(p[i:i + s])
            i += s
        return p[:nq], p[nq:nq + 6], p[nq + 6:nq + 12], th

    def fun(p):
        be, a, lw, th = unpack(p)
        R = V - np.clip(mu_from(Phi, th), LOW, HIGH)
        return y - Q @ be - bell(R, np.exp(lw)) @ a

    def jac(p):
        be, a, lw, th = unpack(p)
        mu = mu_from(Phi, th)
        R = V - np.clip(mu, LOW, HIGH)
        w = np.exp(lw)
        e = np.exp(-(R**2) / (2 * w**2))
        cols = [-Q, -(1 - e), a * e * R**2 / w**2]
        inside = (mu > LOW) & (mu < HIGH)
        for j in range(6):  # Ableitung nach dem Optimum; außerhalb der Grenzen 0
            cols.append((a[j] * e[:, j] * R[:, j] / w[j] ** 2 * inside[:, j])[:, None] * Phi[j])
        return np.hstack(cols)

    p0 = np.r_[beta, amp, log_w, *theta]
    sol = least_squares(fun, p0, jac=jac, method="trf", tr_solver="exact", x_scale="jac", max_nfev=max_nfev)
    return unpack(sol.x)


def predict_y(Q, V, mu, beta, amp, log_w):
    R = V - np.clip(mu, LOW, HIGH)
    return Q @ beta + bell(R, np.exp(log_w)) @ amp


def fit_all(X, V, y):
    """Liefert beide Varianten auf denselben Daten."""
    basis = Basis(X, V)
    Q, Phi = basis.Q(X), basis.Phi(X)
    th0 = basis.theta0
    be, a, lw = fit_shape(Q, V, mu_from(Phi, th0), y)
    two = {"theta": th0, "beta": be, "amp": a, "log_w": lw}
    be2, a2, lw2, th2 = fit_joint(Q, Phi, V, y, be, a, lw, th0)
    joint = {"theta": th2, "beta": be2, "amp": a2, "log_w": lw2}
    return basis, two, joint


def run_fold(X, V, y, tr, te):
    basis, two, joint = fit_all(X[tr], V[tr], y[tr])
    Qtr, Phitr = basis.Q(X[tr]), basis.Phi(X[tr])
    Qte, Phite = basis.Q(X[te]), basis.Phi(X[te])
    mu2, muj = mu_from(Phite, two["theta"]), mu_from(Phite, joint["theta"])
    out = {"te": te, "mu_two": np.clip(mu2, LOW, HIGH), "mu_joint": np.clip(muj, LOW, HIGH)}
    out["e_two"] = y[te] - predict_y(Qte, V[te], mu2, two["beta"], two["amp"], two["log_w"])
    out["e_joint"] = y[te] - predict_y(Qte, V[te], muj, joint["beta"], joint["amp"], joint["log_w"])
    # Mittel aus beiden Optima, Form und Streckenanteil neu angepasst
    tr_mix = (mu_from(Phitr, two["theta"]) + mu_from(Phitr, joint["theta"])) / 2
    be, a, lw = fit_shape(Qtr, V[tr], tr_mix, y[tr], two["log_w"])
    out["e_mix"] = y[te] - predict_y(Qte, V[te], (mu2 + muj) / 2, be, a, lw)
    # Tausch: nur ein Parameter aus dem gemeinsamen Modell, gleiche Form und gleicher Streckenanteil
    swap = {}
    for j in range(6):
        tr_mu = mu_from(Phitr, two["theta"])
        tr_mu[:, j] = mu_from(Phitr, joint["theta"])[:, j]
        be, a, lw = fit_shape(Qtr, V[tr], tr_mu, y[tr], two["log_w"])
        te_mu = mu2.copy()
        te_mu[:, j] = muj[:, j]
        swap[j] = y[te] - predict_y(Qte, V[te], te_mu, be, a, lw)
    out["e_swap"] = swap
    return out


def boot_one(X, V, y, spain, seed):
    idx = np.random.default_rng(seed).integers(0, len(X), len(X))
    basis, two, joint = fit_all(X[idx], V[idx], y[idx])
    phi = basis.Phi(spain)
    d = spain[0, FEATS_DIST]
    Qs = basis.Q(spain)
    return mu_from(phi, two["theta"])[0], mu_from(phi, joint["theta"])[0], float((Qs @ joint["beta"])[0] * d)


def truth_one(X, y_fit, mu_true, sigma, noise, seed):
    """Erfundene Daten mit bekanntem Optimum: Welche Variante trifft es besser?"""
    rng = np.random.default_rng(seed)
    V = np.clip(np.round(mu_true + rng.normal(0, sigma, mu_true.shape)), LOW, HIGH)
    tr, te = next(KFold(5, shuffle=True, random_state=seed).split(X))
    Rt = V - np.clip(mu_true, LOW, HIGH)
    y = y_fit["base"] + bell(Rt, y_fit["w"]) @ y_fit["amp"] + rng.normal(0, noise, len(X))
    basis, two, joint = fit_all(X[tr], V[tr], y[tr])
    phi = basis.Phi(X[te])
    truth = np.clip(mu_true[te], LOW, HIGH)
    return (np.abs(np.clip(mu_from(phi, two["theta"]), LOW, HIGH) - truth).mean(0),
            np.abs(np.clip(mu_from(phi, joint["theta"]), LOW, HIGH) - truth).mean(0))


if __name__ == "__main__":
    sim, feats, spain = load()
    X = sim[feats].to_numpy(float)
    V = sim[SETUPS].to_numpy(float)
    d = sim["Lap Distance"].to_numpy(float)
    y = sim["Lap Time"].to_numpy(float) / d
    t0 = time.time()
    folds = list(KFold(5, shuffle=True, random_state=SEED).split(X))
    res = Parallel(n_jobs=5)(delayed(run_fold)(X, V, y, tr, te) for tr, te in folds)
    print(f"Folds fertig nach {time.time() - t0:.0f} s", flush=True)
    basis, two, joint = fit_all(X, V, y)
    phi = basis.Phi(spain)
    pred_two, pred_joint = mu_from(phi, two["theta"])[0], mu_from(phi, joint["theta"])[0]
    boot = Parallel(n_jobs=6)(delayed(boot_one)(X, V, y, spain, SEED + 100 + i) for i in range(N_BOOT))
    print(f"Bootstrap fertig nach {time.time() - t0:.0f} s", flush=True)

    fit_mu = mu_from(basis.Phi(X), joint["theta"])
    truth_fit = {"base": basis.Q(X) @ joint["beta"], "amp": joint["amp"], "w": np.exp(joint["log_w"])}
    sigma = np.array([pipe[-1].sigma_ for _, pipe in basis.opt])
    noise = float(np.sqrt(np.mean((y - predict_y(basis.Q(X), V, fit_mu, joint["beta"], joint["amp"], joint["log_w"])) ** 2)))
    truth = Parallel(n_jobs=6)(delayed(truth_one)(X, truth_fit, fit_mu, sigma, noise, 500 + i) for i in range(N_TRUTH))
    print(f"Wahrheitsprobe fertig nach {time.time() - t0:.0f} s", flush=True)
    te = np.concatenate([r["te"] for r in res])
    def stack(k):
        return np.concatenate([r[k] for r in res])
    e2, ej, em = stack("e_two"), stack("e_joint"), stack("e_mix")
    mt, mj = stack("mu_two"), stack("mu_joint")
    Vt = V[te]
    Xt = pd.DataFrame(X[te], columns=feats)
    near = ((Xt["Cornering"] >= 80) & (Xt["Width"] <= 30)).to_numpy()
    swap = {SETUPS[j]: np.concatenate([r["e_swap"][j] for r in res]) for j in range(6)}
    rmse = lambda e: float(np.sqrt((e**2).mean()))
    out = {
        "rows_near_spain": int(near.sum()),
        "rmse_s_km": {"zweistufig": rmse(e2), "gemeinsam": rmse(ej), "mittel": rmse(em)},
        "rmse_s_km_near_spain": {"zweistufig": rmse(e2[near]), "gemeinsam": rmse(ej[near]), "mittel": rmse(em[near])},
        "r2": {k: float(1 - (v**2).sum() / ((y[te] - y.mean()) ** 2).sum()) for k, v in {"zweistufig": e2, "gemeinsam": ej, "mittel": em}.items()},
        "fold_rmse": {"zweistufig": [rmse(r["e_two"]) for r in res], "gemeinsam": [rmse(r["e_joint"]) for r in res]},
        "per_param": {},
    }
    resid_sec = (e2 * d[te])[d[te] >= 4.8]
    out["resid_sd_s_long"] = {"zweistufig": float(resid_sec.std()), "gemeinsam": float((ej * d[te])[d[te] >= 4.8].std())}
    bt = np.array([b[0] for b in boot])
    bj = np.array([b[1] for b in boot])
    out["spain_lap_time_boot_sd_s"] = float(np.std([b[2] for b in boot], ddof=1))
    out["fit_noise_s_km"] = noise
    out["truth_mae"] = {"zweistufig": dict(zip(SETUPS, np.mean([t[0] for t in truth], 0).tolist())), "gemeinsam": dict(zip(SETUPS, np.mean([t[1] for t in truth], 0).tolist()))}
    for j, s in enumerate(SETUPS):
        out["per_param"][s] = {
            "mae_setup_two": float(np.abs(mt[:, j] - Vt[:, j]).mean()),
            "mae_setup_joint": float(np.abs(mj[:, j] - Vt[:, j]).mean()),
            "mae_setup_two_near": float(np.abs(mt[near, j] - Vt[near, j]).mean()),
            "mae_setup_joint_near": float(np.abs(mj[near, j] - Vt[near, j]).mean()),
            "rmse_swap": rmse(swap[s]), "swap_mse_gain_folds": [float((r["e_two"]**2).mean() - (r["e_swap"][j]**2).mean()) for r in res],
            "rmse_swap_near": rmse(swap[s][near]),
            "spain_two_latent": float(pred_two[j]),
            "spain_joint_latent": float(pred_joint[j]),
            "spain_two": float(np.clip(pred_two[j], LOW, HIGH)),
            "spain_joint": float(np.clip(pred_joint[j], LOW, HIGH)),
            "boot_two_sd": float(np.clip(bt[:, j], LOW, HIGH).std(ddof=1)),
            "boot_joint_sd": float(np.clip(bj[:, j], LOW, HIGH).std(ddof=1)),
            "boot_two_5_95": [float(v) for v in np.percentile(np.clip(bt[:, j], LOW, HIGH), [5, 95])],
            "boot_joint_5_95": [float(v) for v in np.percentile(np.clip(bj[:, j], LOW, HIGH), [5, 95])],
            "amp_s_km": float(joint["amp"][j]),
            "w": float(np.exp(joint["log_w"][j])),
            "amp_two_s_km": float(two["amp"][j]),
            "w_two": float(np.exp(two["log_w"][j])),
        }
    # Referenz-Rundenzeit Spanien
    Qs = basis.Q(spain)
    out["spain_lap_time_s"] = {"zweistufig": float((Qs @ two["beta"])[0] * spain[0, feats.index("Lap Distance")]),
                               "gemeinsam": float((Qs @ joint["beta"])[0] * spain[0, feats.index("Lap Distance")])}
    json.dump(out, open("results/joint_model.json", "w"), indent=1, ensure_ascii=False)
    np.savez("results/joint_cost_data.npz", y=y, V=V, mu_two=mu_from(basis.Phi(X), two["theta"]), mu_joint=mu_from(basis.Phi(X), joint["theta"]),
             Q=basis.Q(X), beta_joint=joint["beta"], amp_joint=joint["amp"], logw_joint=joint["log_w"], beta_two=two["beta"], amp_two=two["amp"], logw_two=two["log_w"])
    print(json.dumps({k: out[k] for k in ["rows_near_spain", "rmse_s_km", "rmse_s_km_near_spain", "r2", "fold_rmse", "resid_sd_s_long", "spain_lap_time_s", "spain_lap_time_boot_sd_s", "truth_mae"]}))
    for s, v in out["per_param"].items():
        print(s, {k: (round(x, 4) if isinstance(x, float) else [round(i, 6) for i in x]) for k, x in v.items()})
    print(f"Fertig nach {time.time() - t0:.0f} s")
