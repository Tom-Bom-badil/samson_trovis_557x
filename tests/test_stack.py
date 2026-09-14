"""Repository-level tests for the TROVIS HACS integration."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "trovis557x"
TRANSLATIONS = COMPONENT / "translations"


def _load_json(path: Path) -> dict:
    """Load one JSON file."""
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def _requirement(requirements: list[str], prefix: str) -> str:
    """Return exactly one requirement matching the package prefix."""
    matches = [
        requirement
        for requirement in requirements
        if requirement.lower().startswith(prefix.lower())
    ]

    assert len(matches) == 1, (
        f"Expected exactly one requirement starting with {prefix!r}, got {matches}"
    )

    return matches[0]


def test_manifest_contract() -> None:
    """Validate the integration-owned package and backend contract."""
    manifest = _load_json(COMPONENT / "manifest.json")

    assert manifest["domain"] == "trovis557x"
    assert manifest["config_flow"] is True
    assert manifest["integration_type"] == "device"
    assert manifest["iot_class"] == "local_polling"

    # Home Assistant owns the concrete Modbus transport stack. The custom
    # integration depends on Core's Modbus integration and only brings its
    # device library.
    assert "modbus" in manifest.get("dependencies", [])
    assert "recorder" in manifest.get("dependencies", [])

    requirements = manifest["requirements"]

    trovis_requirement = _requirement(requirements, "trovis-modbus")

    # Do not duplicate the current minimum release versions in this test.
    # The manifest itself is the single source of truth for those.
    assert ">=" in trovis_requirement
    assert "<4" in trovis_requirement

    assert not any(
        requirement.lower().startswith("modbus-connection")
        for requirement in requirements
    )
    assert not any(
        requirement.lower().startswith("tmodbus") for requirement in requirements
    )
    assert not any("pymodbus" in requirement.lower() for requirement in requirements)

    assert "trovis_modbus" in manifest["loggers"]


def test_strings_and_english_translation_contract() -> None:
    """Validate integration-owned config-flow strings."""
    strings = _load_json(COMPONENT / "strings.json")
    english = _load_json(TRANSLATIONS / "en.json")

    # English is the source language and should stay synchronized.
    assert strings == english

    steps = strings["config"]["step"]

    expected_steps = {
        "user",
        "device",
        "reconfigure",
    }
    assert expected_steps == steps.keys()

    assert set(steps["user"]["data"]) == {
        "connection",
        "unit_id",
        "baudrate",
    }
    assert set(steps["reconfigure"]["data"]) == {
        "connection",
        "unit_id",
        "baudrate",
        "name",
        "access_code",
    }
    assert "menu_options" not in steps["user"]
    assert "menu_options" not in steps["reconfigure"]
    assert "selector" not in strings
    assert "connection_entry_id" not in json.dumps(strings)
    assert "<id>" not in json.dumps(strings)
    assert "<port>" not in json.dumps(strings)

    config_flow_source = (COMPONENT / "config_flow.py").read_text(encoding="utf-8")
    assert "SerialPortSelector" in config_flow_source
    assert "known_connection" not in config_flow_source
    assert "async_step_serial" not in config_flow_source
    assert "async_step_reconfigure_serial" not in config_flow_source
    assert '"esphome://"' in config_flow_source
    assert '"esphome-hass://"' in config_flow_source

    # socket:// is RTU over a transparent TCP stream and is represented as
    # a serial transport since modbus-connection 4.12.
    socket_branch = config_flow_source.split(
        'if lowered.startswith("socket://"):',
        1,
    )[1].split(
        'if "://" in normalized:',
        1,
    )[0]
    assert "CONF_CONNECTION_TYPE: CONNECTION_TYPE_SERIAL" in socket_branch
    assert "CONF_DEVICE" in socket_branch
    assert "CONF_HOST" not in socket_branch
    assert "CONF_PORT" not in socket_branch
    assert "CONF_FRAMER" not in socket_branch

    # Plain host:port remains native Modbus/TCP without an explicit framer.
    tcp_branch = config_flow_source.split(
        "host, port = _parse_host_port(normalized)",
        1,
    )[1].split(
        "def _connection_data",
        1,
    )[0]
    assert "CONF_CONNECTION_TYPE: CONNECTION_TYPE_TCP" in tcp_branch
    assert "CONF_HOST: host" in tcp_branch
    assert "CONF_PORT: port" in tcp_branch
    assert "CONF_FRAMER" not in tcp_branch

    # Keep support for displaying old pre-4.12 config entries correctly.
    format_connection = config_flow_source.split(
        "def _format_connection",
        1,
    )[1].split(
        "async def _async_probe",
        1,
    )[0]
    assert "FRAMER_RTU" in format_connection
    assert "FRAMER_SOCKET" in format_connection

    # Baud rate is part of the unified setup contract even for native TCP.
    connection_data = config_flow_source.split(
        "def _connection_data",
        1,
    )[1].split(
        "def _complete_serial_data",
        1,
    )[0]
    assert "CONF_BAUDRATE: baudrate" in connection_data


def test_trovis_serial_connection_contract() -> None:
    """Keep the supported TROVIS serial settings deliberately narrow."""
    const_source = (COMPONENT / "const.py").read_text(encoding="utf-8")

    assert "SERIAL_BAUDRATES: Final = (19200, 9600)" in const_source
    assert "DEFAULT_BAUDRATE: Final = 19200" in const_source
    assert 'DEFAULT_PARITY: Final = "N"' in const_source
    assert "DEFAULT_STOPBITS: Final = 1" in const_source
    assert "DEFAULT_BYTESIZE: Final = 8" in const_source

    config_flow_source = (COMPONENT / "config_flow.py").read_text(encoding="utf-8")
    assert "CONF_PARITY: DEFAULT_PARITY" in config_flow_source
    assert "CONF_STOPBITS: DEFAULT_STOPBITS" in config_flow_source
    assert "CONF_BYTESIZE: DEFAULT_BYTESIZE" in config_flow_source

    init_source = (COMPONENT / "__init__.py").read_text(encoding="utf-8")
    # Serial RTU, including socket://, uses the common serial parameter builder.
    assert "def _serial_modbus_params(" in init_source
    assert "def _socket_device(" in init_source
    assert "_socket_device(host, port)" in init_source

    # Native Modbus/TCP must no longer pass the deprecated framer parameter.
    tcp_params = init_source.split(
        "return ModbusTcpParams(",
        1,
    )[1].split(
        ")",
        1,
    )[0]
    assert "host=host" in tcp_params
    assert "port=port" in tcp_params
    assert "framer=" not in tcp_params


def test_documented_sensor_abbreviations() -> None:
    """Keep documented TROVIS sensor abbreviations in visible names."""
    english = _load_json(TRANSLATIONS / "en.json")
    german = _load_json(TRANSLATIONS / "de.json")

    expected = {
        "outdoor_temperature_1": "AF1",
        "outdoor_temperature_2": "AF2",
        "flow_temperature_1": "VF1",
        "flow_temperature_2": "VF2",
        "flow_temperature_3": "VF3",
        "flow_temperature_4": "VF4",
        "return_temperature_1": "RüF1",
        "return_temperature_2": "RüF2",
        "return_temperature_3": "RüF3",
        "room_temperature_1": "RF1",
        "room_temperature_2": "RF2",
        "room_temperature_3": "RF3",
        "ww_storage_temperature": "SF1",
        "ww_storage_temperature_lower": "SF2",
        "sf3": "SF3",
        "ae1": "AE1",
        "ae2": "AE2",
        "ae3": "AE3",
        "fg1": "FG1",
        "fg2": "FG2",
        "fg3": "FG3",
        "pulse_rate": "IMP",
        "analog_input_voltage": "AE",
        "analog_input_current": "AE",
    }

    for translation_key, abbreviation in expected.items():
        english_name = english["entity"]["sensor"][translation_key]["name"]
        german_name = german["entity"]["sensor"][translation_key]["name"]

        assert english_name.startswith(abbreviation), (
            f"{translation_key}: English name must start with "
            f"{abbreviation!r}, got {english_name!r}"
        )

        assert german_name.startswith(abbreviation), (
            f"{translation_key}: German name must start with "
            f"{abbreviation!r}, got {german_name!r}"
        )


def test_local_dev_overrides_remain_local() -> None:
    """Ensure local developer overrides cannot accidentally be committed."""
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")

    assert "**/_local_dev_overrides/" in gitignore

    # Obsolete development mechanisms must not return.
    assert not (COMPONENT / "_local_dev.py").exists()
    assert not (COMPONENT / "local_dev.py").exists()


def test_device_links_use_registry_ids() -> None:
    """Keep sub-device links on Home Assistant's current device registry API."""
    init_source = (COMPONENT / "__init__.py").read_text(encoding="utf-8")
    assert "via_device=(" not in init_source
    assert "via_device_id=dr.async_get_device_id_by_identifier(" in init_source
    assert "dr.async_get(hass).async_get_or_create(" in init_source


