import io
from operator import itemgetter
import re
import json
import structlog
import unittest

from logging_config import configure_logger


TIMESTAMP_RE = re.compile(
    r"([1-9]\d{3})-(0[1-9]|1[0-2])-(0[1-9]|[1-2]\d|3[0-1])T([0-4]\d|5[0-9]):([0-4]\d|5[0-9]):([0-4]\d|5[0-9])(\.\d{3,})?Z"
)


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
