import logger


def pytest_configure() -> None:
    logger.configure_logging()
