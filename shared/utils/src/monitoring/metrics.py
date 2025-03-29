"""
Metrics collection and reporting utilities for Berrys_AgentsV2 platform.

This module provides standardized metrics collection using Prometheus
for the Berrys_AgentsV2 production environment. It implements counters,
gauges, histograms, and summaries with consistent naming and labeling.
"""

import time
import logging
import threading
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, cast

from prometheus_client import Counter, Gauge, Histogram, Summary
from prometheus_client import push_to_gateway, start_http_server
from prometheus_client.core import CollectorRegistry

# Configure logging
logger = logging.getLogger(__name__)

class MetricsBackend(Enum):
    """Supported metrics backends."""
    
    PROMETHEUS = "prometheus"
    # Can be extended with other backends in the future if needed
    # DATADOG = "datadog"
    # CLOUDWATCH = "cloudwatch"


class MetricsManager:
    """Manages metrics collection and reporting for the application."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern to ensure only one metrics manager exists."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        """Initialize metrics manager if not already initialized."""
        if not getattr(self, "_initialized", False):
            self._backend = None
            self._registry = CollectorRegistry()
            self._prefix = ""
            self._default_labels = {}
            self._metrics = {
                "counter": {},
                "gauge": {},
                "histogram": {},
                "summary": {}
            }
            self._server_started = False
            self._push_gateway_url = None
            self._push_job_name = None
            self._initialized = True
    
    def configure(
        self,
        backend: MetricsBackend = MetricsBackend.PROMETHEUS,
        prefix: str = "",
        default_labels: Optional[Dict[str, str]] = None,
        expose_http: bool = True,
        http_port: int = 8000,
        push_gateway_url: Optional[str] = None,
        push_job_name: Optional[str] = None,
        push_interval: int = 60
    ) -> None:
        """
        Configure metrics collection.
        
        Args:
            backend: Metrics backend to use
            prefix: Prefix for all metric names
            default_labels: Default labels to add to all metrics
            expose_http: Whether to expose metrics via HTTP
            http_port: Port to expose metrics on
            push_gateway_url: URL of Prometheus push gateway
            push_job_name: Job name for push gateway
            push_interval: Interval in seconds to push metrics
        """
        self._backend = backend
        self._prefix = prefix
        self._default_labels = default_labels or {}
        
        if expose_http and not self._server_started:
            try:
                start_http_server(http_port, registry=self._registry)
                self._server_started = True
                logger.info(f"Metrics server started on port {http_port}")
            except Exception as e:
                logger.warning(f"Failed to start metrics server: {e}")
        
        if push_gateway_url:
            self._push_gateway_url = push_gateway_url
            self._push_job_name = push_job_name or "berrys_agents"
            
            # Start push thread if we have a push gateway
            if push_interval > 0:
                def push_metrics() -> None:
                    while True:
                        try:
                            push_to_gateway(
                                self._push_gateway_url,
                                job=self._push_job_name,
                                registry=self._registry
                            )
                        except Exception as e:
                            logger.warning(f"Failed to push metrics: {e}")
                        time.sleep(push_interval)
                
                thread = threading.Thread(target=push_metrics, daemon=True)
                thread.start()
    
    def _get_full_name(self, name: str) -> str:
        """
        Get full metric name with prefix.
        
        Args:
            name: Base metric name
            
        Returns:
            str: Full metric name with prefix
        """
        if self._prefix:
            return f"{self._prefix}_{name}"
        return name
    
    def _merge_labels(self, labels: Optional[Dict[str, str]]) -> Dict[str, str]:
        """
        Merge default labels with provided labels.
        
        Args:
            labels: Labels to merge with default labels
            
        Returns:
            Dict[str, str]: Merged labels
        """
        merged = self._default_labels.copy()
        if labels:
            merged.update(labels)
        return merged
    
    def counter(
        self,
        name: str,
        description: str = "",
        labels: Optional[Dict[str, str]] = None,
        documentation: Optional[str] = None
    ) -> Counter:
        """
        Get or create a counter metric.
        
        Args:
            name: Metric name
            description: Short description (deprecated, use documentation)
            labels: Labels to add to the metric
            documentation: Detailed documentation for the metric
            
        Returns:
            Counter: Prometheus counter
        """
        full_name = self._get_full_name(name)
        label_keys = tuple(sorted(self._merge_labels(labels).keys()))
        
        # Create key for metrics cache
        cache_key = f"{full_name}:{label_keys}"
        
        if cache_key not in self._metrics["counter"]:
            if documentation is None:
                documentation = description
            
            self._metrics["counter"][cache_key] = Counter(
                full_name,
                documentation,
                label_keys,
                registry=self._registry
            )
        
        return self._metrics["counter"][cache_key]
    
    def gauge(
        self,
        name: str,
        description: str = "",
        labels: Optional[Dict[str, str]] = None,
        documentation: Optional[str] = None
    ) -> Gauge:
        """
        Get or create a gauge metric.
        
        Args:
            name: Metric name
            description: Short description (deprecated, use documentation)
            labels: Labels to add to the metric
            documentation: Detailed documentation for the metric
            
        Returns:
            Gauge: Prometheus gauge
        """
        full_name = self._get_full_name(name)
        label_keys = tuple(sorted(self._merge_labels(labels).keys()))
        
        # Create key for metrics cache
        cache_key = f"{full_name}:{label_keys}"
        
        if cache_key not in self._metrics["gauge"]:
            if documentation is None:
                documentation = description
            
            self._metrics["gauge"][cache_key] = Gauge(
                full_name,
                documentation,
                label_keys,
                registry=self._registry
            )
        
        return self._metrics["gauge"][cache_key]
    
    def histogram(
        self,
        name: str,
        description: str = "",
        labels: Optional[Dict[str, str]] = None,
        buckets: Optional[List[float]] = None,
        documentation: Optional[str] = None
    ) -> Histogram:
        """
        Get or create a histogram metric.
        
        Args:
            name: Metric name
            description: Short description (deprecated, use documentation)
            labels: Labels to add to the metric
            buckets: Custom buckets for the histogram
            documentation: Detailed documentation for the metric
            
        Returns:
            Histogram: Prometheus histogram
        """
        full_name = self._get_full_name(name)
        label_keys = tuple(sorted(self._merge_labels(labels).keys()))
        
        # Create key for metrics cache
        bucket_key = str(buckets) if buckets else "default"
        cache_key = f"{full_name}:{label_keys}:{bucket_key}"
        
        if cache_key not in self._metrics["histogram"]:
            if documentation is None:
                documentation = description
            
            kwargs = {"registry": self._registry}
            if buckets:
                kwargs["buckets"] = buckets
            
            self._metrics["histogram"][cache_key] = Histogram(
                full_name,
                documentation,
                label_keys,
                **kwargs
            )
        
        return self._metrics["histogram"][cache_key]
    
    def summary(
        self,
        name: str,
        description: str = "",
        labels: Optional[Dict[str, str]] = None,
        documentation: Optional[str] = None
    ) -> Summary:
        """
        Get or create a summary metric.
        
        Args:
            name: Metric name
            description: Short description (deprecated, use documentation)
            labels: Labels to add to the metric
            documentation: Detailed documentation for the metric
            
        Returns:
            Summary: Prometheus summary
        """
        full_name = self._get_full_name(name)
        label_keys = tuple(sorted(self._merge_labels(labels).keys()))
        
        # Create key for metrics cache
        cache_key = f"{full_name}:{label_keys}"
        
        if cache_key not in self._metrics["summary"]:
            if documentation is None:
                documentation = description
            
            self._metrics["summary"][cache_key] = Summary(
                full_name,
                documentation,
                label_keys,
                registry=self._registry
            )
        
        return self._metrics["summary"][cache_key]
    
    def increment_counter(
        self,
        name: str,
        labels: Optional[Dict[str, str]] = None,
        value: float = 1.0
    ) -> None:
        """
        Increment a counter metric.
        
        Args:
            name: Metric name
            labels: Labels for the metric
            value: Value to increment by
        """
        if not self._backend:
            return
        
        try:
            counter = self.counter(name, labels=None)
            merged_labels = self._merge_labels(labels)
            if merged_labels:
                counter.labels(**merged_labels).inc(value)
            else:
                counter.inc(value)
        except Exception as e:
            logger.warning(f"Failed to increment counter {name}: {e}")
    
    def set_gauge(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Set a gauge metric value.
        
        Args:
            name: Metric name
            value: Value to set
            labels: Labels for the metric
        """
        if not self._backend:
            return
        
        try:
            gauge = self.gauge(name, labels=None)
            merged_labels = self._merge_labels(labels)
            if merged_labels:
                gauge.labels(**merged_labels).set(value)
            else:
                gauge.set(value)
        except Exception as e:
            logger.warning(f"Failed to set gauge {name}: {e}")
    
    def observe_histogram(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
        buckets: Optional[List[float]] = None
    ) -> None:
        """
        Observe a value in a histogram metric.
        
        Args:
            name: Metric name
            value: Value to observe
            labels: Labels for the metric
            buckets: Custom buckets for the histogram
        """
        if not self._backend:
            return
        
        try:
            histogram = self.histogram(name, labels=None, buckets=buckets)
            merged_labels = self._merge_labels(labels)
            if merged_labels:
                histogram.labels(**merged_labels).observe(value)
            else:
                histogram.observe(value)
        except Exception as e:
            logger.warning(f"Failed to observe histogram {name}: {e}")
    
    def observe_summary(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Observe a value in a summary metric.
        
        Args:
            name: Metric name
            value: Value to observe
            labels: Labels for the metric
        """
        if not self._backend:
            return
        
        try:
            summary = self.summary(name, labels=None)
            merged_labels = self._merge_labels(labels)
            if merged_labels:
                summary.labels(**merged_labels).observe(value)
            else:
                summary.observe(value)
        except Exception as e:
            logger.warning(f"Failed to observe summary {name}: {e}")
    
    def timing(
        self,
        name: str,
        labels: Optional[Dict[str, str]] = None
    ) -> "TimingContextManager":
        """
        Create a timing context manager for measuring execution time.
        
        Args:
            name: Metric name
            labels: Labels for the metric
            
        Returns:
            TimingContextManager: Context manager for timing
        """
        return TimingContextManager(self, name, labels)


class TimingContextManager:
    """Context manager for timing execution of code blocks."""
    
    def __init__(
        self,
        manager: MetricsManager,
        name: str,
        labels: Optional[Dict[str, str]] = None
    ):
        """
        Initialize timing context manager.
        
        Args:
            manager: Metrics manager
            name: Metric name
            labels: Labels for the metric
        """
        self.manager = manager
        self.name = name
        self.labels = labels
        self.start_time = 0.0
    
    def __enter__(self) -> "TimingContextManager":
        """Start timing on enter."""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Stop timing on exit and record duration."""
        duration = time.time() - self.start_time
        self.manager.observe_histogram(self.name, duration, self.labels)


# Global metrics manager instance
_metrics_manager = MetricsManager()

# Convenience functions for global metrics manager

def configure_metrics(
    backend: MetricsBackend = MetricsBackend.PROMETHEUS,
    prefix: str = "",
    default_labels: Optional[Dict[str, str]] = None,
    expose_http: bool = True,
    http_port: int = 8000,
    push_gateway_url: Optional[str] = None,
    push_job_name: Optional[str] = None,
    push_interval: int = 60
) -> None:
    """
    Configure metrics collection.
    
    Args:
        backend: Metrics backend to use
        prefix: Prefix for all metric names
        default_labels: Default labels to add to all metrics
        expose_http: Whether to expose metrics via HTTP
        http_port: Port to expose metrics on
        push_gateway_url: URL of Prometheus push gateway
        push_job_name: Job name for push gateway
        push_interval: Interval in seconds to push metrics
    """
    _metrics_manager.configure(
        backend=backend,
        prefix=prefix,
        default_labels=default_labels,
        expose_http=expose_http,
        http_port=http_port,
        push_gateway_url=push_gateway_url,
        push_job_name=push_job_name,
        push_interval=push_interval
    )

def increment_counter(
    name: str,
    labels: Optional[Dict[str, str]] = None,
    value: float = 1.0
) -> None:
    """
    Increment a counter metric.
    
    Args:
        name: Metric name
        labels: Labels for the metric
        value: Value to increment by
    """
    _metrics_manager.increment_counter(name, labels, value)

def gauge(
    name: str,
    value: float,
    labels: Optional[Dict[str, str]] = None
) -> None:
    """
    Set a gauge metric value.
    
    Args:
        name: Metric name
        value: Value to set
        labels: Labels for the metric
    """
    _metrics_manager.set_gauge(name, value, labels)

def histogram(
    name: str,
    value: float,
    labels: Optional[Dict[str, str]] = None,
    buckets: Optional[List[float]] = None
) -> None:
    """
    Observe a value in a histogram metric.
    
    Args:
        name: Metric name
        value: Value to observe
        labels: Labels for the metric
        buckets: Custom buckets for the histogram
    """
    _metrics_manager.observe_histogram(name, value, labels, buckets)

def summary(
    name: str,
    value: float,
    labels: Optional[Dict[str, str]] = None
) -> None:
    """
    Observe a value in a summary metric.
    
    Args:
        name: Metric name
        value: Value to observe
        labels: Labels for the metric
    """
    _metrics_manager.observe_summary(name, value, labels)

def timing(
    name: str,
    labels: Optional[Dict[str, str]] = None
) -> TimingContextManager:
    """
    Create a timing context manager for measuring execution time.
    
    Args:
        name: Metric name
        labels: Labels for the metric
        
    Returns:
        TimingContextManager: Context manager for timing
    """
    return _metrics_manager.timing(name, labels)

def capture_metric(
    name: str,
    value: float,
    metric_type: str = "counter",
    labels: Optional[Dict[str, str]] = None
) -> None:
    """
    Capture a metric of the specified type.
    
    Args:
        name: Metric name
        value: Value to record
        metric_type: Type of metric (counter, gauge, histogram, summary)
        labels: Labels for the metric
    """
    if metric_type == "counter":
        increment_counter(name, labels, value)
    elif metric_type == "gauge":
        gauge(name, value, labels)
    elif metric_type == "histogram":
        histogram(name, value, labels)
    elif metric_type == "summary":
        summary(name, value, labels)
    else:
        logger.warning(f"Unknown metric type: {metric_type}")

def record_timer(
    name: str,
    seconds: float,
    labels: Optional[Dict[str, str]] = None
) -> None:
    """
    Record a timing metric.
    
    Args:
        name: Metric name
        seconds: Duration in seconds
        labels: Labels for the metric
    """
    histogram(name, seconds, labels)


# Example FastAPI middleware for HTTP request metrics:
"""
@app.middleware("http")
async def metrics_middleware(request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    # Record request duration
    duration = time.time() - start_time
    histogram(
        "http_request_duration_seconds",
        duration,
        {
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code
        }
    )
    
    # Increment request counter
    increment_counter(
        "http_requests_total",
        {
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code
        }
    )
    
    return response
"""
