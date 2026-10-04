"""Step 2: the in-memory limit on failed login attempts."""
from hypocurate.web.login_limit import LOCKOUT_SECONDS, MAX_FAILURES, WINDOW_SECONDS, LoginLimit


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def test_defaults_are_as_approved():
    assert (MAX_FAILURES, WINDOW_SECONDS, LOCKOUT_SECONDS) == (5, 900, 300)


def test_locked_after_max_failures_and_not_before():
    clock = Clock()
    limit = LoginLimit(clock=clock)
    for _ in range(MAX_FAILURES - 1):
        limit.record_failure()
        assert limit.seconds_locked() == 0
    limit.record_failure()
    assert limit.seconds_locked() == LOCKOUT_SECONDS


def test_unlocked_after_lockout():
    clock = Clock()
    limit = LoginLimit(clock=clock)
    for _ in range(MAX_FAILURES):
        limit.record_failure()
    clock.now += LOCKOUT_SECONDS - 1
    assert limit.seconds_locked() > 0
    clock.now += 1
    assert limit.seconds_locked() == 0


def test_failures_outside_the_window_do_not_count():
    clock = Clock()
    limit = LoginLimit(clock=clock)
    for _ in range(MAX_FAILURES - 1):
        limit.record_failure()
    clock.now += WINDOW_SECONDS
    limit.record_failure()
    assert limit.seconds_locked() == 0


def test_success_resets_the_count():
    clock = Clock()
    limit = LoginLimit(clock=clock)
    for _ in range(MAX_FAILURES - 1):
        limit.record_failure()
    limit.record_success()
    for _ in range(MAX_FAILURES - 1):
        limit.record_failure()
    assert limit.seconds_locked() == 0
