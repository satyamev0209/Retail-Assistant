"""Structured logging configuration."""
import logging
import json
import time
import sys
from functools import wraps
from typing import Any, Callable

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_obj = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, "extra"):
            log_obj.update(record.extra)
            
        # Add exception info if present
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_obj)

def get_logger(name: str) -> logging.Logger:
    """Get a structured logger."""
    logger = logging.getLogger(name)
    
    # Only configure if not already configured
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        # Prevent propagation to avoid double logging if root logger is also configured
        logger.propagate = False
    
    return logger

def log_execution_time(logger: logging.Logger):
    """Decorator to log execution time of a function."""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Create a specialized log record
                extra = {
                    "event_type": "performance",
                    "duration_seconds": round(duration, 4),
                    "status": "success"
                }
                
                # We need to pass extra as a dict to be accessible in the formatter
                # However, standard logging doesn't easily support arbitrary dict merging in record
                # So we'll just log a structured message
                logger.info(
                    f"Executed {func.__name__}", 
                    extra={"extra": extra}
                )
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                extra = {
                    "event_type": "performance",
                    "duration_seconds": round(duration, 4),
                    "status": "error",
                    "error_type": type(e).__name__
                }
                logger.error(
                    f"Failed {func.__name__}: {str(e)}", 
                    extra={"extra": extra}
                )
                raise
        return wrapper
    return decorator
