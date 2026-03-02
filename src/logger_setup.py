from __future__ import annotations

from pathlib import Path

from loguru import logger


def configure_logger(log_level: str = "INFO") -> None:
    Path("logs").mkdir(parents=True, exist_ok=True)
    logger.remove()
    logger.add(
        "logs/pipeline.log",
        rotation="2 MB",
        retention=5,
        level=log_level,
        enqueue=True,
    )
    logger.add(lambda message: print(message, end=""), level=log_level)
