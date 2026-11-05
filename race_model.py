"""Rennmodell nach dem Vorbild der Excel-Vorlage, korrigiert.

Korrekturen gegenüber Excel: Boxenzeit zählt mit, leerer Tank oder abgefahrene Reifen erzwingen einen
Stopp, Sprit je Stint reicht genau bis zum Stopp.
Lauf: python3 race_model.py (Beispiel Spanien mit Platzhaltern, keine Empfehlung)
"""
import heapq
from dataclasses import dataclass, field
from itertools import combinations
from math import comb, sqrt

EPS = 1e-9
TYRES = ["Extra Soft", "Soft", "Medium", "Hard"]


@dataclass
class RaceParams:
    """Alle Standardwerte sind PLATZHALTER, bis Messwerte da sind."""

    n_laps: int = 60  # Spanien, track_data
    lap_noise_sd_s: float = 0.2  # Platzhalter: Zufall je Runde, Wert aus Block 1 übernehmen
    base_lap_s: float = 95.70  # Platzhalter: Vorhersage aus simulator_data, Sprit- und Reifenstand dort unbekannt
    fuel_penalty_s_per_l: float = 0.03  # Platzhalter, frei gewählt
    fuel_per_lap_l: float = 2.55  # Platzhalter: Excel, 0,5 l/km * 5,1 km
    pit_time_s: float = 30.0  # Platzhalter: Excel
    tyre_effect_s_per_pct: float = 0.0  # Platzhalter: Aufschlag je Prozentpunkt verbrauchter Reifen
    tyre_penalty_s: dict = field(default_factory=lambda: {"Extra Soft": 0.0, "Soft": 0.5, "Medium": 1.1, "Hard": 1.7})  # Medium: Beispiel aus dem Transkript, Rest frei gewählt
    wear_pct_per_lap: dict = field(default_factory=lambda: {"Extra Soft": 1.78, "Soft": 1.48, "Medium": 1.28, "Hard": 1.08})  # Platzhalter: Excel


def lap_time(tyre, fuel_start, condition_start, p):
    """Rundenzeit aus Sprit und Reifenzustand zu Rundenbeginn."""
    return p.base_lap_s + p.tyre_penalty_s[tyre] + p.fuel_penalty_s_per_l * fuel_start + p.tyre_effect_s_per_pct * (100 - condition_start)


def race_noise_sd(p):
    """Streuung der Rennzeit durch den Zufall je Runde. Der Mittelwert und damit die beste Strategie ändern sich dadurch nicht."""
    return p.lap_noise_sd_s * sqrt(p.n_laps)


def simulate(tyres, pit_laps, p, fuels=None, rng=None):
    """Rechnet ein Rennen Runde für Runde. Gestoppt wird am Ende einer Runde.

    tyres: Mischung je Stint, ein Eintrag mehr als pit_laps.
    fuels: Sprit je Stint; ohne Angabe genau bis zum nächsten geplanten Stopp.
    Der Wagen beendet eine Runde auch dann, wenn der Tank in ihr leer wird, und kommt dann an die Box.
    Erzwungener Stopp: nimmt den nächsten geplanten Stint, sonst dieselbe Mischung und Sprit bis ins Ziel.
    rng: numpy-Zufallsgenerator; damit bekommt jede Runde ihren Zufallsanteil, ohne ihn rechnet das Modell den Erwartungswert.
    """
    plan = sorted(pit_laps)
    if len(tyres) != len(plan) + 1 or len(set(plan)) != len(plan) or any(not 1 <= x < p.n_laps for x in plan):
        raise ValueError("Ungültige Strategie")

    def laps_until_next_stop(after_lap):
        return min((x for x in plan if x > after_lap), default=p.n_laps) - after_lap

    stint = 0
    fuel = fuels[0] if fuels else p.fuel_per_lap_l * laps_until_next_stop(0)
    condition = 100.0
    total, stops, forced, rows = 0.0, 0, 0, []
    for lap in range(1, p.n_laps + 1):
        tyre = tyres[stint]
        t = lap_time(tyre, fuel, condition, p) + (rng.normal(0, p.lap_noise_sd_s) if rng is not None else 0.0)
        fuel_start, condition_start = fuel, condition
        fuel -= p.fuel_per_lap_l
        condition -= p.wear_pct_per_lap[tyre]
        planned = lap in plan
        must = fuel <= EPS or condition <= EPS
        pit = lap < p.n_laps and (planned or must)
        total += t + (p.pit_time_s if pit else 0.0)
        rows.append({"lap": lap, "tyre": tyre, "fuel_start": fuel_start, "condition_start": condition_start,
                     "lap_time": t, "pit": pit, "forced": pit and must and not planned, "race_time": total})
        if pit:
            stops += 1
            forced += not planned
            if stint + 1 < len(tyres):
                stint += 1
                fuel = fuels[stint] if fuels else p.fuel_per_lap_l * laps_until_next_stop(lap)
            else:
                fuel = p.fuel_per_lap_l * (p.n_laps - lap)
            condition = 100.0
    return {"total_s": total, "stops": stops, "forced_stops": forced, "laps": rows}


