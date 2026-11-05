# F1-Simulation

Ziel: aus 120 Testrunden das Rundenzeit-Modell des Simulators schätzen, den optimalen Trim und die beste Rennstrategie finden. Erste Strecke: Spanien (Round 1, 60 Runden, 5,1 km).

## Feste Regeln
- Claude fährt keine Runden und löst niemals ein Qualifying aus. Das macht der Nutzer selbst.
- Nie im Chat nach dem Passwort fragen. Zugangsdaten stehen nur in `.env`, Claude liest diese Datei nicht.
- Die Zugangsdaten aus `.env` dürfen ausschließlich per GET für die zwei Export-Adressen genutzt werden: `export_practice_data.php` und `export_race_data.php`. Keine anderen Adressen der Seite aufrufen, keine Formulare abschicken, keine Stints oder Qualifying-Runden auslösen.
- Rohdaten im Projektordner nicht verändern.

## Verständnis von `simulator_data` (laut Data Center, vom Nutzer am 02.11.2026 korrigiert)
- Computerberechnete optimale Setups für erfundene Strecken, verrauscht, aber realistisch.
- Jede Zeile: Streckenmerkmale → optimales Setup → Rundenzeit mit diesem Setup.
- Die Abhängigkeit der Setups von der Strecke (A3 in `data_inventory.md`) ist das Lernziel, keine Falle.
- Die Häufung an 1 und 500 (A4) bedeutet vermutlich: Das wahre Optimum liegt außerhalb des Bereichs und wurde abgeschnitten.
- Die Kosten einer Abweichung vom Optimum sind aus diesen Daten lernbar (vom Nutzer am 02.11.2026 bestätigt, frühere Annahme war falsch). Mit der Abweichung als Eingabe steigt das kreuzvalidierte R² der Zeit je km von 0,075 auf 0,739, das Minimum liegt nahe Abweichung 0. Im Training noch nicht bestätigt.

## Zufall je Runde (Hinweis des Lehrers)
Jede Runde hat einen Zufallsanteil, nicht jede Runde ist gleich; deshalb gibt es längere Stints. Das gilt für alle Auswertungen: Einzelrunden nie als Messwert ohne Unsicherheit behandeln. Block 1 schätzt zuerst die Größe des Zufalls, aus den zwei identischen Stints und aus dem 8-Runden-Stint. Daraus folgt die Rundenzahl, um bei Brake und Differential 50 Punkte sicher zu erkennen. Block 2 wird erst danach festgelegt, bei großem Zufall mit längeren Stints statt 1-Runden-Stints.

## Hinweise aus docs/
- Interview Gordy: Modelle mit getrennten Stichproben vergleichen. Setup-Werte unabhängig voneinander und von Sprit und Reifen. Nicht jedes Merkmal wirkt auf jeden Wert. Trainingsrunden sind knapp.
- Interview zum Sprit: Wird der Tank in einer Runde leer, reicht es meist noch bis zum Rundenende. Dann folgt ein Stopp ohne Zeitverlust. Ungetestet: ob man dadurch mit weniger als Verbrauch × Runden auskommt.
- Transkript: Rundenzeit = Grundzeit (Extra Soft, leerer Tank) + fester Aufschlag je Mischung + Aufschlag je Liter. Dazu Verbrauch und Verschleiß pro Runde je Mischung. Leerer Tank oder abgefahrene Reifen erzwingen sofort einen Stopp.
- Das Transkript zeigt eine andere Fassung der Excel-Vorlage: Felder für Reifen- und Spritaufschlag und kumulierte Zeit fehlen in `Race Simulator (2).xlsx`.

## Vorgehen und Dateien
- `setup_model.py`: Modellvergleich je Parameter, schreibt `results/setup_model_report.md` und `results/spain_prediction_tobit.json`. Laufzeit etwa 3 Minuten.
- `joint_model.py`: gemeinsames Modell aus Rundenzeit, schreibt `results/joint_model.json`. Laufzeit etwa 6 Minuten, danach `cost_analysis.py`.
- `cost_analysis.py`: Kostenkurven, Grafik `results/cost_curves.png`, `results/cost_report.md`, `results/cost_curves.json` und das maßgebliche `results/spain_prediction.json`.
- `power.py`: Rundenbedarf für 50 Punkte. `tobit.py`: Regression für abgeschnittene Werte.
- `get_practice_data.py`, `get_race_data.py`: Zugangsdaten aus `.env` (`F1_USERNAME`, `F1_PASSWORD`). Originale in `backup/`.
- `fetch_practice_data.py`: speichert nach `data/tests/practice_<Zeitstempel>.csv`. Vom Nutzer auszuführen.
- `plans/block1_stints.csv`: erster Trainingsblock, 12 Runden. Nur Checkliste, der Nutzer gibt Stints von Hand im Formular ein.
- `analyze_block1.py`: Auswertung des Blocks, schreibt `results/block1_estimates.json`. Mit erfundenen Daten getestet.
- `race_model.py`: Rennmodell und Optimierer, mit wörtlichem Durchrechnen auf kurzen Rennen abgeglichen.

