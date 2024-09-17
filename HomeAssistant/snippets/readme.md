In diesem Bereich finden sich verschiedene Code-Snippets. ALLE (!) Snippets sind work-in-progress und noch nicht fertiggestellt - sie sollen nur dem Einstieg in diese Bereiche der Trovis-Visualisierung dienen. Hilfe ist gern willkommen!

- **plotly**: Einbindung eines Graphen per plotly. Die Plotly-Bibliothek ist sehr gut dokumentiert und meiner Meinung nach nicht so buggy und deutlich flexibler / mächtiger als die üblicherweise verwendenten Lösungen wie HistoryGraphCard oder ApexCharts. ACHTUNG! Das Beispiel enthält einen Datensimulator, der für 24h Livedaten aufbaut (in Winterzeit; daher zur Sommerzeit eine Stunde Versatz bzw. rechts 1h ein freier Bereich). Für die Visualisierung von Echtdaten muss hier die entsprechende Entity angebunden werden, die historische Werte aus einer Datenbank liefert.

- **reglerbild_interaktiv**: Darstellung einer 5575/5576/5579 mit interaktiven Elementen und der tatsächlichen Heizukurve und aktuellem VL als plotly-Graph.

- **seitenaufteilung**: Eine Konzept für die Aufteilung der Reglervisualisierung mit automatischer Anpassung an verschiedene Auflösungen (Heizungsschema interaktiv links oben, Reglerbild interaktiv links unten, rechts 3 Graphen mit Export-Funktionen etc).
