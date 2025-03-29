"""
Prometheus exporter for the Berrys_AgentsV2 monitoring system.

This module provides functionality for exporting metrics to Prometheus, including
a Prometheus formatter that converts internal metrics to Prometheus format.

Usage:
    from shared.utils.src.monitoring.exporters.prometheus import (
        PrometheusExporter,
        start_prometheus_server,
    )

    # Export metrics to Prometheus
    exporter = PrometheusExporter()
    metrics_text = exporter.export_metrics()

    # Or start a Prometheus metrics server
    start_prometheus_server(port=8000)
"""

import threading
import time
from typing import Dict, Any, List, Optional, Union, cast
from http.server import HTTPServer, BaseHTTPRequestHandler
import logging

from shared.utils.src.monitoring.metrics import get_metrics, MetricType

# Configure basic logging
logger = logging.getLogger(__name__)


class PrometheusFormatter:
    """
    Formatter that converts internal metrics to Prometheus format.
    """
    
    def __init__(self, prefix: Optional[str] = None):
        """
        Initialize the formatter.
        
        Args:
            prefix: Optional prefix for metric names
        """
        self.prefix = prefix
    
    def format_metrics(self, metrics: Dict[str, Any]) -> str:
        """
        Format metrics in Prometheus format.
        
        Args:
            metrics: The metrics to format
            
        Returns:
            A string in Prometheus format
        """
        lines = []
        
        # Process each metric
        for key, value in metrics.items():
            # Parse the metric name and labels
            metric_name, labels = self._parse_metric_key(key)
            
            # Add prefix if provided
            if self.prefix:
                metric_name = f"{self.prefix}_{metric_name}"
            
            # Format labels for Prometheus
            labels_str = ",".join(f'{k}="{v}"' for k, v in labels.items())
            if labels_str:
                labels_str = f"{{{labels_str}}}"
            
            # Add the metric to the output
            lines.append(f"{metric_name}{labels_str} {value}")
        
        return "\n".join(lines)
    
    def _parse_metric_key(self, key: str) -> tuple:
        """
        Parse a metric key into name and labels.
        
        Args:
            key: The metric key (e.g., "metric_name{label1=value1,label2=value2}")
            
        Returns:
            A tuple of (metric_name, labels_dict)
        """
        # Split the key into name and labels
        if "{" in key and key.endswith("}"):
            name_part, labels_part = key.split("{", 1)
            labels_part = labels_part[:-1]  # Remove the trailing "}"
            
            # Parse labels
            labels = {}
            for label in labels_part.split(","):
                if "=" in label:
                    label_name, label_value = label.split("=", 1)
                    labels[label_name.strip()] = label_value.strip()
            
            return name_part, labels
        else:
            return key, {}


class PrometheusExporter:
    """
    Exporter for converting internal metrics to Prometheus format.
    """
    
    def __init__(self, prefix: Optional[str] = None):
        """
        Initialize the exporter.
        
        Args:
            prefix: Optional prefix for metric names
        """
        self.formatter = PrometheusFormatter(prefix)
    
    def export_metrics(self) -> str:
        """
        Export metrics in Prometheus format.
        
        Returns:
            A string in Prometheus format
        """
        metrics = get_metrics()
        return self.formatter.format_metrics(metrics)


class PrometheusRequestHandler(BaseHTTPRequestHandler):
    """
    HTTP request handler for the Prometheus metrics server.
    """
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == "/metrics":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            
            exporter = PrometheusExporter()
            metrics_text = exporter.export_metrics()
            
            self.wfile.write(metrics_text.encode("utf-8"))
        elif self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            
            html = """
            <html>
            <head><title>Berrys_AgentsV2 Metrics</title></head>
            <body>
                <h1>Berrys_AgentsV2 Metrics</h1>
                <p><a href="/metrics">Metrics</a></p>
            </body>
            </html>
            """
            
            self.wfile.write(html.encode("utf-8"))
        else:
            self.send_response(404)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Not Found")
    
    def log_message(self, format, *args):
        """Override log_message to use our logger."""
        logger.info(f"Prometheus server: {format % args}")


def start_prometheus_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    server_class=HTTPServer,
    handler_class=PrometheusRequestHandler,
) -> threading.Thread:
    """
    Start a Prometheus metrics server in a background thread.
    
    Args:
        host: The host to listen on
        port: The port to listen on
        server_class: The HTTP server class to use
        handler_class: The request handler class to use
        
    Returns:
        The server thread
    """
    server_address = (host, port)
    httpd = server_class(server_address, handler_class)
    
    def serve_forever():
        logger.info(f"Starting Prometheus metrics server on {host}:{port}")
        httpd.serve_forever()
    
    thread = threading.Thread(target=serve_forever, daemon=True)
    thread.start()
    
    return thread


def register_with_pushgateway(
    gateway_url: str,
    job: str,
    instance: Optional[str] = None,
    interval: int = 60,
) -> threading.Thread:
    """
    Periodically push metrics to a Prometheus Pushgateway.
    
    Args:
        gateway_url: The URL of the Pushgateway
        job: The job name
        instance: The instance name (defaults to hostname)
        interval: The interval in seconds between pushes
        
    Returns:
        The pusher thread
    """
    import socket
    import requests
    
    if instance is None:
        instance = socket.gethostname()
    
    def push_metrics():
        while True:
            try:
                exporter = PrometheusExporter()
                metrics_text = exporter.export_metrics()
                
                response = requests.post(
                    f"{gateway_url}/metrics/job/{job}/instance/{instance}",
                    data=metrics_text,
                    headers={"Content-Type": "text/plain"},
                )
                
                response.raise_for_status()
                logger.debug(f"Pushed metrics to Pushgateway: {gateway_url}")
            except Exception as e:
                logger.error(f"Failed to push metrics to Pushgateway: {str(e)}")
            
            time.sleep(interval)
    
    thread = threading.Thread(target=push_metrics, daemon=True)
    thread.start()
    
    return thread


def get_prometheus_client_registry():
    """
    Get a Prometheus client registry for use with the official Prometheus client.
    
    This function requires the prometheus_client package to be installed.
    
    Returns:
        A Prometheus client registry
    """
    try:
        from prometheus_client import CollectorRegistry, Gauge, Counter, Histogram
        
        registry = CollectorRegistry()
        
        # Get our internal metrics
        metrics = get_metrics()
        
        # Convert internal metrics to Prometheus client metrics
        for key, value in metrics.items():
            metric_name, labels = PrometheusFormatter()._parse_metric_key(key)
            
            # Determine metric type (this is a heuristic)
            if metric_name.endswith("_total"):
                counter = Counter(metric_name, metric_name, labels.keys(), registry=registry)
                counter.labels(**labels)._value.set(value)
            elif metric_name.endswith("_seconds"):
                histogram = Histogram(metric_name, metric_name, labels.keys(), registry=registry)
                histogram.labels(**labels).observe(value)
            else:
                gauge = Gauge(metric_name, metric_name, labels.keys(), registry=registry)
                gauge.labels(**labels).set(value)
        
        return registry
    except ImportError:
        logger.error("prometheus_client package is required for get_prometheus_client_registry")
        return None
