"""Wie viele Runden braucht es, um 50 Setup-Punkte sicher zu erkennen?

"Sicher" heißt hier: 5 % Fehlalarm (zweiseitig), 90 % Trefferquote, unabhängiger Zufall je Runde.
"""
import math

import numpy as np
from scipy.stats import norm

Z = norm.ppf(0.975) + norm.ppf(0.90)


def cost(r, amp_s_lap, w):
    return amp_s_lap * (1 - np.exp(-(r**2) / (2 * w**2)))


def laps_per_setting(sigma, delta):
    """Runden je Einstellung beim Vergleich zweier Einstellungen."""
    return max(2, math.ceil(2 * (Z * sigma / delta) ** 2))  # nie weniger als 2, die Rechnung ist bei sehr kleinen Zahlen nur grob


def direct_delta(amp_s_lap, w, shift=50):
    """Vergleich am Boden der Kurve: Optimum gegen 50 Punkte daneben."""
    return float(cost(shift, amp_s_lap, w))


def flank_delta(amp_s_lap, w, value, shift=50, low=1, high=500):
    """Vergleich an den Flanken: value-k gegen value+k. Liegt das Optimum 50 Punkte daneben, sind die Zeiten verschieden."""
    best = (0.0, 0)
    for k in range(50, 201, 5):
        if value - k < low or value + k > high:
            continue
        d = float(cost(k + shift, amp_s_lap, w) - cost(k - shift, amp_s_lap, w))
        if d > best[0]:
            best = (d, k)
    return best
