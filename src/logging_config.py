"""Application logging configuration."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


LOGGER_NAME = "experiment_analytics_dashboard"
DEFAULT_LOG_PATH = Path(__file__).parents[1] / "data" / "experiment_analytics.log"


def configure_logging(log_path: str | Path = DEFAULT_LOG_PATH) -> logging.Logger:
    """Configure a small rotating file logger for application diagnostics."""

    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    configured_path = str(path.resolve())
    for handler in logger.handlers:
        if getattr(handler, "dashboard_log_path", None) == configured_path:
            return logger

    for handler in list(logger.handlers):
        handler.close()
        logger.removeHandler(handler)

    handler = RotatingFileHandler(
        path,
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    handler.dashboard_log_path = configured_path
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    )
    logger.addHandler(handler)
    return logger
