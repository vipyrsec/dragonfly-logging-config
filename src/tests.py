import io
import logging
import structlog
import unittest
from typing import Any

from logging_config import configure_logger


class TestLogging(unittest.TestCase):
    def test_log_output(self):
        """
        Test whether the log config is built successfully and the emitted logs are correct.
        """

        f = io.StringIO()

        config = {
            "disable_existing_loggers": False,
            "handlers": {
                "default": {
                    "level": "DEBUG",
                    "class": "logging.StreamHandler",
                    "stream": f,
                    "formatter": "json",
                },
            },
            "loggers": {
                "": {"handlers": ["default"], "level": "DEBUG", "propagate": True},
            },
        }

        configure_logger(config)
        cf = structlog.testing.CapturingLoggerFactory()
        structlog.configure(logger_factory=cf)
        log = structlog.get_logger()

        log.info("test")
        record = cf.logger.calls[0]

        self.assertEqual(record.method_name, "info")
        args = record.args[0]
        self.assertDictEqual(
            args,
            {
                "event": "test",
                "level": "info",
                "timestamp": args["timestamp"],
                "lineno": args["lineno"],
                "filename": "tests.py",
                "module": "tests",
                "func_name": "test_log_output",
            },
        )

    def test_additional_processors(self):
        """
        Test whether passing additional processors works correctly.
        """

        f = io.StringIO()

        config = {
            "disable_existing_loggers": False,
            "handlers": {
                "default": {
                    "level": "DEBUG",
                    "class": "logging.StreamHandler",
                    "stream": f,
                    "formatter": "json",
                },
            },
            "loggers": {
                "": {"handlers": ["default"], "level": "DEBUG", "propagate": True},
            },
        }

        def additional_processor(
            logger: logging.Logger, method_name: str, event_dict: dict[str, Any]
        ) -> dict[str, Any]:
            event_dict["testing"] = "testing"
            return event_dict

        configure_logger(config, additional_processors=[additional_processor])

        cf = structlog.testing.CapturingLoggerFactory()
        structlog.configure(logger_factory=cf)
        log = structlog.get_logger()

        log.info("test")
        record = cf.logger.calls[0]

        self.assertEqual(record.args[0]["testing"], "testing")
