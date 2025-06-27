import logging
import os
import sys
from typing import Union

import structlog

_log_init = False


_structlog_shared_processors = [
    structlog.stdlib.add_log_level,
    structlog.stdlib.add_logger_name,
    structlog.stdlib.ExtraAdder(),
]


def _handle_exception(exc_type, exc_value, exc_traceback):
    """
    Log any uncaught exception instead of letting it be printed by Python
    (but leave KeyboardInterrupt untouched to allow users to Ctrl+C to stop)
    See https://stackoverflow.com/a/16993115/3641865
    """
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    root_logger = logging.getLogger()
    root_logger.error(
        "Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback)
    )


def _config_log_level(
    base_log_level: Union[int, str], app_log_level: Union[int, str], app_root_pkg: str
):
    # set base log level on root logger
    root_logger = logging.getLogger()
    if isinstance(base_log_level, str):
        base_log_level = base_log_level.upper()
    root_logger.setLevel(base_log_level)

    # set app log level on app logger
    if isinstance(app_log_level, str):
        app_log_level = app_log_level.upper()
    logging.getLogger("__main__").setLevel(app_log_level)
    logging.getLogger(app_root_pkg).setLevel(app_log_level)


def _structlog_common_config():
    # Capture all warning
    logging.captureWarnings(True)
    # Prepare event dict for `ProcessorFormatter`.
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.contextvars.merge_contextvars,
        ]
        + _structlog_shared_processors
        + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def _replace_handlers(formatter):
    structlog_handler = logging.StreamHandler()
    structlog_handler.setFormatter(formatter)
    # Handover to stdlib logging
    root_logger = logging.getLogger()
    root_logger.addHandler(structlog_handler)


def _structlog_console_formatter():
    colors = os.environ.get("NO_COLOR", "") == ""
    return structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=_structlog_shared_processors,
        processors=[
            structlog.processors.TimeStamper(fmt="%H:%M:%S", utc=False),
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.dev.ConsoleRenderer(colors=colors),
        ],
    )


def _structlog_json_formatter():
    return structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=_structlog_shared_processors,
        processors=[
            structlog.processors.dict_tracebacks,
            structlog.processors.TimeStamper(fmt="iso", key="@timestamp"),
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.EventRenamer(to="message"),
            structlog.processors.JSONRenderer(),
        ],
    )


def _structlog_logfmt_formatter():
    return structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=_structlog_shared_processors,
        processors=[
            structlog.processors.format_exc_info,
            structlog.processors.TimeStamper(fmt="iso", key="@timestamp"),
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.EventRenamer(to="message"),
            structlog.processors.LogfmtRenderer(
                sort_keys=True, key_order=["@timestamp", "level", "logger", "message"]
            ),
        ],
    )


def _structlog_airflow_formatter():
    return structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=_structlog_shared_processors,
        processors=[
            structlog.processors.TimeStamper(fmt="%H:%M:%S", utc=True),
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.dev.ConsoleRenderer(
                columns=[
                    structlog.dev.Column(
                        "timestamp",
                        structlog.dev.KeyValueColumnFormatter(
                            key_style=None,
                            value_style="",
                            reset_style="",
                            value_repr=str,
                        ),
                    ),
                    structlog.dev.Column(
                        "event",
                        structlog.dev.KeyValueColumnFormatter(
                            key_style=None,
                            value_style="",
                            reset_style="",
                            value_repr=str,
                        ),
                    ),
                    structlog.dev.Column(
                        "",
                        structlog.dev.KeyValueColumnFormatter(
                            key_style="",
                            value_style="",
                            reset_style="",
                            value_repr=repr,
                        ),
                    ),
                ],
                exception_formatter=structlog.dev.plain_traceback,
            ),
        ],
    )


def console_logging():
    formatter = _structlog_console_formatter()
    _replace_handlers(formatter)


def json_logging():
    formatter = _structlog_json_formatter()
    _replace_handlers(formatter)


def logfmt_logging():
    formatter = _structlog_logfmt_formatter()
    _replace_handlers(formatter)


def airflow_logging():
    formatter = _structlog_airflow_formatter()
    _replace_handlers(formatter)


def init_logging(
    log_format: str,
    base_log_level: Union[int, str],
    app_log_level: Union[int, str],
    app_root_pkg: str,
):
    global _log_init
    if not _log_init:
        # hook exception for logging
        sys.excepthook = _handle_exception
        # Common config
        _config_log_level(base_log_level, app_log_level, app_root_pkg)
        _structlog_common_config()
        # config structlog output
        if log_format == "json":
            json_logging()
        elif log_format == "logfmt":
            logfmt_logging()
        elif log_format == "airflow":
            airflow_logging()
        else:
            console_logging()
        _log_init = True


def pytest_log_formatter() -> logging.Formatter:
    """
    Return a formatter suitable for pytest
    :return:
    """
    _structlog_common_config()
    return _structlog_console_formatter()
