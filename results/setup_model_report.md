# Setup-Modell Spain

Erzeugt von `setup_model.py`. 5-fache Kreuzvalidierung, gleiche Folds für alle Modelle. Vorhersagen auf 1 bis 500 begrenzt.

## Vorhersage

| Setup | Wert | Modell | Tobit schlank vor Begrenzung | Spanne der 5 Kandidaten | MAE gesamt | MAE nahe dieser Vorhersage | 80 % der verrauschten Datenwerte nahe dieser Vorhersage | 90 % Bootstrap der Vorhersage | Anteil an Grenze nahe dieser Vorhersage |
|---|---|---|---|---|---|---|---|---|---|
| Rear Wing | 500 | Tobit quadr. schlank | 561 | 463 bis 500 | 68.0 | 43.8 | 369 bis 500 | 500 bis 500 | 46% |
| Engine | 114 | Tobit quadr. schlank | 119 | 110 bis 127 | 53.2 | 72.0 | 1 bis 222 | 99 bis 125 | 21% |
| Front Wing | 500 | Tobit schlank | 504 | 480 bis 500 | 71.6 | 51.1 | 357 bis 500 | 498 bis 500 | 43% |
| Brake Balance | 107 | Tobit schlank | 107 | 85 bis 161 | 69.6 | 69.5 | 1 bis 208 | 102 bis 112 | 21% |
| Differential | 217 | Tobit quadr. schlank | 228 | 217 bis 274 | 63.9 | 81.6 | 100 bis 363 | 205 bis 230 | 1% |
| Suspension | 72 | Tobit schlank | 72 | 71 bis 102 | 71.9 | 67.7 | 1 bis 202 | 65 bis 78 | 24% |

Die beiden Spannen messen Verschiedenes: Die Datenspanne enthält das Rauschen der Trainingsdaten. Die Bootstrap-Spanne zeigt, wie genau das Modell den mittleren Wert trifft.

## MAE je Parameter und Modell (alle Zeilen)

| Modell | Rear Wing | Engine | Front Wing | Brake Balance | Differential | Suspension |
|---|---|---|---|---|---|---|
| Linear | 71.3 | 63.8 | 72.6 | 70.9 | 69.8 | 72.2 |
| Lasso | 71.5 | 63.8 | 72.7 | 71.0 | 70.0 | 72.3 |
| Quadratisch | 69.9 | 56.5 | 72.9 | 70.1 | 65.9 | 72.1 |
| Gradient Boosting | 69.1 | 56.6 | 71.7 | 69.3 | 65.2 | 72.0 |
| Linear schlank | 71.3 | 63.8 | 72.6 | 70.9 | 69.8 | 72.2 |
| Tobit | 68.7 | 58.4 | 71.7 | 69.6 | 65.7 | 71.9 |
| Tobit schlank | 68.7 | 58.4 | 71.6 | 69.6 | 65.7 | 71.9 |
| Tobit quadratisch | 68.4 | 53.4 | 72.0 | 69.6 | 64.1 | 71.9 |
| Tobit quadr. schlank | 68.0 | 53.2 | 71.8 | 69.1 | 63.9 | 71.6 |
| Linear nur Innenzeilen | 74.7 | 73.1 | 74.6 | 73.3 | 74.7 | 73.8 |
| GB nur Innenzeilen | 73.5 | 67.1 | 74.2 | 72.7 | 71.3 | 74.2 |

Standardabweichung des MAE über die 5 Folds: Rear Wing 1.2, Engine 0.9, Front Wing 0.8, Brake Balance 1.9, Differential 0.8, Suspension 0.6 (Modell Linear).

## Abschneiden: MAE auf Innenzeilen / Grenzzeilen

