"""
Worker entrypoint — consumes queued jobs and runs agents.

Production: scaled independently (Dockerfile.worker). Queue adapter is
Redis BRPOP in prod; the placeholder below demonstrates the loop.
"""
import logging
import os
import time

from CORE_AGENT_INFRASTRUCTURE.config import get_config
from CORE_AGENT_INFRASTRUCTURE.db.session import init_db

logger = logging.getLogger("stratum.worker")


def process_job(job: dict) -> None:
    logger.info("processing job=%s", job.get("id"))


def main() -> None:
    cfg = get_config()
    logging.basicConfig(level=cfg.log_level)
    init_db()
    logger.info("worker starting (env=%s demo=%s)", cfg.environment, cfg.demo_mode)
    while True:
        try:
            # prod: job = redis.blpop("stratum:jobs") -> process_job(job)
            time.sleep(10)
        except KeyboardInterrupt:
            logger.info("worker stopping")
            break
        except Exception:  # noqa: BLE001
            logger.exception("worker loop error; sleeping 30s")
            time.sleep(30)


if __name__ == "__main__":
    main()
