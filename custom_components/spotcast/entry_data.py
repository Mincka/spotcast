"""EntryData Typed dictionary."""

from typing import TypedDict


class TokenData(TypedDict):
    """Token Data information."""

    access_token: str
    token_type: str
    expires_at: int
    refresh_token: str
    scope: str


class ApiItem(TypedDict):
    """Data for API entry."""

    token: TokenData


class ApiWithImplementationItem(ApiItem):
    """Data for API entry with HA implementation."""

    auth_implementation: str


class EntryData(TypedDict):
    """Data format for Spotcast entry."""

    public_api: ApiWithImplementationItem
    desktop_api: ApiItem
    name: str
    version: str


class OptionData(TypedDict):
    """Data format for Spotcast options."""

    is_default: bool
    base_refresh_rate: int
