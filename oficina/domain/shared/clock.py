"""Relógio do domínio. Testes podem substituir `set_clock`."""

from collections.abc import Callable
from datetime import datetime, timezone

_clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc)


def now() -> datetime:
    return _clock()


def set_clock(fn: Callable[[], datetime]) -> None:
    global _clock
    _clock = fn


def reset_clock() -> None:
    global _clock
    _clock = lambda: datetime.now(timezone.utc)
