"""Build the pytryfi client without letting it start Sentry.

pytryfi 0.0.21 (the newest on PyPI) calls ``sentry_sdk.init()`` with its
author's DSN every time a ``PyTryFi`` is built. That call is process-wide: it
installs Sentry's default integrations into all of Home Assistant, so every
ERROR any integration logs - with its stack trace - is sent to that third
party's Sentry project, and aiohttp, the recorder's SQLAlchemy, threading and
logging all run through Sentry's hooks from then on. Upstream pytryfi has
dropped the call on its main branch but has not released it.

``make_client`` builds ``PyTryFi`` with ``sentry_sdk.init`` replaced by a
no-op for the duration of the constructor only. pytryfi's own
``capture_exception`` calls stay harmless: with no client initialised they do
nothing. Home Assistant's own Sentry integration, if anyone enables it, is
unaffected because the patch is undone as soon as the constructor returns.
"""
from __future__ import annotations

from contextlib import contextmanager
import threading

from pytryfi import PyTryFi

try:
    import sentry_sdk
except ImportError:  # pragma: no cover - pytryfi requires it, but be safe
    sentry_sdk = None

_LOCK = threading.Lock()


@contextmanager
def _sentry_init_disabled():
    if sentry_sdk is None:
        yield
        return
    with _LOCK:
        original = sentry_sdk.init
        sentry_sdk.init = lambda *args, **kwargs: None
        try:
            yield
        finally:
            sentry_sdk.init = original


def make_client(username: str, password: str) -> PyTryFi:
    """A logged-in PyTryFi, built without it starting Sentry."""
    with _sentry_init_disabled():
        return PyTryFi(username, password)
