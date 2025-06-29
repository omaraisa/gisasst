import logging
import os
from datetime import datetime
from pathlib import Path

def setup_logging(log_level='INFO', log_to_file=True, log_to_console=True):
    """Setup logging configuration for the GIS Copilot application"""
    
    # Create logs directory if it doesn't exist
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    # Create log filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f'gis_copilot_{timestamp}.log'
    
    # Configure logging format
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Set logging level
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Clear any existing handlers
    logging.getLogger().handlers.clear()
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        format=log_format,
        datefmt=date_format,
        handlers=[]
    )
    
    # Get root logger
    logger = logging.getLogger()
    
    # Add file handler if requested
    if log_to_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(log_format, date_format)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # Add console handler if requested
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_formatter = logging.Formatter(log_format, date_format)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # Log the setup
    logger.info(f"Logging system initialized - Level: {log_level}, File: {log_file if log_to_file else 'None'}")
    
    return logger, log_file

def get_logger(name):
    """Get a logger with the specified name"""
    return logging.getLogger(name)

def log_exception(logger, message="An error occurred"):
    """Log an exception with full traceback"""
    logger.exception(message)

def log_system_info(logger):
    """Log system information"""
    import sys
    import platform
    
    logger.info("=== System Information ===")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Platform: {platform.platform()}")
    logger.info(f"Architecture: {platform.architecture()}")
    logger.info(f"Processor: {platform.processor()}")
    logger.info("=========================")

def cleanup_old_logs(max_age_days=30):
    """Clean up log files older than max_age_days"""
    log_dir = Path('logs')
    if not log_dir.exists():
        return
    
    import time
    current_time = time.time()
    max_age_seconds = max_age_days * 24 * 60 * 60
    
    cleaned_count = 0
    for log_file in log_dir.glob('gis_copilot_*.log'):
        file_age = current_time - log_file.stat().st_mtime
        if file_age > max_age_seconds:
            try:
                log_file.unlink()
                cleaned_count += 1
            except Exception:
                pass  # Ignore errors when cleaning up
    
    if cleaned_count > 0:
        logger = get_logger(__name__)
        logger.info(f"Cleaned up {cleaned_count} old log files")