## Ergebnis Spanien (vorläufig, gemeinsames Modell)
Rear Wing 500, Engine 92, Front Wing 500, Brake 99, Differential 233, Suspension 77. Referenz-Rundenzeit 95,70 s (Sprit und Reifen dieser Daten unbekannt). Vorherige Fassung in `backup/block1_stints_v1.csv`.

## Kostenkurve und gemeinsames Modell
- Form: nahe 0 quadratisch, ab etwa 100 Punkten sättigend (Glocke `A * (1 - exp(-r^2 / (2 w^2)))`), w etwa 60 bis 72, Grenze 0,8 bis 1,0 s/Runde. Weitgehend symmetrisch, Engine etwas schief. Kosten addieren sich. Abweichung bezieht sich auf das auf 1 bis 500 begrenzte Optimum.
- 50 Punkte kosten auf Spanien etwa 0,2 s/Runde, also rund 13 s/Rennen.
- Gemeinsames Modell gegen zweistufig: R² 0,738 auf 0,769, besser in allen 5 Folds, auch nahe Spanien. Auf erfundenen Daten mit bekanntem Optimum trifft es alle sechs Werte genauer. Bei Brake kein klarer Gewinn (3 von 5 Folds), bei Differential und Engine in allen Folds.
- Unsicherheit über 60 Runden (Bootstrap): Brake 0,14 s, Differential 0,33 s, Engine 1,65 s, alle sechs 2,3 s. Nimmt man abweichende Verfahren ernst, Differential bis 5,4 s (lokale Schätzung 263), Engine bis 5,0 s. Gradient Boosting bei Brake (161, 18 s) gilt als Ausreißer, die lokale Schätzung ergibt 103.

## Regel für Block 2 (erst nach Block 1 festlegen)
- `analyze_block1.py` liefert den Zufall je Runde und die Rundenzahl für 50 Punkte. Obergrenze vorab aus `simulator_data`: 0,40 s, enthält auch Modellfehler.
- Test an den Flanken (Setup -k gegen +k, k etwa 75) statt am flachen Boden: Unterschied etwa 0,67 s statt 0,21 s, also rund neunmal weniger Runden. Beruht auf der Modellkurve. Runden gesamt je Vergleich bei Zufall 0,1 / 0,2 / 0,3 / 0,4 s: 4 / 4 / 10 / 16.
- Weil Kosten sich addieren, kann ein gemeinsamer Versuchsplan mehrere Parameter mit denselben Runden testen.
- Brake lohnt sich allein nicht. Vorrang für Engine und Differential, nur falls der Zufall den Test billig macht.
- Bei großem Zufall längere Stints gleichen Aufbaus je Einstellung, dann heben sich Sprit- und Reifentrend auf.

## Annahmen
- Setup-Wahl im Einzelmodell: unter den Tobit-Modellen (lineare Regression für abgeschnittene Werte) und Gradient Boosting das einfachste, dessen MAE höchstens 0,5 Punkte schlechter ist als das beste.
- Schlankes Modell: Merkmal zählt, wenn sein Lasso-Koeffizient mindestens 5 Punkte je Standardabweichung beträgt.
- "Sicher erkennen": 5 % Fehlalarm, 90 % Trefferquote, unabhängiger Zufall je Runde, mindestens 2 Runden je Einstellung.
- Zufall in `simulator_data` skaliert mit der Streckenlänge (Rest je km konstant). Der Zufall ändert den Erwartungswert nicht, Strategien werden nach dem Erwartungswert verglichen.
- Referenz-Rundenzeit gilt für Abweichung 0. Sprit und Reifen in `simulator_data` sind unbekannt, die Zahl ist also keine Grundzeit.
- Rennmodell: Stopp am Rundenende; Sprit und Reifenzustand zu Rundenbeginn bestimmen die Zeit. Erzwungener Stopp nimmt den nächsten geplanten Stint, sonst gleiche Mischung und Sprit bis ins Ziel.
- Nicht modelliert, weil unbekannt: Tankgrenze, Pflicht zu zwei Mischungen, Überholen und Gegner.
- Werte in `RaceParams` sind Platzhalter, die Optimierer-Ausgabe ist noch keine Empfehlung.

## Stand (02.11.2026)
Modelle, Kostenkurven und Block 1 sind vorbereitet. Noch keine Runde gefahren, keine echten Trainingsdaten. Block 2 absichtlich noch nicht geplant, die Rundenzahl fehlt noch.

## Offen
- `.env` muss der Nutzer selbst anlegen (Berechtigungsregel sperrt die Datei für Claude), siehe Abschluss-Hinweis: `printf 'F1_USERNAME=\nF1_PASSWORD=\n' > .env && chmod 600 .env`
- Block 1 fahren, dann `python3 fetch_practice_data.py` und `python3 analyze_block1.py`, Werte in `RaceParams` übernehmen.
- Block 2, nach Block 1 festzulegen: Tank-Test (Stint mit knapp einer Rundenfüllung weniger), Soft, Medium, Hard, Feinjustierung Brake und Differential nur falls sie sich lohnt.
- Andere Mischungen, Kosten einer Setup-Abweichung und stark abgefahrene Reifen sind noch ungetestet.
- Pit Time für Spanien ist unbekannt, 30 s stammt aus der Excel-Vorlage.
- Rohdaten nach `data/raw/` verschieben? Noch nicht entschieden.
