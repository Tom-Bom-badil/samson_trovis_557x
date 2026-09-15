"""Parse Home Assistant read-exclusion settings."""

from __future__ import annotations

from collections.abc import Iterable

MODBUS_ADDRESS_MIN = 0
MODBUS_ADDRESS_MAX = 0xFFFF

ADDRESS_LIST_PATTERN = (
    r"^\s*(?:\d+(?:\s*-\s*\d+)?"
    r"(?:\s*,\s*\d+(?:\s*-\s*\d+)?)*)?\s*$"
)


def _validate_address(address: int) -> int:
    """Validate one zero-based Modbus PDU address."""
    if not MODBUS_ADDRESS_MIN <= address <= MODBUS_ADDRESS_MAX:
        raise ValueError(
            f"Modbus address {address} is outside "
            f"{MODBUS_ADDRESS_MIN}..{MODBUS_ADDRESS_MAX}"
        )
    return address


def parse_address_list(value: str) -> frozenset[int]:
    """Parse comma-separated zero-based addresses and inclusive ranges."""
    value = value.strip()
    if not value:
        return frozenset()

    addresses: set[int] = set()

    for raw_item in value.split(","):
        item = raw_item.strip()
        if not item:
            raise ValueError("Address list contains an empty item")

        if "-" not in item:
            try:
                address = int(item)
            except ValueError as err:
                raise ValueError(f"Invalid Modbus address {item!r}") from err
            addresses.add(_validate_address(address))
            continue

        parts = item.split("-")
        if len(parts) != 2:
            raise ValueError(f"Invalid Modbus address range {item!r}")

        start_text, end_text = (part.strip() for part in parts)
        if not start_text or not end_text:
            raise ValueError(f"Invalid Modbus address range {item!r}")

        try:
            start = _validate_address(int(start_text))
            end = _validate_address(int(end_text))
        except ValueError as err:
            raise ValueError(f"Invalid Modbus address range {item!r}: {err}") from err

        if start > end:
            raise ValueError(
                f"Invalid Modbus address range {item!r}: "
                "range start must not be greater than range end"
            )

        addresses.update(range(start, end + 1))

    return frozenset(addresses)


def format_address_list(addresses: Iterable[int]) -> str:
    """Return a canonical compact address-list string."""
    sorted_addresses = sorted(set(addresses))
    if not sorted_addresses:
        return ""

    items: list[str] = []
    start = previous = sorted_addresses[0]

    for address in sorted_addresses[1:]:
        if address == previous + 1:
            previous = address
            continue

        items.append(str(start) if start == previous else f"{start}-{previous}")
        start = previous = address

    items.append(str(start) if start == previous else f"{start}-{previous}")
    return ",".join(items)


def normalize_address_list(value: str) -> str:
    """Parse and return the canonical compact representation."""
    return format_address_list(parse_address_list(value))
