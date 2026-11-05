# Datenbestand F1-Simulation

Stand: 02.11.2026. Reine Bestandsaufnahme, noch kein Modell. Alle Dateien wurden nur gelesen.

> **Überholt:** Die Einordnung von A3 und A4 als Falle gilt nicht mehr. `simulator_data` enthält laut Data Center verrauschte optimale Setups. Siehe `CLAUDE.md`.

## 1. Das Wichtigste vorab

1. **`data/raw/` gibt es nicht.** Die Excel-Datei und drei zusätzliche CSV-Dateien liegen direkt im Projektordner. Ausgewertet wurden alle fünf, verschoben wurde nichts.
2. **Die Excel-Datei enthält keine vergangenen Werte.** Sie ist eine Rechenvorlage mit Platzhaltern (Rundenzeit fest 83 s). Die Daten stecken in den CSV-Dateien.
3. **Es gibt kostenlose Trainingsdaten:** `simulator_data` hat 10.000 Zeilen mit Strecke, Setup und Rundenzeit, ohne fehlende Werte.
4. **Reifen und Sprit fehlen darin.** Für Reifenwahl, Reifenzustand und Spritmenge gibt es nirgends Messwerte, nur Platzhalter in der Excel-Datei.
5. **Die 120 Testrunden sind nicht vorhanden.** `practice_data` passt vom Aufbau dazu, enthält aber nur die Kopfzeile. Auch `race_data` ist leer.
6. **Die Setups in `simulator_data` sind nicht zufällig verteilt.** Sie hängen stark von der Strecke ab (lineares R² 0,34 bis 0,66) und häufen sich an den Grenzen 1 und 500. Das ist die größte Falle für die spätere Trim-Suche (Abschnitt 7, A3 und A4).

## 2. Dateien

| Datei | Art | Größe | Inhalt | SHA-256 (Anfang) |
|---|---|---|---|---|
| `Race Simulator (2).xlsx` | Excel, 4 Blätter | 51 KB | kein Datensatz, Rechenvorlage | 3f471e517b9f |
| `simulator_data (1).csv` | CSV | 685 KB | **10.000 Zeilen, einzige echte Datenquelle** | 75d8efc6e0a8 |
| `track_data (1).csv` | CSV | 507 B | 4 Strecken, Setup-Spalten leer | 98dd6234e04d |
| `practice_data (1).csv` | CSV | 298 B | **leer, nur Kopfzeile** | f96f988694b9 |
| `race_data.csv` | CSV | 232 B | **leer, nur Kopfzeile** | 5c0e5254a0ee |

## 3. Blätter und Dateien im Einzelnen

Die Excel-Blätter sind Formulare und keine Tabellen. Deshalb stehen dort Felder statt Spalten.

### 3.1 Excel-Blatt `Setup and Strategy`

Genutzter Bereich `A1:Q117`: 117 Zeilen × 17 Spalten, 846 gefüllte Zellen, davon 771 Formeln. Leer: 57% der Zellen im Bereich (bei einem Formular normal, das ist keine Datenlücke).

**Eingabefelder**

| Feld | Zelle | Typ | Aktueller Wert |
|---|---|---|---|
| Cornering | `D7` | Zahl | 5 |
| Temperature (C) | `F7` | Zahl | 30 |
| Inclines | `D8` | Zahl | 5 |
| Humidity (%) | `F8` | Zahl | 45 |
| Lap Distance (km) | `D9` | Zahl | 3.56 |
| N. Laps | `F9` | Zahl | 88 |
| Pit Time (s) | `D10` | Zahl | 30 |
| Rear Wing | `D13` | Zahl | 250 |
| Engine | `F13` | Zahl | 250 |
| Front Wing | `D14` | Zahl | 250 |
| Brake | `F14` | Zahl | 250 |
| Differential | `D15` | Zahl | 250 |
| Suspension | `F15` | Zahl | 250 |
| Race Start: Tyre Choice | `D19` | Zahl | 2 |
| Race Start: Fuel Load (l) | `E19` | Zahl | 50 |
| Race Start: Pit Lap | `F19` | Text | -- |
| Pit 1: Tyre Choice | `D20` | Zahl | 2 |
| Pit 1: Fuel Load (l) | `E20` | Zahl | 50 |
| Pit 1: Pit Lap | `F20` | Zahl | 25 |
| Pit 2: Tyre Choice | `D21` | Zahl | 2 |
| Pit 2: Fuel Load (l) | `E21` | Zahl | 50 |
| Pit 2: Pit Lap | `F21` | Zahl | 50 |
| Pit 3: Tyre Choice | `D22` | Zahl | 2 |
| Pit 3: Fuel Load (l) | `E22` | Zahl | 50 |
| Pit 3: Pit Lap | `F22` | Zahl | 75 |
| Pit 4: Tyre Choice | `D23` | Zahl | 2 |
| Pit 4: Fuel Load (l) | `E23` | Zahl | 30 |
| Pit 4: Pit Lap | `F23` | Zahl | 80 |