def stint_table(p):
    """Zeit je Mischung und Stintlänge; None, wenn der Reifen vorher am Ende ist."""
    table = {}
    for tyre in TYRES:
        for n in range(1, p.n_laps + 1):
            if p.wear_pct_per_lap[tyre] * (n - 1) >= 100 - EPS:
                table[tyre, n] = None
                continue
            table[tyre, n] = sum(lap_time(tyre, p.fuel_per_lap_l * (n - k), 100 - p.wear_pct_per_lap[tyre] * k, p) for k in range(n))
    return table


def optimize(p, max_stops=4, top=10):
    """Rechnet alle Stopprunden für 0 bis max_stops Stopps durch.

    Bei exakt bemessenem Sprit hängt die Zeit eines Stints nur von Mischung und Länge ab. Die beste
    Mischung je Stint lässt sich also getrennt wählen, ohne jede Mischungsfolge einzeln zu rechnen.
    Das Ergebnis ist dasselbe wie beim Durchrechnen aller Kombinationen, der Aufwand sinkt um den Faktor 4^(Stints).
    """
    table = stint_table(p)
    best_tyre, best_time = {}, {}
    for n in range(1, p.n_laps + 1):
        options = [(table[t, n], t) for t in TYRES if table[t, n] is not None]
        if options:
            best_time[n], best_tyre[n] = min(options)

    keep = top * 120  # gleiche Stints in anderer Reihenfolge sind gleich schnell, vor dem Ausdünnen mehr behalten
    heap, best_by_stops, evaluated, covered = [], {}, 0, 0
    for k in range(max_stops + 1):
        covered += comb(p.n_laps - 1, k) * len(TYRES) ** (k + 1)
        for pits in combinations(range(1, p.n_laps), k):
            evaluated += 1
            edges = (0,) + pits + (p.n_laps,)
            total = k * p.pit_time_s
            for a, b in zip(edges, edges[1:]):
                part = best_time.get(b - a)
                if part is None:
                    break
                total += part
            else:
                if k not in best_by_stops or total < best_by_stops[k][0]:
                    best_by_stops[k] = (total, pits)
                item = (-total, pits)
                if len(heap) < keep:
                    heapq.heappush(heap, item)
                elif item > heap[0]:
                    heapq.heapreplace(heap, item)

    def describe(total, pits):
        edges = (0,) + pits + (p.n_laps,)
        lengths = [b - a for a, b in zip(edges, edges[1:])]
        return {"total_s": total, "stops": len(pits), "pit_laps": list(pits), "tyres": [best_tyre[n] for n in lengths],
                "fuels_l": [round(n * p.fuel_per_lap_l, 2) for n in lengths]}

    ranked, seen = [], set()
    for neg, pits in sorted(heap, reverse=True):
        edges = (0,) + pits + (p.n_laps,)
        key = tuple(sorted(b - a for a, b in zip(edges, edges[1:])))
        if key not in seen:
            seen.add(key)
            ranked.append(describe(-neg, pits))
        if len(ranked) == top:
            break
    return {"best": ranked, "best_by_stops": {k: describe(*v) for k, v in sorted(best_by_stops.items())},
            "pit_lap_sets": evaluated, "strategies_covered": covered}


def clock(seconds):
    return f"{int(seconds // 3600)}:{int(seconds % 3600 // 60):02d}:{seconds % 60:06.3f}"


if __name__ == "__main__":
    params = RaceParams()
    result = optimize(params)
    print("NUR PLATZHALTER, keine Empfehlung.")
    print(f"Abgedeckte Strategien: {result['strategies_covered']:,}; gerechnete Stopprunden-Kombinationen: {result['pit_lap_sets']:,}")
    print(f"Zufall je Runde {params.lap_noise_sd_s} s: Eine einzelne Rennzeit streut um {race_noise_sd(params):.1f} s. Strategien werden nach dem Erwartungswert verglichen.")
    print("\nBeste Strategie je Stoppzahl")
    for k, r in result["best_by_stops"].items():
        print(f"  {k} Stopps: {clock(r['total_s'])}  Stopps nach Runde {r['pit_laps']}  {r['tyres']}  Sprit {r['fuels_l']}")
    print("\nBeste Strategien insgesamt (gleiche Stints in anderer Reihenfolge nur einmal)")
    for r in result["best"][:5]:
        print(f"  {clock(r['total_s'])}  Stopps nach Runde {r['pit_laps']}  {r['tyres']}  Sprit {r['fuels_l']}")
