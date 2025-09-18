from __future__ import annotations

import logging
from typing import cast

import structlog
from structlog.typing import Processor as StructProcessor

_DEF_PROCESSORS: list[StructProcessor] = [
    structlog.processors.TimeStamper(fmt="iso"),
    structlog.processors.add_log_level,
    structlog.processors.StackInfoRenderer(),
    structlog.processors.format_exc_info,
    structlog.processors.UnicodeDecoder(),
]


def configure(level: int = logging.INFO) -> structlog.stdlib.BoundLogger:
    logging.basicConfig(level=level, format="%(message)s")
    structlog.configure(
        processors=[*_DEF_PROCESSORS, structlog.dev.ConsoleRenderer(colors=True)],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    return cast(structlog.stdlib.BoundLogger, structlog.get_logger())
