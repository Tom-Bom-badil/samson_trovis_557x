!!! Achtung - work in progress - hier passieren noch jede Menge Änderungen !!!
Einbindung einer Trovis 557x in Home Assistant:

- Schritt 1: Inhalt der configuration.yaml in die eigene Datei einfügen (Datei liegt im Root-Verzeichnis von HA).
- Schritt 2: Inhalt der secrets.yaml in die eigene Datei einfügen und ggf. anpassen (Datei liegt im Root-Verzeichnis von HA).
- Schritt 3: Im Root-Verzeichnis von HA ein Verzeichnis trovis557x erstellen, Inhalt von trovis557x/* hineinkopieren.
- Schritt 4: Den Inhalt von www in das eigene www-Verzeichnis kopieren (nur notwendig, wenn die Visualisierung übernommen werden soll).
- Schritt 5: Neustart von HA, danach home-assistant.log auf mögliche Fehler prüfen.

Hinweis: Die Dateistruktur entspricht der von Home Assistant, beginnend mit dem HA-Rootverzeichnis. Der Hauptteil der Konfiguration befindet sich nach Funktion geordnet im Verzeichnis trovis557x/. Grund dafür ist, späteren Einsteigern die Einarbeitung in die verschiedenen Reglermodelle mit ihren verschiedenen Funktionen, Sensoren und der Anzahl der Heizkreise zu vereinfachen.

![image](https://github.com/user-attachments/assets/c27cad37-3027-41fa-821b-be60f6041b46)

![image](https://github.com/user-attachments/assets/05d79fef-cf0c-4b21-bc91-885f22d78bb3)

![image](https://github.com/user-attachments/assets/92a11eab-7830-4968-a9ad-f55ce3d4e378)

![image](https://github.com/user-attachments/assets/d7974209-d3f7-496b-ae59-3bad29d2d3f8)