Reifenliste `B30:C34`: 1 = leer, 2 = Extra Soft, 3 = Soft, 4 = Medium, 5 = Hard. Weitere Felder: `Q2` Predicted Race Time (Formel, aktuell 02:01:44).

**3 Beispielzeilen des Formulars**

| Spalte C | Spalte D | Spalte E | Spalte F |
|---|---|---|---|
| Cornering: | 5 | Temperature (C): | 30 |
| Rear Wing: | 250 | Engine: | 250 |
| Race Start: | 2 | 50 | -- |

**Rundentabelle `J6:P116`** (110 Zeilen × 7 Spalten, alles Formeln; aktuell 88 Runden belegt)

| Spalte | Datentyp | Fehlend | Bereich / eindeutige Werte |
|---|---|---|---|
| Lap | float64 | 20% | 1 bis 88 (88 verschiedene) |
| Pit | float64 | 20% | 0 bis 1 (2 verschiedene) |
| Total Pits | float64 | 20% | 0 bis 4 (5 verschiedene) |
| Selected Tyre | object | 20% | Extra Soft |
| Fuel Load | float64 | 20% | 7.28 bis 50 (34 verschiedene) |
| Tyre Condition | float64 | 20% | 0.5728 bis 1 (25 verschiedene) |
| Lap Time (s) | float64 | 20% | 83 bis 83 (1 verschiedene) |

**3 Beispielzeilen** (Runden 1, 25 und 88)

| Lap | Pit | Total Pits | Selected Tyre | Fuel Load | Tyre Condition | Lap Time (s) |
|---|---|---|---|---|---|---|
| 1 | 0 | 0 | Extra Soft | 48.22 | 0.9822 | 83 |
| 25 | 1 | 1 | Extra Soft | 50 | 1 | 83 |
| 88 | 0 | 4 | Extra Soft | 15.76 | 0.8576 | 83 |

### 3.2 Excel-Blatt `Lap Time`

Genutzter Bereich `A1:N24`: 24 Zeilen × 14 Spalten, 59 gefüllte Zellen, davon 6 Formeln. Leer: 82% der Zellen im Bereich (bei einem Formular normal, das ist keine Datenlücke).

Gleicher Formularblock wie in 3.1 (gleiche Zellen, gleiche Werte). Einziges eigenes Feld:

| Feld | Zelle | Typ | Aktueller Wert |
|---|---|---|---|
| Lap Time (secs) | `L6` | Zahl | 83 |

**3 Beispielzeilen des Formulars**

| Spalte C | Spalte D | Spalte E | Spalte F |
|---|---|---|---|
| Cornering: | 5 | Temperature (C): | 30 |
| Rear Wing: | 250 | Engine: | 250 |
| Race Start: | Extra Soft | 50 | -- |

### 3.3 Excel-Blatt `Fuel Consumption`

Genutzter Bereich `A1:N24`: 24 Zeilen × 14 Spalten, 69 gefüllte Zellen, davon 17 Formeln. Leer: 79% der Zellen im Bereich (bei einem Formular normal, das ist keine Datenlücke).

Gleicher Formularblock wie in 3.1. Einziges eigenes Feld:

| Feld | Zelle | Typ | Aktueller Wert |
|---|---|---|---|
| Fuel consumption (liters/lap), Formel `=0.5*D9` | `M6` | Formel | 1.78 |

**3 Beispielzeilen des Formulars**

| Spalte C | Spalte D | Spalte E | Spalte F |
|---|---|---|---|
| Cornering: | 5 | Temperature (C): | 30 |
| Rear Wing: | 250 | Engine: | 250 |
| Race Start: | Extra Soft | 50 | -- |

### 3.4 Excel-Blatt `Tyre Wear`

Genutzter Bereich `A1:T24`: 24 Zeilen × 20 Spalten, 75 gefüllte Zellen, davon 16 Formeln. Leer: 84% der Zellen im Bereich (bei einem Formular normal, das ist keine Datenlücke).

