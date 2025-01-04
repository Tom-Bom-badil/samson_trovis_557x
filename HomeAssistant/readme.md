!!! Achtung - work in progress - hier passieren noch jede Menge Änderungen !!!
Einbindung einer Trovis 557x in Home Assistant:

- Schritt 1: Inhalt der configuration.yaml in die eigene Datei einfügen (Datei liegt im Root-Verzeichnis von HA).
- Schritt 2: Inhalt der secrets.yaml in die eigene Datei einfügen und ggf. anpassen (Datei liegt im Root-Verzeichnis von HA).
- Schritt 3: Im Root-Verzeichnis von HA ein Verzeichnis trovis557x erstellen, Inhalt von trovis557x/* hineinkopieren.
- Schritt 4: Den Inhalt von www in das eigene www-Verzeichnis kopieren (nur notwendig, wenn die Visualisierung übernommen werden soll).
- Schritt 5: Neustart von HA, danach home-assistant.log auf mögliche Fehler prüfen.

Hinweis: Die Dateistruktur entspricht der von Home Assistant, beginnend mit dem HA-Rootverzeichnis. Der Hauptteil der Konfiguration befindet sich nach Funktion geordnet im Verzeichnis trovis557x/. Grund dafür ist, späteren Einsteigern die Einarbeitung in die verschiedenen Reglermodelle mit ihren verschiedenen Funktionen, Sensoren und der Anzahl der Heizkreise zu vereinfachen.

![image](https://github.com/user-attachments/assets/dc3795b2-d6b7-486f-8bde-55d3f148b2f4)

![image](https://github.com/user-attachments/assets/26e20b98-6936-40a5-9f47-650bb71c301e)

![image](https://github.com/user-attachments/assets/a82bb47d-ffe4-4405-bba8-783470814d56)
