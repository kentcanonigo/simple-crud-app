import json
import logging
import time
from datetime import datetime
from flask import request, g

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""

    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'app': 'todoapp',
            'service': 'todo-api'
        }

        # Add request context if available
        try:
            if request:
                log_entry['http_method'] = request.method
                log_entry['url'] = request.path
                log_entry['remote_addr'] = request.remote_addr
                log_entry['user_agent'] = request.headers.get('User-Agent', '')
                log_entry['request_id'] = getattr(g, 'request_id', '')
        except RuntimeError:
            # Outside request context
            pass

        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)

        return json.dumps(log_entry)

def setup_structured_logging():
    """Configure structured JSON logging for Kubernetes/Splunk"""

    # Create JSON formatter
    json_formatter = JSONFormatter()

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Remove default handlers
    root_logger.handlers.clear()

    # Add console handler with JSON formatter
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(json_formatter)
    root_logger.addHandler(console_handler)

    # Configure specific loggers
    logging.getLogger('werkzeug').setLevel(logging.WARNING)  # Reduce Flask noise
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)  # Reduce SQLAlchemy noise

    return root_logger

class StructuredLogger:
    """Helper class for structured business event logging"""

    def __init__(self, logger_name='todoapp'):
        self.logger = logging.getLogger(logger_name)

    def log_business_event(self, event_type, data=None, log_level='INFO'):
        """Log business events with structured data"""
        log_data = {
            'event_type': 'business_event',
            'business_event': event_type,
            'data': data or {},
            'log_level': log_level
        }

        # Add to record for JSON formatter
        record = logging.LogRecord(
            name=self.logger.name,
            level=getattr(logging, log_level.upper(), logging.INFO),
            pathname='',
            lineno=0,
            msg=f"Business event: {event_type}",
            args=(),
            exc_info=None
        )
        record.extra_fields = log_data

        self.logger.handle(record)

    def log_database_operation(self, operation, table, success, error=None, log_level=None):
        """Log database operations"""
        if log_level is None:
            log_level = 'INFO' if success else 'ERROR'

        log_data = {
            'event_type': 'database_operation',
            'operation': operation,
            'table': table,
            'success': success,
            'error': error,
            'log_level': log_level
        }

        level = getattr(logging, log_level.upper(), logging.INFO)
        message = f"Database {operation} on {table}: {'SUCCESS' if success else 'FAILED'}"

        record = logging.LogRecord(
            name=self.logger.name,
            level=level,
            pathname='',
            lineno=0,
            msg=message,
            args=(),
            exc_info=None
        )
        record.extra_fields = log_data

        self.logger.handle(record)

    def log_request(self, method, endpoint, status_code, duration, log_level=None):
        """Log HTTP request details"""
        if log_level is None:
            log_level = 'INFO' if status_code < 400 else 'WARN'

        log_data = {
            'event_type': 'http_request',
            'http_method': method,
            'endpoint': endpoint,
            'status_code': status_code,
            'duration_seconds': duration,
            'log_level': log_level
        }

        level = getattr(logging, log_level.upper(), logging.INFO)
        message = f"{method} {endpoint} {status_code} ({duration:.3f}s)"

        record = logging.LogRecord(
            name=self.logger.name,
            level=level,
            pathname='',
            lineno=0,
            msg=message,
            args=(),
            exc_info=None
        )
        record.extra_fields = log_data

        self.logger.handle(record)

    def log_error(self, error_type, error_message, context=None, log_level='ERROR'):
        """Log application errors"""
        log_data = {
            'event_type': 'application_error',
            'error_type': error_type,
            'error_message': error_message,
            'context': context or {},
            'log_level': log_level
        }

        record = logging.LogRecord(
            name=self.logger.name,
            level=getattr(logging, log_level.upper(), logging.ERROR),
            pathname='',
            lineno=0,
            msg=f"Application error: {error_type} - {error_message}",
            args=(),
            exc_info=None
        )
        record.extra_fields = log_data

        self.logger.handle(record)