Gleicher Formularblock wie in 3.1. Eigene Felder (Verschleiß pro Runde, als Prozent formatiert):

| Feld | Zelle | Typ | Aktueller Wert |
|---|---|---|---|
| Extra Soft | `M7` | Zahl | 0.0178 |
| Soft | `O7` | Zahl | 0.0148 |
| Medium | `Q7` | Zahl | 0.0128 |
| Hard | `S7` | Zahl | 0.0108 |

**3 Beispielzeilen des Formulars**

| Spalte C | Spalte D | Spalte E | Spalte F |
|---|---|---|---|
| Cornering: | 5 | Temperature (C): | 30 |
| Rear Wing: | 250 | Engine: | 250 |
| Race Start: | Extra Soft | 50 | -- |

### 3.5 CSV `simulator_data (1).csv`

10000 Zeilen × 21 Spalten.

| Spalte | Datentyp | Fehlend | Bereich / eindeutige Werte |
|---|---|---|---|
| Lap Distance | float64 | 0% | 2.9 bis 5.1 (23 verschiedene) |
| Cornering | int64 | 0% | 0 bis 100 (101 verschiedene) |
| Inclines | int64 | 0% | 0 bis 100 (101 verschiedene) |
| Camber | int64 | 0% | 0 bis 100 (101 verschiedene) |
| Grip | int64 | 0% | 0 bis 100 (101 verschiedene) |
| Wind (Avg. Speed) | int64 | 0% | 0 bis 100 (101 verschiedene) |
| Temperature | int64 | 0% | 0 bis 40 (41 verschiedene) |
| Humidity | int64 | 0% | 0 bis 100 (101 verschiedene) |
| Air Density | int64 | 0% | 0 bis 100 (101 verschiedene) |
| Air Pressure | int64 | 0% | 0 bis 100 (101 verschiedene) |
| Wind (Gusts) | int64 | 0% | 0 bis 100 (101 verschiedene) |
| Altitude | int64 | 0% | 0 bis 100 (101 verschiedene) |
| Roughness | int64 | 0% | 0 bis 100 (101 verschiedene) |
| Width | int64 | 0% | 0 bis 100 (101 verschiedene) |
| Rear Wing | int64 | 0% | 1 bis 500 (500 verschiedene) |
| Engine | int64 | 0% | 1 bis 500 (467 verschiedene) |
| Front Wing | int64 | 0% | 1 bis 500 (500 verschiedene) |
| Brake Balance | int64 | 0% | 1 bis 500 (500 verschiedene) |
| Differential | int64 | 0% | 1 bis 500 (499 verschiedene) |
| Suspension | int64 | 0% | 1 bis 500 (451 verschiedene) |
| Lap Time | float64 | 0% | 54.351 bis 100.34 (8916 verschiedene) |

**3 Beispielzeilen**

| Lap Distance | Cornering | Inclines | Camber | Grip | Wind (Avg. Speed) | Temperature | Humidity | Air Density | Air Pressure | Wind (Gusts) | Altitude | Roughness | Width | Rear Wing | Engine | Front Wing | Brake Balance | Differential | Suspension | Lap Time |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 3.5 | 80 | 87 | 94 | 7 | 57 | 9 | 32 | 39 | 7 | 81 | 7 | 30 | 35 | 500 | 1 | 334 | 22 | 54 | 1 | 67.069 |
| 4.1 | 27 | 63 | 10 | 96 | 67 | 28 | 56 | 32 | 63 | 34 | 83 | 37 | 7 | 433 | 101 | 302 | 48 | 115 | 161 | 78.072 |
| 4.9 | 2 | 43 | 45 | 66 | 33 | 6 | 44 | 1 | 89 | 17 | 87 | 5 | 36 | 226 | 1 | 81 | 1 | 1 | 103 | 92.396 |

### 3.6 CSV `track_data (1).csv`

4 Zeilen × 23 Spalten.

