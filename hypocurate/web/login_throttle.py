"""Bounded throttling of failed logins, kept in memory (no table).

Second-model review of step 2, finding 2: a lockout lets anyone keep the owner
out, so there is none. The correct password is always accepted. Wrong passwords
are counted; once MAX_FAILURES have been counted within WINDOW_SECONDS, further
wrong attempts are refused at once (and not counted) until the oldest counted
failure leaves the window.

The comparison, the check and the count happen under one lock, so concurrent
attempts cannot slip past the bound.

What this does and does not do: it bounds the work and the log noise caused by
wrong attempts. It does not slow guessing, because a correct guess is accepted
even while throttled. Protection against guessing is the password itself: in
production at least 24 random characters (hypocurate/config.py).

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
