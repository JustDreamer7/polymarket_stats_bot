import logging

import structlog

logger = structlog.get_logger(__name__)


class AppLogger:
    _configured: bool = False

    @classmethod
    def setup(cls):

        if cls._configured:
            return structlog.get_logger()
        logging.basicConfig(level="INFO", handlers=[logging.StreamHandler()])

        structlog.configure(
            processors=[
                structlog.stdlib.add_log_level,
                structlog.stdlib.add_logger_name,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.dev.set_exc_info,
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )

        return logger


logger = AppLogger.setup()