| Spalte | Datentyp | Fehlend | Bereich / eindeutige Werte |
|---|---|---|---|
| Round | int64 | 0% | 1 bis 4 (4 verschiedene) |
| Track | object | 0% | Spain, Belgium, United States of America, Brazil |
| Lap Distance | float64 | 0% | 2.9 bis 5.1 (4 verschiedene) |
| N. Laps | int64 | 0% | 60 bis 106 (4 verschiedene) |
| Cornering | int64 | 0% | 16 bis 99 (4 verschiedene) |
| Inclines | int64 | 0% | 29 bis 85 (4 verschiedene) |
| Camber | int64 | 0% | 8 bis 99 (4 verschiedene) |
| Grip | int64 | 0% | 40 bis 94 (4 verschiedene) |
| Wind (Avg. Speed) | int64 | 0% | 15 bis 92 (4 verschiedene) |
| Temperature | int64 | 0% | 4 bis 18 (4 verschiedene) |
| Humidity | int64 | 0% | 5 bis 92 (4 verschiedene) |
| Air Density | int64 | 0% | 24 bis 91 (4 verschiedene) |
| Air Pressure | int64 | 0% | 5 bis 91 (4 verschiedene) |
| Wind (Gusts) | int64 | 0% | 26 bis 80 (4 verschiedene) |
| Altitude | int64 | 0% | 18 bis 66 (4 verschiedene) |
| Roughness | int64 | 0% | 4 bis 75 (3 verschiedene) |
| Width | int64 | 0% | 6 bis 56 (4 verschiedene) |
| Rear Wing | float64 | 100% | keine Werte |
| Engine | float64 | 100% | keine Werte |
| Front Wing | float64 | 100% | keine Werte |
| Brake Balance | float64 | 100% | keine Werte |
| Differential | float64 | 100% | keine Werte |
| Suspension | float64 | 100% | keine Werte |

**3 Beispielzeilen**

| Round | Track | Lap Distance | N. Laps | Cornering | Inclines | Camber | Grip | Wind (Avg. Speed) | Temperature | Humidity | Air Density | Air Pressure | Wind (Gusts) | Altitude | Roughness | Width | Rear Wing | Engine | Front Wing | Brake Balance | Differential | Suspension |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Spain | 5.1 | 60 | 99 | 72 | 31 | 94 | 92 | 10 | 68 | 26 | 63 | 76 | 20 | 4 | 9 | leer | leer | leer | leer | leer | leer |
| 2 | Belgium | 3.2 | 96 | 78 | 29 | 8 | 43 | 23 | 18 | 5 | 39 | 91 | 51 | 18 | 75 | 6 | leer | leer | leer | leer | leer | leer |
| 3 | United States of America | 2.9 | 106 | 16 | 51 | 39 | 63 | 15 | 4 | 92 | 91 | 32 | 80 | 66 | 4 | 56 | leer | leer | leer | leer | leer | leer |

### 3.7 CSV `practice_data (1).csv`

0 Zeilen × 29 Spalten.

| Spalte | Datentyp | Fehlend | Bereich |
|---|---|---|---|
| Round | unbekannt (leer) | n/a | n/a |
| Track | unbekannt (leer) | n/a | n/a |
| Qualifying | unbekannt (leer) | n/a | n/a |
| Stint | unbekannt (leer) | n/a | n/a |
| Lap | unbekannt (leer) | n/a | n/a |
| Rear Wing | unbekannt (leer) | n/a | n/a |
| Front Wing | unbekannt (leer) | n/a | n/a |
| Engine | unbekannt (leer) | n/a | n/a |
| Brake | unbekannt (leer) | n/a | n/a |
| Differential | unbekannt (leer) | n/a | n/a |
| Suspension | unbekannt (leer) | n/a | n/a |
| Fuel | unbekannt (leer) | n/a | n/a |
| Tyre Remaining | unbekannt (leer) | n/a | n/a |
| Tyre Choice | unbekannt (leer) | n/a | n/a |
| Lap Time | unbekannt (leer) | n/a | n/a |
| Lap Distance | unbekannt (leer) | n/a | n/a |
| Cornering | unbekannt (leer) | n/a | n/a |
| Inclines | unbekannt (leer) | n/a | n/a |
| Camber | unbekannt (leer) | n/a | n/a |
| Grip | unbekannt (leer) | n/a | n/a |
| Altitude | unbekannt (leer) | n/a | n/a |
| Roughness | unbekannt (leer) | n/a | n/a |
| Width | unbekannt (leer) | n/a | n/a |
| Temperature | unbekannt (leer) | n/a | n/a |
| Humidity | unbekannt (leer) | n/a | n/a |
| Wind (Avg. Speed) | unbekannt (leer) | n/a | n/a |
| Wind (Gusts) | unbekannt (leer) | n/a | n/a |
| Air Density | unbekannt (leer) | n/a | n/a |
| Air Pressure | unbekannt (leer) | n/a | n/a |

