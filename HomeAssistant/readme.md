-work in progress-

Hinweis: Der Hauptteil der Konfiguration befindet sich nach Funktion geordnet im Verzeichnis trovis557x/. Grund dafür ist, späteren Neulingen die Einarbeitung in die verschiedenen Reglermodelle mit den verschiedenen Funktionen, Sensoren und Anzahl Heizkreise zu vereinfachen.

Leider habe ich bis jetzt trotz stundenlangen Herumprobierens noch nicht herausgefunden, wie man sensors, binary_sensors und switches in einer einzigen Datei zusammenfassen und dann per !include_dir_merge_list einbinden kann, also z.B. 

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

Daher liegen die Dateien bis jetzt in separaten Unterverzeichnissen und werden in der configuration.yaml wie folgt eingebunden:
```
modbus:
  - trovis:
    [...]
    sensors: !include_dir_merge_list trovis557x/sensors/
    binary_sensors: !include_dir_merge_list trovis557x/binary_sensors/
    switches: !include_dir_merge_list trovis557x/switches/
```

Ziel ist aber definitiv eine Zusammenfassung, so dass am Ende nur 9 Dateien im Hauptverzeichnis statt wie jetzt 3x9 Dateien in 3 Unterverzeichnissen übrig sind. Falls jemand einen Tip hat, wie man das bewerkstelligen kann und wie die configuration.yaml dafür auszusehen hat - vielen Dank im Voraus! :)
