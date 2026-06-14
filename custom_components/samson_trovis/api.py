"""TROVIS protocol/API layer."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry

from .transport import TrovisTransport
from .constants.descriptions import TrovisCoilDescription, TrovisRegisterDescription, TrovisRegisterValueType
from .constants.areas import AREA_CONTROLLER, DEFAULT_ENABLED_AREAS
from .constants.models import MODEL_OPTIONS
from .constants.registers import CONTROLLER_REGISTERS
from .constants.coils import CONTROLLER_COILS
from .constants.config import (
    CONF_ENABLED_AREAS,
    CONTROLLER_MODEL_REGISTER,
    MAX_COILS_PER_READ,
    MAX_REGISTERS_PER_READ,
)


_LOGGER = logging.getLogger(__name__)


class TrovisApi:
    """TROVIS-specific API using the transport layer."""

    def __init__(self, transport: TrovisTransport, entry: ConfigEntry | None = None) -> None:
        """Initialize the API."""
        self.transport = transport
        self.entry = entry

    @property
    def enabled_areas(self) -> set[str]:
        """Return the enabled functional areas."""
        if self.entry is None:
            return set(DEFAULT_ENABLED_AREAS)

        return set(self.entry.options.get(CONF_ENABLED_AREAS) or DEFAULT_ENABLED_AREAS)

    async def async_read_model(self) -> str | None:
        """Read the TROVIS model from register 0."""
        registers = await self.transport.async_read_registers(CONTROLLER_MODEL_REGISTER, 1)

        if not registers:
            return None

        raw_model = int(registers[0])
        model = str(raw_model)

        if model not in MODEL_OPTIONS:
            _LOGGER.warning("TROVIS model register returned an unknown model value: %s", raw_model)

        _LOGGER.info(
            "Connected to TROVIS model %s on %s with slave_id %s",
            model,
            self.transport.port_url,
            self.transport.slave_id,
        )

        return model

    async def async_read_enabled_areas(self) -> dict[str, Any]:
        """Read all enabled areas."""
        data: dict[str, Any] = {}

        if AREA_CONTROLLER in self.enabled_areas:
            data.update(await self._async_read_register_descriptions(CONTROLLER_REGISTERS))
            data.update(await self._async_read_coil_descriptions(CONTROLLER_COILS))

        return data


    def _split_register_groups(
        self,
        descriptions: list[TrovisRegisterDescription],
    ) -> list[list[TrovisRegisterDescription]]:
        """Split register descriptions into safe contiguous read groups."""
        groups: list[list[TrovisRegisterDescription]] = []
        group: list[TrovisRegisterDescription] = []
        group_start: int | None = None
        group_end: int | None = None

        for description in descriptions:
            address = int(description.address)

            if group_start is None or group_end is None:
                group = [description]
                group_start = address
                group_end = address
                continue

            next_count = address - group_start + 1
            is_contiguous = address == group_end + 1

            if is_contiguous and next_count <= MAX_REGISTERS_PER_READ:
                group.append(description)
                group_end = address
                continue

            groups.append(group)
            group = [description]
            group_start = address
            group_end = address

        if group:
            groups.append(group)

        return groups


    async def _async_read_register_group(
        self,
        descriptions: list[TrovisRegisterDescription],
    ) -> dict[str, Any]:
        """Read one safe contiguous register group."""
        start = int(descriptions[0].address)
        count = int(descriptions[-1].address) - start + 1

        registers = await self.transport.async_read_registers(start, count)

        if registers is None:
            return {}

        data: dict[str, Any] = {}

        for description in descriptions:
            index = int(description.address) - start

            if index < 0 or index >= len(registers):
                continue

            data[description.key] = self._convert_register_value(description, int(registers[index]))

        return data


    async def _async_read_register_descriptions(
        self,
        descriptions: tuple[TrovisRegisterDescription, ...],
    ) -> dict[str, Any]:
        """Read and convert a list of register descriptions."""
        descriptions_with_address = sorted(
            (description for description in descriptions if description.address is not None),
            key=lambda description: int(description.address),
        )

        if not descriptions_with_address:
            return {}

        data: dict[str, Any] = {}

        for group in self._split_register_groups(descriptions_with_address):
            data.update(await self._async_read_register_group(group))

        return data


    def _convert_register_value(self, description: TrovisRegisterDescription, raw_value: int) -> Any:
        """Convert a raw register value using its description."""
        if raw_value in description.invalid_values:
            return None

        if description.value_type == TrovisRegisterValueType.SIGNED and raw_value >= 0x8000:
            raw_value -= 0x10000

        if description.value_type == TrovisRegisterValueType.ENUM:
            if description.enum_map is None:
                return raw_value
            return description.enum_map.get(raw_value, raw_value)

        value = raw_value * description.scale + description.offset

        if description.format_as_text:
            decimals = description.text_decimals if description.text_decimals is not None else 0
            return f"{value:.{decimals}f}"

        if isinstance(value, float) and value.is_integer() and description.scale == 1.0 and description.offset == 0.0:
            return int(value)

        return value


    async def async_write_register_description(
        self,
        description: TrovisRegisterDescription,
        value: float,
    ) -> bool:
        """Write a converted value to one TROVIS register."""
        if description.address is None:
            return False

        if description.read_only:
            _LOGGER.warning("Refusing to write read-only TROVIS register: %s", description.key)
            return False

        raw_value = self._convert_value_to_register(description, value)

        return await self.transport.async_write_register(
            int(description.address),
            raw_value,
        )


    async def async_write_register_option(
        self,
        description: TrovisRegisterDescription,
        option: str,
    ) -> bool:
        """Write a selected option to one TROVIS register."""
        if description.address is None:
            return False

        if description.read_only:
            _LOGGER.warning("Refusing to write read-only TROVIS register: %s", description.key)
            return False

        if description.enum_map is None:
            _LOGGER.warning("Cannot write TROVIS select without enum_map: %s", description.key)
            return False

        reverse_map = {str(label): raw_value for raw_value, label in description.enum_map.items()}

        if option not in reverse_map:
            _LOGGER.warning(
                "Invalid TROVIS select option for %s: %s",
                description.key,
                option,
            )
            return False

        return await self.transport.async_write_register(
            int(description.address),
            int(reverse_map[option]),
        )


    def _convert_value_to_register(
        self,
        description: TrovisRegisterDescription,
        value: float,
    ) -> int:
        """Convert a Home Assistant value to a raw register value."""
        if description.scale == 0:
            raise ValueError(f"Cannot write register {description.key}: scale must not be 0")

        raw_value = round((float(value) - description.offset) / description.scale)

        if description.value_type == TrovisRegisterValueType.SIGNED and raw_value < 0:
            raw_value += 0x10000

        return int(raw_value)



    async def _async_read_coil_descriptions(
        self,
        descriptions: tuple[TrovisCoilDescription, ...],
    ) -> dict[str, Any]:
        """Read a list of coil descriptions."""
        descriptions_with_address = sorted(
            (description for description in descriptions if description.address is not None),
            key=lambda description: int(description.address),
        )

        if not descriptions_with_address:
            return {}

        data: dict[str, Any] = {}

        for group in self._split_coil_groups(descriptions_with_address):
            data.update(await self._async_read_coil_group(group))

        return data


    def _split_coil_groups(
        self,
        descriptions: list[TrovisCoilDescription],
    ) -> list[list[TrovisCoilDescription]]:
        """Split coil descriptions into safe contiguous read groups."""
        groups: list[list[TrovisCoilDescription]] = []
        group: list[TrovisCoilDescription] = []
        group_start: int | None = None
        group_end: int | None = None

        for description in descriptions:
            address = int(description.address)

            if group_start is None or group_end is None:
                group = [description]
                group_start = address
                group_end = address
                continue

            next_count = address - group_start + 1
            is_contiguous = address == group_end + 1

            if is_contiguous and next_count <= MAX_COILS_PER_READ:
                group.append(description)
                group_end = address
                continue

            groups.append(group)
            group = [description]
            group_start = address
            group_end = address

        if group:
            groups.append(group)

        return groups


    async def _async_read_coil_group(
        self,
        descriptions: list[TrovisCoilDescription],
    ) -> dict[str, Any]:
        """Read one contiguous coil group."""
        start = int(descriptions[0].address)
        count = int(descriptions[-1].address) - start + 1

        coils = await self.transport.async_read_coils(start, count)

        if coils is None:
            return {}

        data: dict[str, Any] = {}

        for description in descriptions:
            index = int(description.address) - start

            if index < 0 or index >= len(coils):
                continue

            data[description.key] = bool(coils[index])

        return data