**Keine Beispielzeilen, die Datei enthält nur die Kopfzeile.**

### 3.8 CSV `race_data.csv`

0 Zeilen × 23 Spalten.

| Spalte | Datentyp | Fehlend | Bereich |
|---|---|---|---|
| Round | unbekannt (leer) | n/a | n/a |
| Track | unbekannt (leer) | n/a | n/a |
| Lap | unbekannt (leer) | n/a | n/a |
| Position | unbekannt (leer) | n/a | n/a |
| Fuel | unbekannt (leer) | n/a | n/a |
| Tyre Condition | unbekannt (leer) | n/a | n/a |
| Tyre Choice | unbekannt (leer) | n/a | n/a |
| Pit | unbekannt (leer) | n/a | n/a |
| Lap Time | unbekannt (leer) | n/a | n/a |
| Lap Distance | unbekannt (leer) | n/a | n/a |
| Cornering | unbekannt (leer) | n/a | n/a |
| Inclines | unbekannt (leer) | n/a | n/a |
| Camber | unbekannt (leer) | n/a | n/a |
| Grip | unbekannt (leer) | n/a | n/a |
| Altitude | unbekannt (leer) | n/a | n/a |
| Roughness | unbekannt (leer) | n/a | n/a |
| Width | unbekannt (leer) | n/a | n/a |
| Temperature | unbekannt (leer) | n/a | n/a |
| Humidity | unbekannt (leer) | n/a | n/a |
| Wind (Avg. Speed) | unbekannt (leer) | n/a | n/a |
| Wind (Gusts) | unbekannt (leer) | n/a | n/a |
| Air Density | unbekannt (leer) | n/a | n/a |
| Air Pressure | unbekannt (leer) | n/a | n/a |

**Keine Beispielzeilen, die Datei enthält nur die Kopfzeile.**

## 4. Stellgrößen, Ergebnisgrößen, Randbedingungen

Einteilung nach Spaltennamen und Excel-Aufbau, also eine begründete Annahme und keine Dokumentation des Simulators.

| Rolle | Spalten | Wo |
|---|---|---|
| **Stellgröße: Setup** | Rear Wing, Front Wing, Engine, Brake / Brake Balance, Differential, Suspension (ganzzahlig, 1 bis 500) | simulator, practice, Excel; in track leer |
| **Stellgröße: Strategie** | Tyre Choice, Fuel / Fuel Load (Startmenge und Menge beim Stopp), Pit Lap | practice (leer), Excel |
| **Ergebnis** | Lap Time; Race: Position | simulator; practice und race (leer) |
| **Zustand, verläuft über die Runden** | Tyre Remaining / Tyre Condition, Fuel je Runde, Lap, Stint | practice und race (leer), Excel als Formel |
| **Randbedingung, nicht wählbar** | Lap Distance, Cornering, Inclines, Camber, Grip, Altitude, Roughness, Width, Temperature, Humidity, Wind (Avg. Speed), Wind (Gusts), Air Density, Air Pressure, N. Laps, Pit Time | alle, je nach Datei |
| **Unklar** | Qualifying (Flag oder Rundenart?), Pit (Flag oder Rundennummer?) | practice, race (leer) |

**Korrektur an der Aufgabenstellung:** Temperatur ist hier keine Ergebnisgröße, sondern Wetter der Strecke. Reifentemperaturen gibt es nirgends. Verschleiß taucht nur als Reifenzustand auf, gemessene Werte dazu fehlen.

## 5. Historische Daten mit Setup und Rundenzeit

| Quelle | Setup | Rundenzeit | Zeilen | Nutzbar? |
|---|---|---|---|---|
| `simulator_data` | ja | ja | 10.000 | **Ja, einzige Quelle** |
| `practice_data` | ja | ja | 0 | Noch nicht, leer |
| `race_data` | nein | ja | 0 | Nein: leer und ohne Setup-Spalten |
| `track_data` | Spalten leer | nein | 4 | Nein, liefert nur Streckenwerte |
| Excel-Datei | Platzhalter | Platzhalter 83 s | 0 | Nein |

**Was `simulator_data` hergibt:** Rundenzeit in Abhängigkeit von Strecke und Setup, über den ganzen Wertebereich und ohne Lücken.

**Was es nicht hergibt:**

