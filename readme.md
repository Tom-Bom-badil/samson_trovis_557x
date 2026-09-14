[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-%2341BDF5.svg)](https://www.home-assistant.io)
[![Custom integration](https://img.shields.io/badge/Custom%20Integration-%2341BDF5.svg)](https://www.home-assistant.io/getting-started/concepts-terminology)
[![Release](https://img.shields.io/github/v/release/Tom-Bom-badil/trovis-modbus-hass?include_prereleases&color=41BDF5)](https://github.com/Tom-Bom-badil/trovis-modbus-hass/releases)
[![HACS Custom Repository](https://img.shields.io/badge/HACS-not%20applied%20yet-orange.svg)](https://www.hacs.xyz/docs/faq/custom_repositories/)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://GitHub.com/Tom-Bom-badil/home-assistant_helios-vallox/graphs/commit-activity)
[![CI](https://img.shields.io/github/actions/workflow/status/Tom-Bom-badil/trovis-modbus-hass/ci.yml?branch=develop&label=CI&color=green)](https://github.com/Tom-Bom-badil/trovis-modbus-hass/actions/workflows/ci.yml)
[![HA Analytics](https://img.shields.io/badge/dynamic/json?url=https://analytics.home-assistant.io/custom_integrations.json&query=$.trovis557x.total&label=HA%20Analytics&suffix=%20installations%20%2A&color=green)](https://analytics.home-assistant.io/)


## SAMSON TROVIS 557x – Home Assistant Custom Integration

<img width="100%" alt="SAMSON TROVIS controllers" src="https://github.com/user-attachments/assets/2afe0be0-614a-4dbd-9fdc-4132434ffd36" />

<br/>

This is a Home Assistant custom integration for monitoring and
adjusting SAMSON TROVIS 557x heating and district heating controllers over
Modbus, including compatible OEM variants from Sauter, Pewo, Yados and others.

The integration is intended primarily for simple monitoring of an already
commissioned system, and for occasional fine adjustment.

The integration automatically detects the controller model, configured hydronic
system, technical control-circuit roles, and available physical sensor inputs.
It then automatically creates a matching Home Assistant device and entity structure.

The TROVIS controller continues to perform the actual heating control. Home
Assistant reads its operating state and, when explicitly enabled, writes
supported settings back to it.

## 👉 Features

Depending on the detected controller and hydronic configuration, the integration
provides:
- UI-based setup without Modbus YAML or a separate Modbus integration,
- native Modbus TCP, RTU over TCP, and serial Modbus RTU connections,
- support for multiple independently configured controllers,
- automatic controller-model and hydronic-system identification,
- model-, role-, and configuration-aware entity selection,
- linked sub-devices for Measurements, Rk1-Rk4, Solar, and buffer-tank functions,
- Home Assistant `sensor`, `binary_sensor`, `number`, `select`, `switch`, `date`,
  `time`, `climate` and `water_heater` entities,
- grouped reads and validated register and coil writes,
- a controller-level **Write access** safety switch,
- German and English translations.

## 👉 Supported controllers

The following controllers are currently supported:

- SAMSON TROVIS 5573, 5573-1, 5575, 5576, 5578, 5578-E, 5579
- SAUTER EQJW-126F001, -146F001, -146F002, -246F002, -246F003
- YADOS YADO\|MATIC 01, 01-0003, 03, 03-1003, 08
- PEWO PCR06

<sup>(for details, see the [project wiki](https://github.com/Tom-Bom-badil/trovis-modbus-hass/wiki/Supported-controllers))</sup>

## 👉 Related projects

- [`trovis-modbus`](https://github.com/Tom-Bom-badil/trovis-modbus) –
  a generic library that contains a controller-specific data model and read/write logic
- [`modbus-connection`](https://github.com/home-assistant-libs/modbus-connection) –
  a backend-neutral Modbus connection API used internally by the integration

## 👉 Documentation

Lots of in-depth insights into how everything works, including installation
instructions, adapter configuration and tests, troubleshooting guides and
technical backgrounds can be found on the [project wiki](https://github.com/Tom-Bom-badil/trovis-modbus-hass/wiki).

If any information you are searching for should be missing on this Wiki, check
out the [Wiki](https://github.com/Tom-Bom-badil/samson_trovis_557x/wiki) and the
[discussions](https://github.com/Tom-Bom-badil/samson_trovis_557x/discussions) of
the 'old' Trovis project, where we have collected information on the controller
and Modbus in general over many years.