| Modell | Rear Wing | Engine | Front Wing | Brake Balance | Differential | Suspension |
|---|---|---|---|---|---|---|
| Linear | 70.0 / 76.6 | 64.6 / 62.5 | 71.8 / 77.6 | 70.7 / 72.0 | 68.6 / 73.3 | 71.0 / 81.8 |
| Lasso | 70.0 / 78.0 | 64.6 / 62.6 | 71.7 / 79.1 | 70.6 / 73.3 | 68.6 / 74.2 | 70.9 / 83.1 |
| Quadratisch | 69.8 / 70.3 | 60.9 / 49.3 | 72.1 / 77.7 | 70.0 / 70.8 | 67.4 / 61.6 | 70.3 / 86.0 |
| Gradient Boosting | 69.2 / 68.4 | 59.5 / 51.8 | 71.2 / 74.9 | 69.2 / 70.2 | 66.6 / 60.9 | 70.3 / 85.2 |
| Linear schlank | 70.0 / 76.6 | 64.6 / 62.6 | 71.8 / 77.7 | 70.7 / 72.1 | 68.6 / 73.3 | 71.0 / 81.8 |
| Tobit | 71.5 / 57.7 | 71.2 / 36.9 | 73.1 / 62.5 | 72.0 / 56.2 | 70.4 / 51.8 | 72.3 / 69.3 |
| Tobit schlank | 71.5 / 57.6 | 71.3 / 36.9 | 73.1 / 62.5 | 72.0 / 56.2 | 70.3 / 51.7 | 72.3 / 69.2 |
| Tobit quadratisch | 72.6 / 51.5 | 71.3 / 23.4 | 73.5 / 62.7 | 72.5 / 53.3 | 72.7 / 38.4 | 72.0 / 71.8 |
| Tobit quadr. schlank | 72.2 / 51.1 | 71.5 / 22.8 | 73.3 / 62.3 | 72.1 / 52.9 | 72.6 / 38.2 | 71.5 / 72.0 |
| Linear nur Innenzeilen | 69.9 / 94.0 | 61.7 / 92.0 | 71.3 / 95.2 | 70.3 / 89.7 | 68.6 / 92.8 | 70.0 / 103.0 |
| GB nur Innenzeilen | 67.9 / 96.1 | 55.2 / 86.9 | 70.1 / 100.3 | 67.5 / 101.1 | 63.9 / 93.2 | 69.3 / 112.4 |

## Spanien je Modell

| Modell | Rear Wing | Engine | Front Wing | Brake Balance | Differential | Suspension |
|---|---|---|---|---|---|---|
| Linear | 500 | 140 | 475 | 124 | 225 | 84 |
| Lasso | 500 | 140 | 473 | 126 | 225 | 88 |
| Quadratisch | 476 | 135 | 469 | 93 | 222 | 85 |
| Gradient Boosting | 463 | 110 | 480 | 161 | 274 | 102 |
| Linear schlank | 500 | 134 | 477 | 123 | 227 | 85 |
| Tobit | 500 | 127 | 500 | 109 | 225 | 71 |
| Tobit schlank | 500 | 119 | 500 | 107 | 228 | 72 |
| Tobit quadratisch | 500 | 118 | 497 | 85 | 220 | 75 |
| Tobit quadr. schlank | 500 | 114 | 500 | 99 | 217 | 76 |
| Linear nur Innenzeilen | 487 | 169 | 447 | 137 | 227 | 104 |
| GB nur Innenzeilen | 430 | 141 | 464 | 173 | 256 | 124 |

## Lasso-Koeffizienten

Setup-Punkte je Standardabweichung des Merkmals.

| Setup | Lap Distance | Cornering | Inclines | Camber | Grip | Wind (Avg. Speed) | Temperature | Humidity | Air Density | Air Pressure | Wind (Gusts) | Altitude | Roughness | Width |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Rear Wing | 0 | +53 | +52 | 0 | 0 | +41 | 0 | +29 | -56 | -54 | +8 | -1 | +24 | 0 |
| Engine | 0 | -10 | +20 | +1 | +29 | +2 | +20 | +23 | +22 | +18 | +6 | -21 | -1 | -2 |
| Front Wing | +1 | +69 | +42 | 0 | 0 | +27 | +1 | +16 | -51 | -66 | +16 | 0 | -11 | 0 |
| Brake Balance | 0 | +69 | 0 | 0 | +2 | 0 | +14 | +1 | +1 | 0 | 0 | 0 | +38 | +68 |
| Differential | 0 | +59 | +47 | +1 | +37 | -1 | +26 | +10 | +22 | 0 | 0 | 0 | 0 | +51 |
| Suspension | 0 | -23 | -34 | +17 | +37 | +2 | 0 | 0 | 0 | 0 | -1 | 0 | +13 | +14 |

## Permutations-Wichtigkeit (Gradient Boosting)

Anstieg des MAE in Punkten, wenn das Merkmal gemischt wird, auf den Test-Folds.