- Einfluss von Reifenmischung, Reifenzustand und Spritmenge. Diese Spalten fehlen, und mit welchen Werten die Zeilen entstanden sind, ist unbekannt.
- Rauschen des Simulators. Keine Kombination aus Strecke und Setup kommt doppelt vor, das Rauschen lässt sich also nicht direkt messen.
- Die Gewissheit, dass es derselbe Simulator ist wie bei den Testrunden. Der Dateiname legt das nahe, belegt ist es nicht. Prüfen lässt es sich erst mit den 120 Runden.

Was das bringt: Der Einfluss von Strecke und Setup lässt sich schon vorab lernen. Die 120 Testrunden können sich dann auf Sprit, Reifen und die Bestätigung des Modells konzentrieren.

## 6. Verknüpfungen

| Spalten | simulator | track | practice | race | Excel |
|---|---|---|---|---|---|
| Round, Track | – | ja | ja | ja | – |
| Lap Distance | ja | ja | ja | ja | ja |
| Cornering, Inclines, Temperature, Humidity | ja | ja | ja | ja | ja |
| Camber, Grip, Altitude, Roughness, Width | ja | ja | ja | ja | – |
| Wind (Avg. Speed), Wind (Gusts), Air Density, Air Pressure | ja | ja | ja | ja | – |
| 6 Setup-Werte | ja | ja | ja | – | ja |
| Tyre Choice | – | – | ja | ja | ja |
| Fuel | – | – | ja | ja | ja |
| Lap Time | ja | – | ja | ja | ja |
| N. Laps | – | ja | – | – | ja |
| Tyre Remaining / Tyre Condition | – | – | ja | ja | ja |
| Pit | – | – | – | ja | ja |
| Position | – | – | – | ja | – |
| Qualifying, Stint | – | – | ja | – | – |

*In track sind die Setup-Spalten leer. Excel enthält bei Tyre Choice, Fuel und Lap Time nur Eingabefelder oder Platzhalter, bei Pit die Spalten Pit und Pit Lap. Pit Time steht nur in Excel.*

| Verknüpfung | Schlüssel | Stand |
|---|---|---|
| track ↔ practice, track ↔ race | `Round` + `Track` | In track eindeutig (4 Zeilen). Gegenprobe erst möglich, wenn practice und race gefüllt sind. |
| simulator ↔ track | keiner | `simulator_data` hat weder Round noch Track. Verbindung nur über die 14 Streckenmerkmale als Modelleingaben. Exakte Treffer der 4 Strecken in simulator: **0**. Alle Streckenwerte liegen aber im abgedeckten Bereich, es wird also nicht über den Datenbereich hinaus geschätzt. |
| simulator ↔ practice | 6 Setup-Spalten + 14 Streckenmerkmale | Gleiche Größen, sobald die Namen vereinheitlicht sind (A8). |
| race ↔ Setup | nur indirekt über `Round` | race_data hat keine Setup-Spalten. |
| Excel ↔ CSV | nur gleiche Bezeichnungen | Excel hat nur 5 der 14 Streckenmerkmale. Es fehlen Camber, Grip, Roughness, Width, Altitude, beide Wind-Spalten, Air Density und Air Pressure. Keine Strecken-ID. |
| Excel-Blätter untereinander | Zellbezüge auf `Setup and Strategy` | Nur Reifennamen und Rundentabelle sind verknüpft, der Rest nicht (A6). |

**Reifenmischung als Schlüssel:** In den CSV-Dateien gibt es dazu keine Werte. Die Namen stehen nur in Excel (Extra Soft, Soft, Medium, Hard). Ob `Tyre Choice` in practice Namen oder Nummern enthalten wird, ist offen.

## 7. Auffälligkeiten

### Kritisch für das Vorhaben

**A1. Die 120 Testrunden fehlen.** `practice_data` hat 0 Zeilen. Ohne sie gibt es keine Daten zu Reifen und Sprit und keine Prüfung gegen den echten Simulator.

**A2. Rundenzeiten aus simulator und practice sind nicht direkt vergleichbar.** In practice stecken zusätzlich Sprit und Reifenzustand. In simulator sind diese Größen unbekannt, vermutlich fest. Wer beide Dateien einfach zusammenwirft, schiebt diesen Versatz dem Setup in die Schuhe.

