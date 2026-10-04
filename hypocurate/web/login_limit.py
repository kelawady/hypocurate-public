"""A simple limit on failed login attempts, kept in memory (no table).

After MAX_FAILURES failed attempts within WINDOW_SECONDS, every login attempt,
even with the right password, is refused for LOCKOUT_SECONDS. A successful
login clears the count; a restart clears everything.

The limit is global, not per client address: behind Render's proxy the client
address can be spoofed through X-Forwarded-For, and there is one shared
password. The web service runs one process, so the count is shared.
"""
from __future__ import annotations

import threading
import time
from collections import deque
from collections.abc import Callable

MAX_FAILURES = 5
WINDOW_SECONDS = 15 * 60
LOCKOUT_SECONDS = 5 * 60


class LoginLimit:
    def __init__(
        self,
        max_failures: int = MAX_FAILURES,
        window_seconds: float = WINDOW_SECONDS,
        lockout_seconds: float = LOCKOUT_SECONDS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.max_failures = max_failures
        self.window_seconds = window_seconds
        self.lockout_seconds = lockout_seconds
        self._clock = clock
        self._failures: deque[float] = deque()
        self._locked_until = 0.0
        self._lock = threading.Lock()

    def seconds_locked(self) -> float:
        """Seconds until login is allowed again; 0 when it is allowed now."""
        with self._lock:
            return max(0.0, self._locked_until - self._clock())

    def record_failure(self) -> None:
        with self._lock:
            now = self._clock()
            self._failures.append(now)
            while self._failures and self._failures[0] <= now - self.window_seconds:
                self._failures.popleft()
            if len(self._failures) >= self.max_failures:
                self._locked_until = now + self.lockout_seconds
                self._failures.clear()

    def record_success(self) -> None:
        with self._lock:
            self._failures.clear()
