import logging
import sys
from pathlib import Path

def setup_logger(name: str = "PQC-Benchmark", log_file: str = None, level: int = logging.INFO) -> logging.Logger:
    """
    Sets up a logger with the specified name, log file, and logging level.
    
    Args:
        name: The name of the logger.
        log_file: Path to the log file. If None, only logs to console.
        level: Logging level (e.g., logging.INFO, logging.DEBUG).
        
    Returns:
        A configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid adding handlers multiple times if logger is already configured
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
