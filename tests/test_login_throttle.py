"""Step 2 fix (review finding 2): bounded throttling of failed logins, no lockout."""
import threading
from collections import Counter

from hypocurate.web.login_throttle import MAX_FAILURES, WINDOW_SECONDS, Attempt, LoginThrottle

RIGHT = "the-right-password"


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def test_defaults_are_as_approved():
    assert (MAX_FAILURES, WINDOW_SECONDS) == (5, 900)


def test_wrong_attempts_counted_up_to_the_bound_then_throttled():
    t = LoginThrottle(clock=Clock())
    results = [t.attempt("wrong", RIGHT) for _ in range(MAX_FAILURES + 2)]
    assert results == [Attempt.WRONG] * MAX_FAILURES + [Attempt.THROTTLED] * 2


def test_correct_password_always_accepted():
    t = LoginThrottle(clock=Clock())
    assert t.attempt(RIGHT, RIGHT) is Attempt.OK
    for _ in range(MAX_FAILURES * 3):
        t.attempt("wrong", RIGHT)
    assert t.attempt(RIGHT, RIGHT) is Attempt.OK


def test_success_does_not_reset_the_count():
    t = LoginThrottle(clock=Clock())
    for _ in range(MAX_FAILURES):
        t.attempt("wrong", RIGHT)
    t.attempt(RIGHT, RIGHT)
    assert t.attempt("wrong", RIGHT) is Attempt.THROTTLED


def test_throttle_ends_when_failures_leave_the_window():
    clock = Clock()
    t = LoginThrottle(clock=clock)
    for _ in range(MAX_FAILURES):
        t.attempt("wrong", RIGHT)
    clock.now += WINDOW_SECONDS - 1
    assert t.attempt("wrong", RIGHT) is Attempt.THROTTLED
    clock.now += 1
    assert t.attempt("wrong", RIGHT) is Attempt.WRONG


def test_throttled_attempts_are_not_counted():
    """Otherwise a steady stream of refused attempts would extend the throttle forever."""
    clock = Clock()
    t = LoginThrottle(clock=clock)
    for _ in range(MAX_FAILURES):
        t.attempt("wrong", RIGHT)
    for _ in range(100):
        clock.now += 1
        t.attempt("wrong", RIGHT)
    clock.now = 1000.0 + WINDOW_SECONDS
    assert t.attempt("wrong", RIGHT) is Attempt.WRONG


def test_concurrent_failures_never_pass_the_bound():
    t = LoginThrottle()
    start = threading.Barrier(64)
    results = []
    lock = threading.Lock()

    def go():
        start.wait()
        r = t.attempt("wrong", RIGHT)
        with lock:
            results.append(r)

    threads = [threading.Thread(target=go) for _ in range(64)]
    for th in threads:
        th.start()
    for th in threads:
        th.join()
    assert Counter(results) == {Attempt.WRONG: MAX_FAILURES, Attempt.THROTTLED: 64 - MAX_FAILURES}