def test_pumps_and_valves_device_contract() -> None:
    """Keep the canonical read-only actuator view and speaking IDs stable."""
    strings = _load_json(COMPONENT / "strings.json")
    german = _load_json(TRANSLATIONS / "de.json")

    assert strings["device"]["pumps_and_valves"]["name"] == "Pumps and Valves"
    assert german["device"]["pumps_and_valves"]["name"] == "Pumpen und Ventile"

    sensor_source = (COMPONENT / "sensor.py").read_text(encoding="utf-8")
    binary_source = (COMPONENT / "binary_sensor.py").read_text(encoding="utf-8")
    switch_source = (COMPONENT / "switch.py").read_text(encoding="utf-8")

    assert "pumps_and_valves_rk{index}_valve_setpoint" in sensor_source
    assert "pumps_and_valves_up{index}" in binary_source
    assert "pumps_and_valves_rk{index}_valve_opening" in binary_source
    assert "pumps_and_valves_rk{index}_valve_closing" in binary_source
    assert 'key="pumps_and_valves_slp"' in binary_source
    assert 'key="pumps_and_valves_zp"' in binary_source
    assert 'key="pumps_and_valves_solar_pump"' in binary_source

    # Pumps and Valves is the canonical status view. Pump controls remain in
    # their functional Rk devices and must not be duplicated here.
    assert "pumps_and_valves_up{index}_control" not in switch_source
    assert 'key="pumps_and_valves_slp_control"' not in switch_source
    assert 'key="pumps_and_valves_zp_control"' not in switch_source

    # Pump states in this device deliberately use plain binary semantics so
    # Home Assistant renders them consistently as On/Off instead of mixing
    # Running/Not running with On/Off.
    rk_actuators = binary_source.split(
        "def _pumps_and_valves_rk_binary_descriptions", 1
    )[1].split("_PUMPS_AND_VALVES_RK4", 1)[0]
    solar_actuators = binary_source.split("_PUMPS_AND_VALVES_SOLAR", 1)[1].split(
        "def _description_supported", 1
    )[0]
    assert "BinarySensorDeviceClass.RUNNING" not in rk_actuators
    assert "BinarySensorDeviceClass.RUNNING" not in solar_actuators


