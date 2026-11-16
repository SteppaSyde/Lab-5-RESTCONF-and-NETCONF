import logging
import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
REPORT_DIR = PROJECT_ROOT / "data" / "reports"
LOG_PATH = PROJECT_ROOT / "logs" / "lab5.log"


def configure_logging() -> logging.Logger:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("lab5")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)

    return logger


def get_credentials() -> tuple[str, str, str]:
    names = ("DEVICE_HOST", "DEVICE_USERNAME", "DEVICE_PASSWORD")
    values = tuple(os.getenv(name, "") for name in names)
    missing = [name for name, value in zip(names, values) if not value.strip()]
    if missing:
        raise RuntimeError(
            "Set the required environment variables before running: "
            + ", ".join(missing)
        )
    return values


def get_port(environment_name: str, default: int) -> int:
    value = os.getenv(environment_name)
    if value is None:
        return default
    try:
        port = int(value)
    except ValueError as exc:
        raise RuntimeError(f"{environment_name} must be a valid TCP port") from exc
    if not 1 <= port <= 65535:
        raise RuntimeError(f"{environment_name} must be between 1 and 65535")
    return port
