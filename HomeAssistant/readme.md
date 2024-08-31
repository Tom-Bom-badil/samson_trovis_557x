-work in progress-

Hinweis: Der Hauptteil der Konfiguration befindet sich im Verzeichnis trovis557x/. Leider habe ich bis jetzt nocht nicht herausgefunden, wie man sensors, binary_sensors und switches in einer einzigen Datei zusammenfassen und dann per !include_dir_merge_list einbinden kann, also z.B. 

_trovis557x/1_regler.yaml_
```
sensors:
  [...]
binary sensors:
  [...]
switches:
  [...]
```

_trovis557x/2_messwerte.yaml_
```
sensors:
  [...]
binary sensors:
  [...]
switches:
  [...]
```

Daher liegen die Dateien bis jetzt in separaten Unterverzeichnissen. Ziel ist aber definitiv die Zusammenfassung, so dass am Ende nur 9 Dateien im Hautverzeichnis statt wie jetzt 3x9 Dateien in 3 Unterverzeichnissen übrig sind. Falls jemand einen Tip hat, wie man das bewerkstelligen kann und was dafür wie in der configuration.yaml einzustellen ist - vielen Dank im Voraus! :)
