"""Regression für beidseitig abgeschnittene Werte, gemeinsam genutzt."""
import numpy as np
from scipy.optimize import minimize
from scipy.stats import norm
from sklearn.base import BaseEstimator, RegressorMixin

LOW, HIGH = 1, 500


class Tobit(BaseEstimator, RegressorMixin):
    """Lineare Regression für beidseitig abgeschnittene Werte (Maximum Likelihood)."""

    def fit(self, X, y):
        X = np.asarray(X, float)
        y = np.asarray(y, float)
        self.mean_, self.std_ = X.mean(0), X.std(0)
        Z = np.c_[np.ones(len(X)), (X - self.mean_) / self.std_]
        lo, hi = y <= LOW, y >= HIGH
        mid = ~(lo | hi)

        def loss(p):
            b, log_s = p[:-1], p[-1]
            s = np.exp(log_s)
            mu = Z @ b
            r = (y[mid] - mu[mid]) / s
            zl = (LOW - mu[lo]) / s
            zh = (HIGH - mu[hi]) / s
            log_cdf, log_sf = norm.logcdf(zl), norm.logsf(zh)
            hl = np.exp(norm.logpdf(zl) - log_cdf)
            hh = np.exp(norm.logpdf(zh) - log_sf)
            grad_b = (Z[mid].T @ r - Z[lo].T @ hl + Z[hi].T @ hh) / s
            grad_s = (r**2 - 1).sum() - (hl * zl).sum() + (hh * zh).sum()
            value = (-0.5 * r**2 - log_s).sum() + log_cdf.sum() + log_sf.sum()
            return -value, -np.r_[grad_b, grad_s]

        start = np.r_[np.linalg.lstsq(Z, y, rcond=None)[0], np.log(y.std())]
        res = minimize(loss, start, jac=True, method="L-BFGS-B", options={"maxiter": 2000})
        self.coef_, self.sigma_ = res.x[:-1], np.exp(res.x[-1])
        return self

    def predict(self, X):
        return np.c_[np.ones(len(X)), (np.asarray(X, float) - self.mean_) / self.std_] @ self.coef_