**A3. Setups hängen von der Strecke ab.** Die Streckenmerkmale sind untereinander praktisch unabhängig (größter Betrag von r: 0,025), die Setups hängen aber von der Strecke ab. Rear Wing und Front Wing korrelieren zudem mit 0,64 untereinander. Vermutung: Die Daten stammen aus einer Regel "gutes Setup je Strecke plus Streuung". Folge: Ein Modell kann Wirkung von Setup und Strecke schwer trennen und ist abseits dieser Regel unzuverlässig, gerade dort, wo die Trim-Suche hinläuft.

| Setup | Anteil = 1 | Anteil = 500 | Median | R² linear aus Strecke | Stärkstes Streckenmerkmal (r) |
|---|---|---|---|---|---|
| Rear Wing | 3.8% | 16.2% | 341 | 0.65 | Air Density (-0.37) |
| Engine | 37.0% | 0.6% | 45 | 0.34 | Grip (+0.28) |
| Front Wing | 8.2% | 5.6% | 231 | 0.66 | Cornering (+0.46) |
| Brake Balance | 13.7% | 1.6% | 161 | 0.61 | Cornering (+0.51) |
| Differential | 23.1% | 2.0% | 116 | 0.59 | Cornering (+0.43) |
| Suspension | 11.3% | 0.1% | 140 | 0.35 | Grip (+0.36) |

**A4. Häufung an den Grenzen 1 und 500.** Engine steht in 37% der Zeilen auf 1, Differential in 23%, Rear Wing in 16% auf 500. 64% der Zeilen haben mindestens einen Wert auf 1, 22% mindestens einen auf 500. Nur 26% der Zeilen liegen bei allen sechs Werten im Inneren. Vermutung: Die Werte wurden an den Grenzen abgeschnitten. Dann wären die Bereiche nahe den Grenzen schlecht abgedeckt, und 1 und 500 wären harte Grenzen für die Suche. Suspension erreicht 500 nur in 5 Zeilen (Maximum auffällig dünn besetzt), Engine liegt in nur 7% der Zeilen bei 250 oder höher.

**A5. Das Setup-Signal ist klein im Vergleich zur Streckenlänge.** Rundenzeit und Lap Distance korrelieren mit 0,999. Je Kilometer liegt die Zeit nur zwischen 18,71 und 19,77 s (Mittel 19,20, Standardabweichung 0,16), bei mittlerer Länge also rund 0,66 s je Runde. Die rohe Korrelation der Setups mit der Rundenzeit liegt deshalb bei fast 0. Das heißt nicht, dass Setups egal sind, sondern dass die Länge alles überdeckt. Ein Bewertungsmaß auf der rohen Rundenzeit sieht darum auch bei einem schlechten Modell sehr gut aus.

### Fehlerquellen in der Excel-Datei

**A6. Felder "from main sheet (do not edit here)" sind nicht verknüpft.** In `Lap Time`, `Fuel Consumption` und `Tyre Wear` sind Strecke, Setup, Sprit und Boxenrunde feste Zahlen ohne Formel (im Datei-XML geprüft). Nur die Reifennamen sind verknüpft. Vor allem rechnet `Fuel Consumption!M6 = 0.5*D9` mit der lokalen Kopie. Ändert man die Streckenlänge im Hauptblatt, bleibt der Verbrauch falsch.

**A7. Vorhersage der Rennzeit ist ein Platzhalter und ignoriert Boxenstopps.**

- `Q2` ist die reine Summe der Rundenzeiten: 88 × 83 s = 7304 s = 02:01:44. `Pit Time` (`D10`, 30 s) wird in keiner Formel verwendet, 4 Stopps fehlen also in der Rennzeit.
- Rundenzeit ist fest 83 s, unabhängig von Setup, Reifen und Sprit. Das sind 23,3 s/km gegenüber 19,2 s/km in `simulator_data` (bei 3,56 km wären das etwa 68 s).
- Verbrauch ist fest 0,5 l/km. Der Reifenverschleiß ist je Mischung konstant (1,78 / 1,48 / 1,28 / 1,08 % pro Runde) und unabhängig von der Strecke. Auffällig: 1,78 % bei Extra Soft entspricht zahlenmäßig genau den 1,78 l/Runde beim Verbrauch. Das sieht eher nach gesetzter Startzahl als nach Messwert aus.

**A7b. Kleinere Rechenlogik.**

