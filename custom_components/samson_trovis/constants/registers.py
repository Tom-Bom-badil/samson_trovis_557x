"""Register catalog for SAMSON TROVIS."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfTemperature, EntityCategory

from .areas import (
    AREA_CONTROLLER,
    AREA_DIAGNOSTIC,
    AREA_HEAT_METERS,
    AREA_HEATING_CIRCUIT_1,
    AREA_HEATING_CIRCUIT_2,
    AREA_HEATING_CIRCUIT_3,
    AREA_HEATING_CIRCUIT_4_DOMESTIC_HOT_WATER,
    AREA_MEASUREMENTS,
    AREA_MISCELLANEOUS,
    AREA_SCHEDULES,
)
from .descriptions import TrovisRegisterDescription, TrovisRegisterValueType


DIAGNOSTIC_REGISTERS: tuple[TrovisRegisterDescription, ...] = ()
HEAT_METERS_REGISTERS: tuple[TrovisRegisterDescription, ...] = ()
SCHEDULE_REGISTERS: tuple[TrovisRegisterDescription, ...] = ()
MISCELLANEOUS_REGISTERS: tuple[TrovisRegisterDescription, ...] = ()


CONTROLLER_REGISTERS: tuple[TrovisRegisterDescription, ...] = (
    TrovisRegisterDescription(key="model", area=AREA_CONTROLLER, address=0, read_only=True, description="Controller model"),
    TrovisRegisterDescription(key="hydraulic_scheme", area=AREA_CONTROLLER, address=1, read_only=True, scale=0.1, format_as_text=True, text_decimals=1, description="Hydraulic scheme"),
    TrovisRegisterDescription(key="firmware_version", area=AREA_CONTROLLER, address=2, read_only=True, scale=0.01, format_as_text=True, text_decimals=2, description="Firmware version"),
)


MEASUREMENT_REGISTERS: tuple[TrovisRegisterDescription, ...] = (
    ### dummy only, delete later
    TrovisRegisterDescription(key="00_library", area=AREA_CONTROLLER, address=None, read_only=True, icon="mdi:library", description="Current Modbus backend"),
    ###
    TrovisRegisterDescription(key="outside_temperature_1", area=AREA_MEASUREMENTS, address=9, read_only=True, value_type=TrovisRegisterValueType.SIGNED, scale=0.1, native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, description="Outside sensor AF1"),
    TrovisRegisterDescription(key="outside_temperature_2", area=AREA_MEASUREMENTS, address=10, read_only=True, value_type=TrovisRegisterValueType.SIGNED, scale=0.1, native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, description="Outside sensor AF2"),
    TrovisRegisterDescription(key="hc1_flow_temperature", area=AREA_MEASUREMENTS, address=12, read_only=True, value_type=TrovisRegisterValueType.SIGNED, scale=0.1, native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, description="Flow sensor VF1"),
    TrovisRegisterDescription(key="hc2_flow_temperature", area=AREA_MEASUREMENTS, address=13, read_only=True, value_type=TrovisRegisterValueType.SIGNED, scale=0.1, native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, description="Flow sensor VF2"),
    TrovisRegisterDescription(key="hc3_flow_temperature", area=AREA_MEASUREMENTS, address=14, read_only=True, value_type=TrovisRegisterValueType.SIGNED, scale=0.1, native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, description="Flow sensor VF3"),
    TrovisRegisterDescription(key="hc4_flow_temperature", area=AREA_MEASUREMENTS, address=15, read_only=True, value_type=TrovisRegisterValueType.SIGNED, scale=0.1, native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, description="Flow sensor VF4"),
    TrovisRegisterDescription(key="hc1_return_temperature", area=AREA_MEASUREMENTS, address=16, read_only=True, value_type=TrovisRegisterValueType.SIGNED, scale=0.1, native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, description="Return sensor RüF1"),
    TrovisRegisterDescription(key="hc2_return_temperature", area=AREA_MEASUREMENTS, address=17, read_only=True, value_type=TrovisRegisterValueType.SIGNED, scale=0.1, native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, description="Return sensor RüF2"),
    TrovisRegisterDescription(key="hc3_return_temperature", area=AREA_MEASUREMENTS, address=18, read_only=True, value_type=TrovisRegisterValueType.SIGNED, scale=0.1, native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, description="Return sensor RüF3"),
    TrovisRegisterDescription(key="dhw_storage_temperature", area=AREA_MEASUREMENTS, address=22, read_only=True, value_type=TrovisRegisterValueType.SIGNED, scale=0.1, native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, description="Storage temperature SF1"),
    TrovisRegisterDescription(key="dhw_storage_temperature_lower", area=AREA_MEASUREMENTS, address=23, read_only=True, value_type=TrovisRegisterValueType.SIGNED, scale=0.1, native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, description="Lower storage temperature SF2"),
    TrovisRegisterDescription(key="storage_remote_temperature", area=AREA_MEASUREMENTS, address=24, read_only=True, value_type=TrovisRegisterValueType.SIGNED, scale=0.1, native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, description="Storage/remote sensor SF3/FG3"),
)


HEATING_CIRCUIT_1_REGISTERS: tuple[TrovisRegisterDescription, ...] = (
    TrovisRegisterDescription(key="heating_circuit_1_flow_temperature_setpoint", area=AREA_HEATING_CIRCUIT_1, address=999, read_only=True, value_type=TrovisRegisterValueType.SIGNED, scale=0.1, native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, description="Heating circuit 1 flow temperature setpoint"),
)


HEATING_CIRCUIT_2_REGISTERS: tuple[TrovisRegisterDescription, ...] = (
    TrovisRegisterDescription(key="heating_circuit_2_flow_temperature_setpoint", area=AREA_HEATING_CIRCUIT_2, address=1199, read_only=True, value_type=TrovisRegisterValueType.SIGNED, scale=0.1, native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, description="Heating circuit 2 flow temperature setpoint"),
)


HEATING_CIRCUIT_3_REGISTERS: tuple[TrovisRegisterDescription, ...] = (
    TrovisRegisterDescription(key="heating_circuit_3_flow_temperature_setpoint", area=AREA_HEATING_CIRCUIT_3, address=1399, read_only=True, value_type=TrovisRegisterValueType.SIGNED, scale=0.1, native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, description="Heating circuit 3 flow temperature setpoint"),
)


HEATING_CIRCUIT_4_DOMESTIC_HOT_WATER_REGISTERS: tuple[TrovisRegisterDescription, ...] = (
    TrovisRegisterDescription(key="heating_circuit_4_domestic_hot_water_flow_temperature_setpoint", area=AREA_HEATING_CIRCUIT_4_DOMESTIC_HOT_WATER, address=1799, read_only=True, value_type=TrovisRegisterValueType.SIGNED, scale=0.1, native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, description="Heating circuit 4 / domestic hot water flow temperature setpoint"),
)


REGISTER_GROUPS: dict[str, tuple[TrovisRegisterDescription, ...]] = {
    AREA_DIAGNOSTIC: DIAGNOSTIC_REGISTERS,
    AREA_CONTROLLER: CONTROLLER_REGISTERS,
    AREA_MEASUREMENTS: MEASUREMENT_REGISTERS,
    AREA_HEATING_CIRCUIT_1: HEATING_CIRCUIT_1_REGISTERS,
    AREA_HEATING_CIRCUIT_2: HEATING_CIRCUIT_2_REGISTERS,
    AREA_HEATING_CIRCUIT_3: HEATING_CIRCUIT_3_REGISTERS,
    AREA_HEATING_CIRCUIT_4_DOMESTIC_HOT_WATER: HEATING_CIRCUIT_4_DOMESTIC_HOT_WATER_REGISTERS,
    AREA_HEAT_METERS: HEAT_METERS_REGISTERS,
    AREA_SCHEDULES: SCHEDULE_REGISTERS,
    AREA_MISCELLANEOUS: MISCELLANEOUS_REGISTERS,
}


ALL_REGISTERS: tuple[TrovisRegisterDescription, ...] = tuple(
    register
    for group in REGISTER_GROUPS.values()
    for register in group
)



