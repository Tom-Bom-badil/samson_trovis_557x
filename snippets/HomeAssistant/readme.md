In diesem Bereich finden sich verschiedene Code-Snippets. ALLE (!) Snippets sind **work-in-progress** und noch nicht fertiggestellt - sie sollen nur dem Einstieg in diese Bereiche der Trovis-Visualisierung in Home Assistant dienen. Hilfe ist gern willkommen!

# **Die Originalvorlage**
Diese komplett interaktive Ansicht habe ich ca. 2014 begonnen - seit 2019 ist sie fast unverändert, es werden im Minutentakt Daten gelogged und visualisiert. Das Backend ist SmartHomeNG, das Frontend die smartVISU. Ziel meines HA-Projektes ist, diese Anzeige so originalgetreu wie möglich in HA zu implementieren (mit einigen verbesserungen).

Hier ein Screenshot aus der Heizperiode:
![__Vorlage - smartVISU im Einsatz__](https://github.com/user-attachments/assets/dd0faec7-c7be-47ee-b9c6-371eeabb3a05)

# **Datei seitenaufteilung.yaml**

Ziel: Eine Konzept für die Aufteilung der Reglervisualisierung mit automatischer Anpassung an verschiedene Auflösungen (Heizungsschema interaktiv links oben, Reglerbild interaktiv links unten, rechts 3 Graphen mit Export-Funktionen etc).

Das Grundgerüst:
![seitenaufteilung](https://github.com/user-attachments/assets/374489ba-a67d-4748-b063-ee1df406f228)

Heizung aus (Status 0):
![seitenaufteilung_status_0](https://github.com/user-attachments/assets/af327bf7-d65c-4389-8d86-f91769436e28)

Heizbetrieb (Status 1):
![seitenaufteilung_status_1](https://github.com/user-attachments/assets/d53d4dff-0039-4419-b8c1-e6f99d5e1e1e)

Warmwasserbereitung (Status 2):
![seitenaufteilung_status_2](https://github.com/user-attachments/assets/ec061fe8-5640-43bb-b2e6-92120e75610d)

# **Datei reglerbild_interaktiv.yaml**
Ziel: Darstellung einer 5575/5576/5579 mit interaktiven Elementen und der tatsächlichen Heizkurve und aktuellem VL als plotly-Graph.

![reglerbild_interaktiv](https://github.com/user-attachments/assets/d9cff9b5-2bd7-4564-8b1c-4be8c340e9a5)

# **Datei plotly.yaml**
Ziel: Einbindung eines Graphen per plotly. Die Plotly-Bibliothek ist extrem gut dokumentiert und meiner Meinung nach nicht so buggy und deutlich flexibler / mächtiger als die üblicherweise verwendenten Lösungen wie HistoryGraphCard oder ApexCharts. Doku [hier](https://plotly.com/javascript). ACHTUNG! Die Beispieldatei enthält einen Datensimulator, der für 48h Daten generiert (zur Winterzeit --> daher sieht man zur Sommerzeit eine Stunde Versatz bzw. rechts einen 1h freien Bereich). Für die Visualisierung von Echtdaten muss die entsprechende entity: statt der fn: angebunden werden. Für einen Plot sollte die Entity bereits historische Werte aus einer Datenbank liefern.

Bereich R1 (rechts oben):
![plotly_1](https://github.com/user-attachments/assets/4e264bbf-5d39-43ae-a783-4ce92bb04e4d)

Heizkurve auf dem Regler:

![plotly_2](https://github.com/user-attachments/assets/5bc4732e-2dc4-48da-b3d8-2964ac58fbba)
