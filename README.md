[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-%2341BDF5.svg)](https://www.home-assistant.io)
[![Custom integration](https://img.shields.io/badge/Custom%20Integration-%2341BDF5.svg)](https://www.home-assistant.io/getting-started/concepts-terminology)
[![Release](https://img.shields.io/github/v/release/Tom-Bom-badil/samson_trovis_557x?include_prereleases&color=41BDF5)](https://github.com/Tom-Bom-badil/samson_trovis_557x/releases)
[![HACS Custom Repository](https://img.shields.io/badge/HACS-not%20applied%20yet-orange.svg)](https://www.hacs.xyz/docs/faq/custom_repositories/)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://GitHub.com/Tom-Bom-badil/samson_trovis_557x/graphs/commit-activity)
[![CI](https://img.shields.io/github/actions/workflow/status/Tom-Bom-badil/samson_trovis_557x/ci.yml?branch=develop&label=CI&color=green)](https://github.com/Tom-Bom-badil/samson_trovis_557x/actions/workflows/ci.yml)
[![HA Analytics](https://img.shields.io/badge/dynamic/json?url=https://analytics.home-assistant.io/custom_integrations.json&query=$.samson_trovis_557x.total&label=HA%20Analytics&suffix=%20installations%20%2A&color=green)](https://analytics.home-assistant.io/)


## Samson Trovis 557x – Home Automation Integrations

<img width="100%" alt="SAMSON TROVIS controllers" src="https://github.com/user-attachments/assets/2afe0be0-614a-4dbd-9fdc-4132434ffd36" />

<br/>

This GitHub Repo contains a Home Assistant custom integration for monitoring and
adjusting SAMSON TROVIS 557x heating and district heating controllers over
Modbus, including compatible OEM variants from Sauter, Pewo, Yados and others.

It is the successor of previous Trovis projects for other home automation systems that have been around since ~2016, and of the HA Modbus YAML configuration for Trovis that has grown over the last couple of years.

The integration is primarily intended for easy monitoring of an already
commissioned system, and for occasional fine adjustment.

The integration automatically detects the controller model, configured hydronic
system, technical control-circuit roles, and available physical sensor inputs.
It then automatically creates a matching Home Assistant device and entity structure.

The TROVIS controller continues to perform the actual heating control. Home
Assistant reads its operating state and, when explicitly enabled, writes
supported settings back to it.

## 👉 Installation

Install the integration through HACS, restart Home Assistant and add
**SAMSON TROVIS 557x** under **Settings → Devices & services → Add integration**. See the [Installation and Setup](https://github.com/Tom-Bom-badil/samson_trovis_557x/wiki/Installation-and-setup) section of the wiki for detailed instructions.

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

<sup>(for details, see the [project wiki](https://github.com/Tom-Bom-badil/samson_trovis_557x/wiki/Supported-controllers))</sup>

## 👉 Documentation: Wiki

Lots of in-depth insights into how everything works, including installation
instructions, adapter configuration and tests, troubleshooting guides and
technical backgrounds as well as basics on the technologies used in the project
can be found on the [project wiki](https://github.com/Tom-Bom-badil/samson_trovis_557x/wiki).

The Wiki (and also the discussions section) has grown over the last ~10 years,
so you can find a lot of useful information there.

## 👉 Reporting issues or asking questions

Please use the [discussions](https://github.com/Tom-Bom-badil/samson_trovis_557x/discussions) on GitHub.

## 👉 Related projects

- [`trovis-modbus`](https://github.com/Tom-Bom-badil/trovis-modbus) -
  a generic library that contains a controller-specific data model and read/write logic
- [`modbus-connection`](https://github.com/home-assistant-libs/modbus-connection) -
  a backend-neutral Modbus connection API used internally by the integration