- Fuel Load beim Stopp ist die neue Gesamtmenge, nicht die nachgefüllte Menge.
- Die Tabelle zeigt den Zustand am Rundenende (Runde 1 bereits 48,22 l statt 50 l, 98 % statt 100 %).
- Die erste Tabellenzeile (`N7`, `O7`) schaut auf `J8` statt auf `J7`. Ein Stopp in Runde 2 würde schon in Runde 1 erscheinen.
- Keine Sperre gegen leeren Tank oder Reifenzustand unter 0.
- Die Tabelle fasst höchstens 110 Runden. Das reicht für alle 4 Strecken (Maximum 106).
- Die Dropdown-Felder speichern Nummern statt Namen: 2 = Extra Soft. Nummer 1 ist leer, die Zählung ist also um eins verschoben.

### Einheiten und Benennung

**A8. Uneinheitliche Namen und Reihenfolgen.** `Brake` (practice, Excel) gegen `Brake Balance` (simulator, track). `Tyre Remaining` (practice) gegen `Tyre Condition` (race, Excel). `Fuel` gegen `Fuel Load`. Die Spaltenreihenfolge der Setups unterscheidet sich ebenfalls: practice hat Rear Wing, Front Wing, Engine; simulator und track haben Rear Wing, Engine, Front Wing. Spalten darum immer nach Namen zuordnen, nie nach Position.

**A9. Einheiten fehlen, und viele Spalten sind offenbar Kennzahlen statt Messwerte.** Air Pressure, Air Density und Altitude laufen von 0 bis 100 und sind damit weder hPa noch kg/m³ noch Meter. Wind hat keine Einheit. Temperature läuft von 0 bis 40 (°C laut Excel). Lap Distance ist in km (laut Excel), Lap Time in Sekunden. Das passt zusammen: im Schnitt 187,5 km/h, Spanne 182,1 bis 192,5 km/h. Ein Einheitenfehler in der Rundenzeit ist damit nicht zu erkennen.

**A10. Excel-Startwerte passen nicht zur CSV-Skala.** Cornering und Inclines stehen dort auf 5, in den CSV-Dateien reicht die Skala von 0 bis 100. Lap Distance ist 3,56 km, in den CSV-Dateien gibt es nur 0,1-km-Schritte. Ob Excel dieselbe Skala meint, ist unklar. Die 250 je Setup-Wert sind die Bereichsmitte, liegen aber bei Engine weit über der Masse der Daten (Median 45).

### Physikalisch unplausibel, also wohl künstlich erzeugt

**A11. Streckenwerte verhalten sich nicht wie echte Physik.**

- Air Density ist unabhängig von Air Pressure, Altitude und Temperature (größter Betrag von r: 0,019).
- Böen sind in 49% der Zeilen schwächer als der Durchschnittswind, auch in Spanien (Wind 92, Böen 76).

Die Werte sind offenbar künstlich und gleichmäßig gezogen. Folge: Sie als unabhängige Eingaben behandeln und kein physikalisches Vorwissen einbauen.

### Geprüft und unauffällig

- `simulator_data`: keine fehlenden Werte und keine doppelten Zeilen. Ausreißer der Rundenzeit nach der Regel 1,5 × Quartilsabstand: 0, auf Zeit je km: 46.
- Streckenmerkmale in simulator sind gleichmäßig verteilt und decken ihren Bereich voll ab. Die Häufigkeit des Werts 0 ist normal, das sind keine versteckten fehlenden Werte.
- Streckenlänge × Runden in track_data: 306,0 / 307,2 / 307,4 / 307,8 km. Das passt zur üblichen Renndistanz von rund 305 km. Excel kommt mit 88 × 3,56 auf 313,3 km.
- Die Power-Query-Abfrage in der Excel-Datei ist leer, es gibt keine ausgeblendeten Blätter, Zeilen oder Spalten, keine Makros und keine Kommentare.
- Dateinamen mit `(1)` und `(2)` sehen nach Download-Kopien aus. Falls es neuere Fassungen gibt, müsste die Auswertung wiederholt werden.

## 8. Offene Fragen

1. **Woher kommen die 120 Testrunden?** Müssen sie erst im Simulator gefahren werden, oder fehlt eine Datei? Davon hängt alles Weitere ab.
2. **Sind die vorliegenden `practice_data` und `race_data` wirklich die aktuelle Fassung?** Beide haben nur die Kopfzeile.
3. **Mit welchem Sprit und welchen Reifen entstand `simulator_data`?** Das steht vielleicht in der Aufgabenbeschreibung.
4. **Sollen die Dateien nach `data/raw/` umziehen?** Empfehlung: ja, damit die Rohdaten klar getrennt sind. Noch nicht erledigt, weil es nicht beauftragt war.
