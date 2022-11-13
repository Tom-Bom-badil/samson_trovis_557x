Ein smartHomeNG Plugin zum Auslesen von SAMSON TROVIS 557x Automationssystemen (Heizungsregler).

Unterstützt werden alle Modelle mit Modbus (5571, 5573, 5576, 5578, 5579).

Einige Teile des Projektes können auch für die Anbindung des Reglers an TrovisView verwendet werden.

Weitere Details sind im [Wiki](https://github.com/Tom-Bom-badil/samson_trovis_557x/wiki) zu finden.

------------

A smartHomeNG plugin to read out SAMSON TROVIS 557x Heating Automation Controllers.

The plugin supports all Modbus models (5571, 5573, 5576, 5578, 5579).

Some parts of the project can also be used to connect the controller to TrovisView.

Further details can be found on the [Wiki](https://github.com/Tom-Bom-badil/samson_trovis_557x/wiki) (German).


<br/><br/><br/><br/>
Changelog Version 2 (yet to come, please ignore for now):

2.0.0<br/>
Added ModbusTCP support (for adapters with built-in TCP/RTU gateway like USR-TCP-K7)<br/>
Added support for Python 3.8+ (auto-switch between pymodbus2.2+/3.0+)<br/>
Changed connection behaviour - moved connect() from startup into regular runs and added disconnect()<br/>
Updated register/coil tables, added new information, revised existing information<br/>
Updated items - important: formerly wrongly addressed Rk3 is now Rk4<br/>
Updated plugin.yaml: Rev 2 in format x.x.x, status 'ready', added 'werte' attribute to prevent errors in log<br/>
Removed unnecessary development files (templates, tools, assets) from official shNG Plugins repo<br/>
Updated Wiki, included A LOT of useful background information: github.com/Tom-Bom-badil/samson_trovis_557x/wiki
