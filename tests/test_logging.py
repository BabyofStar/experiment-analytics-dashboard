from pathlib import Path

from src.logging_config import configure_logging


def test_configure_logging_writes_a_rotating_log(tmp_path: Path):
    log_path = tmp_path / "logs" / "dashboard.log"
    logger = configure_logging(log_path)

    logger.info("test event")

    assert log_path.exists()
    assert "test event" in log_path.read_text(encoding="utf-8")
