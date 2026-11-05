# Kosten der Setup-Abweichung

Erzeugt von `cost_analysis.py`. Grafik: `results/cost_curves.png`.

## Form je Parameter

Kreuzvalidierte RMSE der Zeit je km; nur dieser Parameter bekommt die jeweilige Form.

| Parameter | gleichmäßig (V) | quadratisch | sättigend (Glocke) |
|---|---|---|---|
| Rear Wing | 0.07715 | 0.08042 | 0.07651 |
| Engine | 0.07714 | 0.08277 | 0.07651 |
| Front Wing | 0.07722 | 0.07981 | 0.07651 |
| Brake Balance | 0.07704 | 0.07944 | 0.07651 |
| Differential | 0.07714 | 0.08108 | 0.07651 |
| Suspension | 0.07671 | 0.07876 | 0.07651 |

## Symmetrie

Grenze der Kurve (s je Runde, 5.1 km) links und rechts des Optimums.

| Parameter | links | rechts |
|---|---|---|
| Rear Wing | 0.82 | 0.80 |
| Engine | 0.82 | 0.93 |
| Front Wing | 0.86 | 0.85 |
| Brake Balance | 0.92 | 0.92 |
| Differential | 0.83 | 0.86 |
| Suspension | 1.04 | 1.03 |

## Kosten der Unsicherheit über 60 Runden

Erwartung: Bootstrap-Streuung um den Modellwert. Spalten dahinter: anderes Schätzverfahren und Zeitverlust, falls dieses recht hätte.

| Parameter | Wert gemeinsam | Bootstrap Std. | Erwartet (s/Rennen) | zweistufig | lokal nahe Spanien | Tobit einfach | GB |
|---|---|---|---|---|---|---|---|
| Rear Wing | 500 | 0 | 0.00 | 500 (0.0 s) | 500 (0.0 s) | 500 (0.0 s) | 463 (6.8 s) |
| Engine | 92 | 15 | 1.65 | 114 (3.4 s) | 67 (4.6 s) | 119 (5.0 s) | 110 (2.2 s) |
| Front Wing | 500 | 0 | 0.00 | 500 (0.0 s) | 500 (0.0 s) | 500 (0.0 s) | 480 (2.1 s) |
| Brake Balance | 99 | 5 | 0.14 | 99 (0.0 s) | 103 (0.1 s) | 107 (0.4 s) | 161 (18.0 s) |
| Differential | 233 | 7 | 0.33 | 217 (1.4 s) | 263 (5.4 s) | 228 (0.1 s) | 274 (9.3 s) |
| Suspension | 77 | 5 | 0.18 | 76 (0.0 s) | 67 (0.7 s) | 72 (0.2 s) | 102 (3.5 s) |

Gesamt erwartet über alle sechs: 2.3 s/Rennen.

## Runden für 50 Punkte (5 % Fehlalarm, 90 % Trefferquote), gesamt für den Vergleich zweier Einstellungen

| Parameter | Zufall je Runde (s) | am Boden: Optimum gegen +50 | Flanken: -k gegen +k |
|---|---|---|---|
| Brake Balance | 0.05 | 4 | 4 |
| Brake Balance | 0.10 | 10 | 4 |
| Brake Balance | 0.20 | 40 | 4 |
| Brake Balance | 0.30 | 90 | 10 |
| Brake Balance | 0.40 | 158 | 16 |
| Differential | 0.05 | 4 | 4 |
| Differential | 0.10 | 10 | 4 |
| Differential | 0.20 | 36 | 4 |
| Differential | 0.30 | 82 | 10 |
| Differential | 0.40 | 144 | 16 |

Flanken-Parameter: Brake Balance: k = 75, Unterschied 0.68 s statt 0.21 s; Differential: k = 75, Unterschied 0.66 s statt 0.22 s.

Obergrenze aus `simulator_data` (Rest des gemeinsamen Modells bei langen Strecken): 0.40 s. Das enthält auch Modellfehler; den echten Zufall misst erst Block 1.
