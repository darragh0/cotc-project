from __future__ import annotations

import datetime as dt
import json
import logging
from typing import Final


class StdFormatter(logging.Formatter):
    COLORS: Final[dict[int, str]] = {
        logging.DEBUG: "\033[1;92m",
        logging.INFO: "\033[1;94m",
        logging.WARNING: "\033[1;93m",
        logging.ERROR: "\033[1;91m",
        logging.CRITICAL: "\033[1;91m",
    }

    fmt: str | None

    def __init__(self, *, fmt: str | None = None, datefmt: str | None = None) -> None:
        super().__init__()
        self.fmt: str | None = fmt
        self.datefmt: str | None = "%H:%M:%S" if datefmt is None else datefmt

    def format(self, record: logging.LogRecord) -> str:
        if self.fmt is not None:
            cslen: int = len("<colorstart>")
            celen: int = len("<colorend>")

            cs: int = self.fmt.find("<colorstart>")
            ce: int = self.fmt.find("<colorend>")

            if cs != -1 and ce != -1:
                fmt = (
                    f"{self.fmt[:cs]}"
                    f"{StdFormatter.COLORS[record.levelno]}"
                    f"{self.fmt[cs + cslen : ce]}"
                    "\033[0;0m"
                    f"{self.fmt[ce + celen :]}"
                )

        return logging.Formatter(fmt, datefmt=self.datefmt).format(record)


class JsonFormatter(logging.Formatter):
    keys: dict[str, str]

    def __init__(self, *, keys: dict[str, str] | None = None) -> None:
        super().__init__()
        self.keys: dict[str, str] = keys if keys is not None else {}

    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, str] = {}

        if self.keys.pop("message", None) is not None:
            entry["message"] = record.getMessage()

        if self.keys.pop("timestamp", None) is not None:
            entry["timestamp"] = dt.datetime.fromtimestamp(
                record.created,
                tz=dt.timezone.utc,
            ).isoformat()

        entry.update(
            {key: getattr(record, val) for key, val in self.keys.items()},
        )

        if record.exc_info is not None:
            entry["exception"] = self.formatException(record.exc_info)

        if record.stack_info is not None:
            entry["stack_info"] = self.formatStack(record.stack_info)

        return json.dumps(entry, default=str)


class DismissErrorsFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno < logging.WARNING
