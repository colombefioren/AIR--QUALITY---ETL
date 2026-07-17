import logging
import sys


def setup_logging():
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.handlers.clear()

    console_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%H:%M:%S'
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.info("Logging configuration completed")

    return root_logger
