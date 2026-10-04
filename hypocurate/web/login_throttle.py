"""Counting of failed logins, kept in memory (no table).

Second-model review of step 2, finding 2: a lockout lets anyone keep the owner
out, so there is none. What this does, and only this: every attempt is still
checked against the password. A correct password is never refused by this
counter. After MAX_FAILURES wrong attempts within WINDOW_SECONDS, further wrong
attempts receive 429 instead of 401 (and are not counted), until the oldest
counted failure leaves the window.

The comparison, the check and the count happen under one lock, so concurrent
attempts cannot pass the count.

Protection against guessing is the password: a random password of at least 24
characters in production. Configuration (hypocurate/config.py) enforces the
length, not the randomness.

The web service runs one process, so the count is shared; a restart clears it.
"""
from __future__ import annotations

import hmac
import threading
import time
from collections import deque
from collections.abc import Callable
from enum import Enum

MAX_FAILURES = 5
WINDOW_SECONDS = 15 * 60


class Attempt(Enum):
    OK = "ok"
    WRONG = "wrong"
    THROTTLED = "throttled"


class LoginThrottle:
    def __init__(
        self,
        max_failures: int = MAX_FAILURES,
        window_seconds: float = WINDOW_SECONDS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.max_failures = max_failures
        self.window_seconds = window_seconds
        self._clock = clock
        self._failures: deque[float] = deque()
        self._lock = threading.Lock()

    def attempt(self, password: str, expected: str) -> Attempt:
        with self._lock:
            if hmac.compare_digest(password.encode(), expected.encode()):
                return Attempt.OK
            now = self._clock()
            while self._failures and self._failures[0] <= now - self.window_seconds:
                self._failures.popleft()
            if len(self._failures) >= self.max_failures:
                return Attempt.THROTTLED
            self._failures.append(now)
            return Attempt.WRONG
