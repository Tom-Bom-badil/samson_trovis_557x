!!! Achtung - work in progress - hier passieren noch jede Menge Änderungen !!!
Einbindung einer Trovis 557x in Home Assistant:

- Schritt 1: Inhalt der configuration.yaml in die eigene Datei einfügen (Datei liegt im Root-Verzeichnis von HA).
- Schritt 2: Inhalt der secrets.yaml in die eigene Datei einfügen und ggf. anpassen (Datei liegt im Root-Verzeichnis von HA).
- Schritt 3: Im Root-Verzeichnis von HA ein Verzeichnis trovis557x erstellen, Inhalt von trovis557x/* hineinkopieren.
- Schritt 4: Den Inhalt von www in das eigene www-Verzeichnis kopieren (nur notwendig, wenn die Visualisierung übernommen werden soll).
- Schritt 5: Neustart von HA, danach home-assistant.log auf mögliche Fehler prüfen.

Hinweis: Die Dateistruktur entspricht der von Home Assistant, beginnend mit dem HA-Rootverzeichnis. Der Hauptteil der Konfiguration befindet sich nach Funktion geordnet im Verzeichnis trovis557x/. Grund dafür ist, späteren Einsteigern die Einarbeitung in die verschiedenen Reglermodelle mit ihren verschiedenen Funktionen, Sensoren und der Anzahl der Heizkreise zu vereinfachen.

![image](https://github.com/user-attachments/assets/8a63f0f1-9b86-4e58-8d63-7ef36a1bdbc8)

![image](https://github.com/user-attachments/assets/9e5afcb6-dc93-482a-af58-27dabdc65364)

![image](https://github.com/user-attachments/assets/92a11eab-7830-4968-a9ad-f55ce3d4e378)

![image](https://github.com/user-attachments/assets/316d281d-3a5d-4682-aa76-038e5564cf59)
