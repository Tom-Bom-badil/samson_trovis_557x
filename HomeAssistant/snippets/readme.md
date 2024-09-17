In diesem Bereich finden sich verschiedene Code-Snippets. ALLE (!) Snippets sind work-in-progress und noch nicht fertiggestellt - sie sollen nur dem Einstieg in diese Bereiche der Trovis-Visualisierung dienen. Hilfe ist gern willkommen!

**Die Originalvorlage**
---
Diese komplett interaktive Ansicht habe ich vor ca. 10 Jahren begonnen - seit 6 Jahren ist sie unverändert. Das Backend ist SmartHomeNG, das Frontend die smartVISU. Ziel meines HA-Projektes ist, diese Anzeige so originalgetreu wie möglich in HA zu implementieren (mit einigen verbesserungen).

![__Vorlage - smartVISU im Einsatz__](https://github.com/user-attachments/assets/dd0faec7-c7be-47ee-b9c6-371eeabb3a05)

**plotly**
---
Einbindung eines Graphen per plotly. Die Plotly-Bibliothek ist extrem gut dokumentiert und meiner Meinung nach nicht so buggy und deutlich flexibler / mächtiger als die üblicherweise verwendenten Lösungen wie HistoryGraphCard oder ApexCharts. Doku hier: https://plotly.com/javascript. ACHTUNG! Das Beispiel enthält einen Datensimulator, der für 48h Livedaten aufbaut (in Winterzeit; daher sieht man zur Sommerzeit eine Stunde Versatz bzw. rechts einen 1h freien Bereich). Für die Visualisierung von Echtdaten muss die entsprechende entity: statt der fn: angebunden werden. Für einen Plot sollte die Entity historische Werte aus einer Datenbank liefern.^

![plotly_1](https://github.com/user-attachments/assets/4e264bbf-5d39-43ae-a783-4ce92bb04e4d)
![plotly_2](https://github.com/user-attachments/assets/5bc4732e-2dc4-48da-b3d8-2964ac58fbba)

**reglerbild_interaktiv**
---
Darstellung einer 5575/5576/5579 mit interaktiven Elementen und der tatsächlichen Heizukurve und aktuellem VL als plotly-Graph.

![reglerbild_interaktiv](https://github.com/user-attachments/assets/d9cff9b5-2bd7-4564-8b1c-4be8c340e9a5)

**seitenaufteilung**
---
Eine Konzept für die Aufteilung der Reglervisualisierung mit automatischer Anpassung an verschiedene Auflösungen (Heizungsschema interaktiv links oben, Reglerbild interaktiv links unten, rechts 3 Graphen mit Export-Funktionen etc).

![seitenaufteilung](https://github.com/user-attachments/assets/374489ba-a67d-4748-b063-ee1df406f228)
![seitenaufteilung_status_0](https://github.com/user-attachments/assets/af327bf7-d65c-4389-8d86-f91769436e28)
![seitenaufteilung_status_1](https://github.com/user-attachments/assets/d53d4dff-0039-4419-b8c1-e6f99d5e1e1e)
![seitenaufteilung_status_2](https://github.com/user-attachments/assets/ec061fe8-5640-43bb-b2e6-92120e75610d)
