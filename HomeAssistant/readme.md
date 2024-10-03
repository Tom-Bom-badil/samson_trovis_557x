!!! Achtung - work in progress !!!
Einbindung einer Trovis 557x in Home Assistant:

- Schritt 1: Inhalt der configuration.yaml kopieren (Datei liegt im Root-Verzeichnis von HA)
- Schritt 2: Inhalt der secrets.yaml kopieren und ggf. anpassen (Datei liegt im Root-Verzeichnis von HA)
- Schritt 3: Im Root-Verzeichnis von HA ein Verzeichnis trovis557x erstellen und Inhalte von trovis557x hineinkopieren.
- Schritt 4: Neustart von HA, danach home-assistant.log auf mögliche Fehler prüfen.

Hinweis: Die Dateistruktur entspricht der von Home Assistant, beginnend mit dem HA-Rootverzeichnis. Der Hauptteil der Konfiguration befindet sich nach Funktion geordnet im Verzeichnis trovis557x/. Grund dafür ist, späteren Einsteigern die Einarbeitung in die verschiedenen Reglermodelle mit ihren verschiedenen Funktionen, Sensoren und der Anzahl der Heizkreise zu vereinfachen.
