import logging
import logging.handlers
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional

# ANSI color codes for console output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Configure the root logger
def setup_logger(name: str = "supervisor_agent", level: int = logging.INFO) -> logging.Logger:
    """
    Set up a logger with console and file handlers.
    
    Args:
        name: The name of the logger
        level: The logging level
        
    Returns:
        A configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Clear any existing handlers
    if logger.handlers:
        logger.handlers.clear()
    
    # Create formatters
    class ColoredFormatter(logging.Formatter):
        def format(self, record):
            # For console: only show level and message
            level_color = {
                'INFO': Colors.GREEN,
                'WARNING': Colors.YELLOW,
                'ERROR': Colors.RED,
                'CRITICAL': Colors.RED
            }.get(record.levelname, '')
            
            # Handle both JSON and string messages
            if isinstance(record.msg, str):
                if record.msg.startswith('{'):
                    try:
                        # Parse JSON message and extract just the message field
                        log_data = json.loads(record.msg)
                        message = log_data.get('message', record.msg)
                    except json.JSONDecodeError:
                        message = record.msg
                else:
                    message = record.msg
                
                record.msg = f"{level_color}{record.levelname}{Colors.RESET}: {message}"
            
            return super().format(record)
    
    console_formatter = ColoredFormatter('%(message)s')
    
    # File handler gets the full JSON format
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler with rotation
    log_file = os.path.join("logs", f"{name}.log")
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    return logger

# Create a structured logger
class StructuredLogger:
    """
    A logger that outputs structured JSON logs.
    """
    def __init__(self, name: str = "supervisor_agent", level: int = logging.INFO):
        self.logger = setup_logger(name, level)
        self.name = name
    
    def _log(self, level: int, message: str, **kwargs):
        """
        Log a message with additional structured data.
        
        Args:
            level: The logging level
            message: The log message
            **kwargs: Additional fields to include in the structured log
        """
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "level": logging.getLevelName(level),
            "logger": self.name,
            "message": message,
            **kwargs
        }
        
        self.logger.log(level, json.dumps(log_data))
    
    def debug(self, message: str, **kwargs):
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        self._log(logging.CRITICAL, message, **kwargs)
    
    def check_result(self, check_type: str, status: str, message: str, **kwargs):
        """
        Log a check result with structured data.
        
        Args:
            check_type: The type of check (e.g., 'morning', 'evening')
            status: The result status (e.g., 'PASS', 'FAIL')
            message: A descriptive message
            **kwargs: Additional fields to include
        """
        self._log(
            logging.INFO if status == 'PASS' else logging.WARNING,
            f"{check_type.capitalize()} check: {message}",
            check_type=check_type,
            status=status,
            **kwargs
        )

# Create a singleton instance
logger = StructuredLogger()

# Helper functions for common logging patterns
def log_check_result(check_type: str, status: str, message: str, **kwargs):
    """
    Log a check result.
    
    Args:
        check_type: The type of check (e.g., 'morning', 'evening')
        status: The result status (e.g., 'PASS', 'FAIL')
        message: A descriptive message
        **kwargs: Additional fields to include
    """
    logger.check_result(check_type, status, message, **kwargs)

def log_api_request(method: str, path: str, params: Optional[Dict[str, Any]] = None):
    """
    Log an API request.
    
    Args:
        method: The HTTP method
        path: The request path
        params: Request parameters
    """
    logger.info(f"API Request: {method} {path}", method=method, path=path, params=params)

def log_api_response(status_code: int, response_time_ms: float):
    """
    Log an API response.
    
    Args:
        status_code: The HTTP status code
        response_time_ms: The response time in milliseconds
    """
    logger.info(
        f"API Response: {status_code} ({response_time_ms:.2f}ms)",
        status_code=status_code,
        response_time_ms=response_time_ms
    ) 