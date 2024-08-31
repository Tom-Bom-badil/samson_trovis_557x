-work in progress-

Hinweis: Der Hauptteil der Konfiguration befindet sich im Verzeichnis trovis557x/. Leider habe ich es bis jetzt nocht nicht herausgefunden, wie man sensors, binary_sensors und switches in einer einzigen Datei zusammenfassen kann, also z.B. 

trovis557x/1_regler.yaml
```
sensors:
  [...]
binary sensors:
  [...]
switches:
  [...]
```

trovis557x/2_messwerte.yaml
```
sensors:
  [...]
binary sensors:
  [...]
switches:
  [...]
```

Daher liegen die Dateien bis jetzt in separaten Unterverzeichnissen. Ziel ist aber definitiv die Zusammenfassung, so dass am Ende nur 9 Dateien übrig sind.
Falls jemand einen Tip hat, wie man das bewerkstelligen kann und was dafür wie in der configuration.yaml einzustellen ist - vielen Dank im Voraus! :)