| Setup | Lap Distance | Cornering | Inclines | Camber | Grip | Wind (Avg. Speed) | Temperature | Humidity | Air Density | Air Pressure | Wind (Gusts) | Altitude | Roughness | Width |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Rear Wing | -0.0 | 22.5 | 20.9 | -0.0 | 0.0 | 13.4 | -0.0 | 6.6 | 24.0 | 23.1 | 0.6 | 0.0 | 4.6 | -0.0 |
| Engine | -0.0 | 1.3 | 5.2 | 0.0 | 11.2 | -0.1 | 5.3 | 7.4 | 6.9 | 4.4 | 0.3 | 5.2 | 0.1 | -0.0 |
| Front Wing | -0.0 | 34.1 | 12.7 | 0.0 | 0.0 | 5.2 | -0.0 | 1.8 | 20.1 | 32.2 | 1.8 | 0.0 | 0.8 | -0.1 |
| Brake Balance | -0.0 | 35.9 | -0.0 | -0.0 | 0.1 | 0.0 | 1.6 | -0.0 | 0.2 | -0.0 | -0.0 | -0.0 | 11.9 | 35.4 |
| Differential | 0.0 | 30.6 | 20.0 | 0.0 | 12.1 | 0.0 | 6.4 | 0.9 | 4.4 | -0.0 | 0.0 | -0.0 | 0.0 | 24.3 |
| Suspension | -0.0 | 4.0 | 9.2 | 2.3 | 11.1 | 0.1 | 0.0 | 0.0 | -0.0 | 0.1 | 0.0 | 0.1 | 1.5 | 1.4 |

## Schlanke Merkmalssätze (Lasso, Betrag mindestens 5)

| Setup | Anzahl | Merkmale |
|---|---|---|
| Rear Wing | 8 | Cornering, Inclines, Wind (Avg. Speed), Humidity, Air Density, Air Pressure, Wind (Gusts), Roughness |
| Engine | 9 | Cornering, Inclines, Grip, Temperature, Humidity, Air Density, Air Pressure, Wind (Gusts), Altitude |
| Front Wing | 8 | Cornering, Inclines, Wind (Avg. Speed), Humidity, Air Density, Air Pressure, Wind (Gusts), Roughness |
| Brake Balance | 4 | Cornering, Temperature, Roughness, Width |
| Differential | 7 | Cornering, Inclines, Grip, Temperature, Humidity, Air Density, Width |
| Suspension | 6 | Cornering, Inclines, Camber, Grip, Roughness, Width |

In keinem Satz: Lap Distance.

## Rundenzeit Spanien

| Modell | MAE (s) | Std.-Abw. Fehler (s) | Spain (s) |
|---|---|---|---|
| Linear | 0.518 | 0.653 | 97.99 |
| Lasso | 0.520 | 0.655 | 97.96 |
| Quadratisch | 0.510 | 0.644 | 97.73 |
| Gradient Boosting | 0.517 | 0.653 | 97.76 |
| Quadratisch auf s/km | 0.510 | 0.644 | 97.67 |
| Quadratisch auf s/km + Setup-Abweichung (Referenz bei Abweichung 0) | 0.254 | 0.342 | 95.75 |

## Kosten einer Abweichung vom vorhergesagten Setup

Kreuzvalidiertes R² der Zeit je km: nur Strecke 0.075, mit Setup-Abweichung 0.739. Zeitverlust in Sekunden pro Runde auf Spain (5.1 km) gegenüber Abweichung 0:

| Setup | -150 | -100 | -50 | +0 | +50 | +100 | +150 | Minimum der Kurve bei |
|---|---|---|---|---|---|---|---|---|
| Rear Wing | +0.73 | +0.58 | +0.24 | +0.00 | +0.15 | +0.50 | +0.74 | +5 |
| Engine | +0.66 | +0.48 | +0.14 | +0.00 | +0.30 | +0.72 | +0.88 | -10 |
| Front Wing | +0.80 | +0.55 | +0.20 | +0.00 | +0.19 | +0.55 | +0.77 | +0 |
| Brake Balance | +0.79 | +0.52 | +0.16 | +0.00 | +0.21 | +0.59 | +0.81 | -5 |
| Differential | +0.81 | +0.56 | +0.19 | +0.00 | +0.23 | +0.61 | +0.80 | +0 |
| Suspension | +0.96 | +0.61 | +0.24 | +0.00 | +0.19 | +0.59 | +0.88 | +5 |

## Sind die Setups nach Abzug der Strecke unabhängig?

Korrelation der Abweichungen untereinander, größter Betrag: 0.089.
