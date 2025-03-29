"""
Monitoring and Observability System for Berrys_AgentsV2.

This package provides a comprehensive monitoring and observability solution for the
Berrys_AgentsV2 platform, including metrics collection, structured logging, distributed
tracing, and alert management capabilities.

Usage:
    # Import specific modules as needed
    from shared.utils.src.monitoring.metrics import capture_metric
    from shared.utils.src.monitoring.logging import get_logger
    from shared.utils.src.monitoring.tracing import trace_request
    from shared.utils.src.monitoring.health import check_health
    from shared.utils.src.monitoring.alerts import trigger_alert
"""

__version__ = "1.0.0"

# Re-export common functions for easier imports
from shared.utils.src.monitoring.metrics import (
    capture_metric,
    increment_counter,
    record_timer,
    gauge,
    histogram,
)
from shared.utils.src.monitoring.logging import get_logger, LogLevel
from shared.utils.src.monitoring.tracing import trace, get_current_span
from shared.utils.src.monitoring.health import check_health, register_health_check
from shared.utils.src.monitoring.alerts import trigger_alert, AlertSeverity
