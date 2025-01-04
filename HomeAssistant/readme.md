!!! Achtung - work in progress - hier passieren noch jede Menge Änderungen !!!
Einbindung einer Trovis 557x in Home Assistant:

- Schritt 1: Inhalt der configuration.yaml in die eigene Datei einfügen (Datei liegt im Root-Verzeichnis von HA).
- Schritt 2: Inhalt der secrets.yaml in die eigene Datei einfügen und ggf. anpassen (Datei liegt im Root-Verzeichnis von HA).
- Schritt 3: Im Root-Verzeichnis von HA ein Verzeichnis trovis557x erstellen, Inhalt von trovis557x/* hineinkopieren.
- Schritt 4: Den Inhalt von www in das eigene www-Verzeichnis kopieren (nur notwendig, wenn die Visualisierung übernommen werden soll).
- Schritt 5: Neustart von HA, danach home-assistant.log auf mögliche Fehler prüfen.

Hinweis: Die Dateistruktur entspricht der von Home Assistant, beginnend mit dem HA-Rootverzeichnis. Der Hauptteil der Konfiguration befindet sich nach Funktion geordnet im Verzeichnis trovis557x/. Grund dafür ist, späteren Einsteigern die Einarbeitung in die verschiedenen Reglermodelle mit ihren verschiedenen Funktionen, Sensoren und der Anzahl der Heizkreise zu vereinfachen.

![image](https://github.com/user-attachments/assets/8cea7360-2cf3-4bdc-adca-aaf51222f315)

![image](https://github.com/user-attachments/assets/028b1e60-2d0a-4b1e-8bbe-269102a0cb8a)

