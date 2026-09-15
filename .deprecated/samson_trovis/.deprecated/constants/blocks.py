"""Modbus block descriptions for SAMSON TROVIS."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class TrovisBlockType(StrEnum):
    """Supported Modbus block types."""

    REGISTER = "register"
    COIL = "coil"


@dataclass(frozen=True, kw_only=True)
class TrovisBlockDescription:
    """Description of a Modbus block to poll."""

    key: str
    area: str
    block_type: TrovisBlockType
    start: int
    count: int


REGISTER_BLOCKS: tuple[TrovisBlockDescription, ...] = ()
COIL_BLOCKS: tuple[TrovisBlockDescription, ...] = ()
ALL_BLOCKS: tuple[TrovisBlockDescription, ...] = REGISTER_BLOCKS + COIL_BLOCKS
