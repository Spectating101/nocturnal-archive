"""Utility helpers for working with optional async callables."""

from __future__ import annotations

import inspect
from typing import Any


async def resolve_awaitable(value: Any) -> Any:
    """Return the resolved value of a possibly awaitable object.

    Many integrations expose async callables in production but are patched with
    synchronous mocks during tests. This helper lets callers await either style
    safely by only awaiting real awaitables.
    """

    if inspect.isawaitable(value):
        return await value
    return value