def test_rk4_cleanup_contract() -> None:
    """Keep the resolved Rk4 cleanup decisions in the HA presentation."""
    sensor_source = (COMPONENT / "sensor.py").read_text(encoding="utf-8")
    binary_source = (COMPONENT / "binary_sensor.py").read_text(encoding="utf-8")
    switch_source = (COMPONENT / "switch.py").read_text(encoding="utf-8")

    active_setpoint = sensor_source.split('key="rk4_setpoint_active"', 1)[1].split(
        "),", 1
    )[0]
    assert "entity_category=EntityCategory.DIAGNOSTIC" in active_setpoint

    for removed_key in (
        "rk4_mode_control_autonomous",
        "rk4_storage_tank_charging_pump_control_autonomous",
        "rk4_circulation_pump_control_autonomous",
        "rk4_special_setpoint_control_autonomous",
    ):
        assert removed_key not in binary_source

    intermediate_heating = switch_source.split(
        'key="rk4_intermediate_heating_function_enabled"', 1
    )[1].split("),", 1)[0]
    assert "enabled=False" not in intermediate_heating
    assert "coordinator.device.intermediate_heating_available" in switch_source


def test_system_overall_status_contract() -> None:
    """Keep the overall actuator bit mask as one controller diagnostic sensor."""
    strings = _load_json(COMPONENT / "strings.json")
    german = _load_json(TRANSLATIONS / "de.json")
    sensor_source = (COMPONENT / "sensor.py").read_text(encoding="utf-8")

    assert strings["entity"]["sensor"]["system_overall_status"]["name"] == (
        "System overall status"
    )
    assert german["entity"]["sensor"]["system_overall_status"]["name"] == (
        "Regler Gesamtstatus"
    )

    assert 'key="system_overall_status"' in sensor_source
    assert 'value_kind="system_overall_status"' in sensor_source
    assert "coordinator.device.system_overall_status" in sensor_source


def test_dashboard_controller_button_helper_contract() -> None:
    """Keep the dashboard controller-button helper local and clearly identified."""
    strings = _load_json(COMPONENT / "strings.json")
    german = _load_json(TRANSLATIONS / "de.json")
    number_source = (COMPONENT / "number.py").read_text(encoding="utf-8")

    assert (
        strings["entity"]["number"]["helper_dashboard_controller_button_clicked"][
            "name"
        ]
        == "Helper - Active controller button on the dashboard"
    )

    assert "helper_dashboard_controller_button_clicked" in german["entity"]["number"]

    assert 'key="helper_dashboard_controller_button_clicked"' in number_source
    assert (
        'translation_key="helper_dashboard_controller_button_clicked"' in number_source
    )
    assert "native_min_value=1" in number_source
    assert "native_max_value=4" in number_source
    assert "native_step=1" in number_source
    assert "initial_value=1" in number_source

    assert "class TrovisHelperNumber" in number_source
    assert "self.async_write_ha_state()" in number_source


def test_timeout_retry_contract() -> None:
    """Keep TROVIS read retries local to the integration-owned unit proxy."""
    init_source = (COMPONENT / "__init__.py").read_text(encoding="utf-8")

    assert "_READ_RETRIES = 2" in init_source
    assert "class _ReadRetryModbusUnit" in init_source
    assert '"read_holding_registers"' in init_source
    assert '"read_coils"' in init_source
    assert "except ModbusTimeoutError" in init_source
    assert "set_message_spacing" not in init_source


def test_verified_write_publishes_without_full_poll_contract() -> None:
    """Verified writes must publish cache state without a coordinator refresh."""
    init_source = (COMPONENT / "__init__.py").read_text(encoding="utf-8")
    switch_source = (COMPONENT / "switch.py").read_text(encoding="utf-8")

    assert "if verified is True:" in init_source
    immediate_publish = (
        "self.coordinator.async_set_updated_data(self.coordinator.device)"
    )
    assert immediate_publish in init_source
    assert "await self.coordinator.async_request_refresh()" in init_source
    assert (
        switch_source.count(
            "self.coordinator.async_set_updated_data(self.coordinator.device)"
        )
        >= 2
    )
