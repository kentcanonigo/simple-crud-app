import json
import time
import logging
import requests
from datetime import datetime
from typing import Optional, Dict, Any
import os


class SplunkHECHandler:
    """Splunk HTTP Event Collector (HEC) handler for sending logs and metrics"""

    def __init__(self, hec_url: str, hec_token: str, index: str = "main",
                 source: str = "todoapp", sourcetype: str = "json", verify_ssl: bool = True):
        self.hec_url = hec_url.rstrip('/')
        self.hec_token = hec_token
        self.index = index
        self.source = source
        self.sourcetype = sourcetype
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Splunk {hec_token}',
            'Content-Type': 'application/json'
        })

    def send_event(self, event_data: Dict[str, Any], event_time: Optional[float] = None) -> bool:
        """Send a single event to Splunk HEC"""
        if event_time is None:
            event_time = time.time()

        payload = {
            "time": event_time,
            "host": os.environ.get('HOSTNAME', 'localhost'),
            "source": self.source,
            "sourcetype": self.sourcetype,
            "index": self.index,
            "event": event_data
        }

        try:
            response = self.session.post(
                f"{self.hec_url}/services/collector",
                data=json.dumps(payload),
                verify=self.verify_ssl,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logging.error(f"Failed to send event to Splunk: {e}")
            return False

    def send_metric(self, metric_name: str, metric_value: float,
                   dimensions: Optional[Dict[str, str]] = None,
                   metric_time: Optional[float] = None) -> bool:
        """Send a metric to Splunk HEC"""
        if metric_time is None:
            metric_time = time.time()

        if dimensions is None:
            dimensions = {}

        payload = {
            "time": metric_time,
            "host": os.environ.get('HOSTNAME', 'localhost'),
            "source": self.source,
            "sourcetype": "prometheus:metric",
            "index": self.index,
            "event": "metric",
            "fields": {
                "metric_name": metric_name,
                "_value": metric_value,
                **dimensions
            }
        }

        try:
            response = self.session.post(
                f"{self.hec_url}/services/collector",
                data=json.dumps(payload),
                verify=self.verify_ssl,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logging.error(f"Failed to send metric to Splunk: {e}")
            return False


class SplunkMetricsExporter:
    """Export Prometheus metrics to Splunk"""

    def __init__(self, hec_handler: SplunkHECHandler):
        self.hec_handler = hec_handler

    def export_prometheus_metrics(self, registry=None) -> Dict[str, Any]:
        """Export all Prometheus metrics to Splunk"""
        from prometheus_client import REGISTRY

        if registry is None:
            registry = REGISTRY

        exported_count = 0
        errors = []

        for collector in registry._collector_to_names:
            try:
                for metric in collector.collect():
                    for sample in metric.samples:
                        # Create dimensions from labels
                        dimensions = dict(sample.labels) if sample.labels else {}
                        dimensions['metric_type'] = metric.type

                        # Send metric to Splunk
                        success = self.hec_handler.send_metric(
                            metric_name=sample.name,
                            metric_value=sample.value,
                            dimensions=dimensions
                        )

                        if success:
                            exported_count += 1
                        else:
                            errors.append(f"Failed to export {sample.name}")

            except Exception as e:
                errors.append(f"Error collecting metrics from {collector}: {e}")

        return {
            "exported_count": exported_count,
            "errors": errors,
            "timestamp": datetime.utcnow().isoformat()
        }


class SplunkLogger:
    """Custom logger that sends structured logs to Splunk"""

    def __init__(self, hec_handler: SplunkHECHandler, app_name: str = "todoapp"):
        self.hec_handler = hec_handler
        self.app_name = app_name

    def log_request(self, method: str, endpoint: str, status_code: int,
                   duration: float, user_id: Optional[str] = None):
        """Log HTTP request details"""
        event_data = {
            "event_type": "http_request",
            "app": self.app_name,
            "method": method,
            "endpoint": endpoint,
            "status_code": status_code,
            "duration_seconds": duration,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.hec_handler.send_event(event_data)

    def log_database_operation(self, operation: str, table: str,
                              success: bool, duration: Optional[float] = None):
        """Log database operations"""
        event_data = {
            "event_type": "database_operation",
            "app": self.app_name,
            "operation": operation,
            "table": table,
            "success": success,
            "duration_seconds": duration,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.hec_handler.send_event(event_data)

    def log_business_event(self, event_type: str, details: Dict[str, Any]):
        """Log business logic events"""
        event_data = {
            "event_type": "business_event",
            "app": self.app_name,
            "business_event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            **details
        }
        self.hec_handler.send_event(event_data)

    def log_error(self, error_type: str, error_message: str,
                 stack_trace: Optional[str] = None, context: Optional[Dict] = None):
        """Log application errors"""
        event_data = {
            "event_type": "application_error",
            "app": self.app_name,
            "error_type": error_type,
            "error_message": error_message,
            "stack_trace": stack_trace,
            "context": context or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        self.hec_handler.send_event(event_data)


def create_splunk_integration() -> tuple[Optional[SplunkHECHandler],
                                       Optional[SplunkMetricsExporter],
                                       Optional[SplunkLogger]]:
    """Create Splunk integration components based on environment configuration"""
    hec_url = os.environ.get('SPLUNK_HEC_URL')
    hec_token = os.environ.get('SPLUNK_HEC_TOKEN')

    if not hec_url or not hec_token:
        return None, None, None

    # Optional configuration
    index = os.environ.get('SPLUNK_INDEX', 'main')
    source = os.environ.get('SPLUNK_SOURCE', 'todoapp')
    verify_ssl = os.environ.get('SPLUNK_VERIFY_SSL', 'true').lower() == 'true'

    try:
        hec_handler = SplunkHECHandler(
            hec_url=hec_url,
            hec_token=hec_token,
            index=index,
            source=source,
            verify_ssl=verify_ssl
        )

        metrics_exporter = SplunkMetricsExporter(hec_handler)
        splunk_logger = SplunkLogger(hec_handler)

        return hec_handler, metrics_exporter, splunk_logger

    except Exception as e:
        logging.error(f"Failed to initialize Splunk integration: {e}")
        return None, None, None