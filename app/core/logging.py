"""
Logging Configuration Module
Provides formatted console and file logging with log rotation.
"""

import sys
import logging
from pathlib import Path
from app.core.config import settings, PROJECT_ROOT

def setup_logging() -> logging.Logger:
    """Configures application-wide logging based on settings."""
    log_dir = PROJECT_ROOT / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "app.log"

    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Root logger configuration
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
        force=True
    )

    logger = logging.getLogger("app")
    logger.info(f"Logging initialized at level {settings.LOG_LEVEL} (File: {log_file})")
    return logger

logger = logging.getLogger("app")
