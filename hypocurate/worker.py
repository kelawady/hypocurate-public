"""The background worker (PRD Section 6).

Step 2: an idle loop. It checks that the database answers, logs, and sleeps.
The queue, heartbeat and pipeline arrive in step 9. Run with
`python -m hypocurate.worker`.
"""
from __future__ import annotations

import logging
import time

from hypocurate.config import load_settings
from hypocurate.db.engine import database_reachable, make_engine

log = logging.getLogger("hypocurate.worker")
IDLE_SECONDS = 60


def run(max_cycles: int | None = None, sleep=time.sleep) -> None:
    settings = load_settings(web=False)
    engine = make_engine(settings.database_url)
    cycles = 0
    while max_cycles is None or cycles < max_cycles:
        reachable = database_reachable(engine)
        log.info("worker idle: no pipeline yet; database %s", "reachable" if reachable else "NOT reachable")
        cycles += 1
        sleep(IDLE_SECONDS)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    run()
