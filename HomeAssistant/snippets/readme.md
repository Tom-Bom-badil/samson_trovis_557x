In diesem Bereich finden sich verschiedene Code-Snippets. ALLE (!) Snippets sind work-in-progress und noch nicht fertiggestellt - sie sollen nur dem Einstieg in diese Bereiche der Trovis-Visualisierung dienen. Hilfe ist gern willkommen!

- **plotly**: Einbindung eines Graphen per plotly. Die Plotly-Bibliothek ist extrem gut dokumentiert und meiner Meinung nach nicht so buggy und deutlich flexibler / mächtiger als die üblicherweise verwendenten Lösungen wie HistoryGraphCard oder ApexCharts. Doku hier: https://plotly.com/javascript. ACHTUNG! Das Beispiel enthält einen Datensimulator, der für 48h Livedaten aufbaut (in Winterzeit; daher sieht man zur Sommerzeit eine Stunde Versatz bzw. rechts einen 1h freien Bereich). Für die Visualisierung von Echtdaten muss die entsprechende entity: statt der fn: angebunden werden. Für einen Plot sollte die Entity historische Werte aus einer Datenbank liefern.^

![plotly_1](https://github.com/user-attachments/assets/4e264bbf-5d39-43ae-a783-4ce92bb04e4d)
![plotly_2](https://github.com/user-attachments/assets/5bc4732e-2dc4-48da-b3d8-2964ac58fbba)

- **reglerbild_interaktiv**: Darstellung einer 5575/5576/5579 mit interaktiven Elementen und der tatsächlichen Heizukurve und aktuellem VL als plotly-Graph.

- **seitenaufteilung**: Eine Konzept für die Aufteilung der Reglervisualisierung mit automatischer Anpassung an verschiedene Auflösungen (Heizungsschema interaktiv links oben, Reglerbild interaktiv links unten, rechts 3 Graphen mit Export-Funktionen etc).
