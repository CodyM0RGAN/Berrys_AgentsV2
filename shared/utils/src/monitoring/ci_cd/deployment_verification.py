"""
Deployment verification for the Berrys_AgentsV2 monitoring system.

This module provides functionality for verifying deployments, including health checks,
metric monitoring, and performance regression detection. It integrates with the
CI/CD pipeline to ensure deployments are healthy and performing as expected.

Usage:
    from shared.utils.src.monitoring.ci_cd.deployment_verification import (
        verify_deployment,
        monitor_canary_deployment,
    )

    # Verify a deployment
    success, results = verify_deployment("api-gateway", "https://api.example.com")

    # Monitor a canary deployment
    canary_monitor = monitor_canary_deployment(
        "api-gateway",
        "https://canary.example.com",
        "https://prod.example.com",
        threshold=1.2  # Allow 20% degradation
    )
"""

import json
import logging
import time
import threading
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union, Callable

import requests

from shared.utils.src.monitoring.alerts import trigger_alert, AlertSeverity
from shared.utils.src.monitoring.metrics import capture_metric

# Configure basic logging
logger = logging.getLogger(__name__)


class VerificationStatus(Enum):
    """Status values for deployment verification."""
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"
    UNKNOWN = "unknown"


class VerificationType(Enum):
    """Types of deployment verification."""
    HEALTH = "health"
    METRICS = "metrics"
    PERFORMANCE = "performance"
    LOGS = "logs"
    CUSTOM = "custom"


def verify_deployment(
    service_name: str,
    base_url: str,
    verify_health: bool = True,
    verify_metrics: bool = True,
    verify_performance: bool = True,
    custom_checks: Optional[List[Callable[[], Tuple[bool, str]]]] = None,
    timeout: int = 60,
    retries: int = 3,
    retry_delay: int = 5,
) -> Tuple[bool, Dict[str, Any]]:
    """
    Verify a deployment by performing various checks.
    
    Args:
        service_name: The name of the service being verified
        base_url: The base URL of the deployed service
        verify_health: Whether to verify service health
        verify_metrics: Whether to verify service metrics
        verify_performance: Whether to verify service performance
        custom_checks: Custom verification functions
        timeout: Timeout in seconds for each check
        retries: Number of retries for each check
        retry_delay: Delay in seconds between retries
        
    Returns:
        A tuple of (success, results) where success is a boolean indicating
        whether all checks passed, and results is a dictionary of check results
    """
    logger.info(f"Verifying deployment of {service_name} at {base_url}")
    
    # Initialize results
    results = {
        "service": service_name,
        "base_url": base_url,
        "timestamp": time.time(),
        "overall_status": VerificationStatus.UNKNOWN.value,
        "checks": [],
    }
    
    # Verify health
    if verify_health:
        health_result = _verify_health(base_url, timeout, retries, retry_delay)
        results["checks"].append(health_result)
    
    # Verify metrics
    if verify_metrics:
        metrics_result = _verify_metrics(base_url, timeout, retries, retry_delay)
        results["checks"].append(metrics_result)
    
    # Verify performance
    if verify_performance:
        performance_result = _verify_performance(base_url, service_name, timeout, retries, retry_delay)
        results["checks"].append(performance_result)
    
    # Run custom checks
    if custom_checks:
        for i, check_func in enumerate(custom_checks):
            try:
                success, message = check_func()
                results["checks"].append({
                    "type": VerificationType.CUSTOM.value,
                    "name": f"custom_check_{i}",
                    "status": VerificationStatus.PASSED.value if success else VerificationStatus.FAILED.value,
                    "message": message,
                })
            except Exception as e:
                results["checks"].append({
                    "type": VerificationType.CUSTOM.value,
                    "name": f"custom_check_{i}",
                    "status": VerificationStatus.FAILED.value,
                    "message": f"Check failed with error: {str(e)}",
                    "error": str(e),
                })
    
    # Determine overall status
    if any(check["status"] == VerificationStatus.FAILED.value for check in results["checks"]):
        results["overall_status"] = VerificationStatus.FAILED.value
        trigger_alert(
            f"Deployment verification failed for {service_name}",
            f"One or more verification checks failed for {service_name} at {base_url}",
            AlertSeverity.ERROR,
            {"service": service_name, "url": base_url},
        )
    elif any(check["status"] == VerificationStatus.WARNING.value for check in results["checks"]):
        results["overall_status"] = VerificationStatus.WARNING.value
        trigger_alert(
            f"Deployment verification warning for {service_name}",
            f"One or more verification checks issued warnings for {service_name} at {base_url}",
            AlertSeverity.WARNING,
            {"service": service_name, "url": base_url},
        )
    elif all(check["status"] == VerificationStatus.PASSED.value for check in results["checks"]):
        results["overall_status"] = VerificationStatus.PASSED.value
    
    success = results["overall_status"] in [VerificationStatus.PASSED.value, VerificationStatus.WARNING.value]
    
    # Record verification metrics
    capture_metric(
        "deployment_verification_result",
        1.0 if success else 0.0,
        {
            "service": service_name,
            "status": results["overall_status"],
        },
    )
    
    logger.info(f"Deployment verification complete: {results['overall_status']}")
    
    return success, results


def _verify_health(
    base_url: str,
    timeout: int,
    retries: int,
    retry_delay: int,
) -> Dict[str, Any]:
    """
    Verify service health by checking the health endpoint.
    
    Args:
        base_url: The base URL of the service
        timeout: Timeout in seconds for the health check
        retries: Number of retries for the health check
        retry_delay: Delay in seconds between retries
        
    Returns:
        A dictionary with the health check result
    """
    logger.info(f"Verifying health at {base_url}/health")
    
    for attempt in range(retries):
        try:
            response = requests.get(f"{base_url}/health", timeout=timeout)
            
            if response.status_code == 200:
                health_data = response.json()
                
                if health_data.get("status") == "healthy":
                    return {
                        "type": VerificationType.HEALTH.value,
                        "name": "health_check",
                        "status": VerificationStatus.PASSED.value,
                        "message": "Health check passed",
                        "data": health_data,
                    }
                else:
                    unhealthy_components = []
                    for component, info in health_data.get("components", {}).items():
                        if info.get("status") != "healthy":
                            unhealthy_components.append(component)
                    
                    return {
                        "type": VerificationType.HEALTH.value,
                        "name": "health_check",
                        "status": VerificationStatus.FAILED.value,
                        "message": f"Service is not healthy: {', '.join(unhealthy_components)}",
                        "data": health_data,
                    }
            else:
                if attempt < retries - 1:
                    logger.warning(f"Health check failed with status {response.status_code}, retrying in {retry_delay}s")
                    time.sleep(retry_delay)
                    continue
                
                return {
                    "type": VerificationType.HEALTH.value,
                    "name": "health_check",
                    "status": VerificationStatus.FAILED.value,
                    "message": f"Health check returned status code {response.status_code}",
                    "data": {"status_code": response.status_code},
                }
        except requests.RequestException as e:
            if attempt < retries - 1:
                logger.warning(f"Health check failed with error: {str(e)}, retrying in {retry_delay}s")
                time.sleep(retry_delay)
                continue
            
            return {
                "type": VerificationType.HEALTH.value,
                "name": "health_check",
                "status": VerificationStatus.FAILED.value,
                "message": f"Health check failed with error: {str(e)}",
                "error": str(e),
            }
    
    return {
        "type": VerificationType.HEALTH.value,
        "name": "health_check",
        "status": VerificationStatus.FAILED.value,
        "message": f"Health check failed after {retries} attempts",
    }


def _verify_metrics(
    base_url: str,
    timeout: int,
    retries: int,
    retry_delay: int,
) -> Dict[str, Any]:
    """
    Verify service metrics by checking the metrics endpoint.
    
    Args:
        base_url: The base URL of the service
        timeout: Timeout in seconds for the metrics check
        retries: Number of retries for the metrics check
        retry_delay: Delay in seconds between retries
        
    Returns:
        A dictionary with the metrics check result
    """
    logger.info(f"Verifying metrics at {base_url}/metrics")
    
    for attempt in range(retries):
        try:
            response = requests.get(f"{base_url}/metrics", timeout=timeout)
            
            if response.status_code == 200:
                try:
                    metrics_data = response.json()
                    
                    if metrics_data:
                        return {
                            "type": VerificationType.METRICS.value,
                            "name": "metrics_check",
                            "status": VerificationStatus.PASSED.value,
                            "message": "Metrics check passed",
                            "data": {"metric_count": len(metrics_data)},
                        }
                    else:
                        return {
                            "type": VerificationType.METRICS.value,
                            "name": "metrics_check",
                            "status": VerificationStatus.WARNING.value,
                            "message": "Metrics endpoint returned empty data",
                            "data": {},
                        }
                except json.JSONDecodeError:
                    # Prometheus format metrics are not JSON
                    if response.text:
                        metric_count = len(response.text.strip().split("\n"))
                        
                        return {
                            "type": VerificationType.METRICS.value,
                            "name": "metrics_check",
                            "status": VerificationStatus.PASSED.value,
                            "message": "Prometheus metrics check passed",
                            "data": {"metric_count": metric_count},
                        }
                    else:
                        return {
                            "type": VerificationType.METRICS.value,
                            "name": "metrics_check",
                            "status": VerificationStatus.WARNING.value,
                            "message": "Metrics endpoint returned empty data",
                            "data": {},
                        }
            else:
                if attempt < retries - 1:
                    logger.warning(f"Metrics check failed with status {response.status_code}, retrying in {retry_delay}s")
                    time.sleep(retry_delay)
                    continue
                
                return {
                    "type": VerificationType.METRICS.value,
                    "name": "metrics_check",
                    "status": VerificationStatus.FAILED.value,
                    "message": f"Metrics check returned status code {response.status_code}",
                    "data": {"status_code": response.status_code},
                }
        except requests.RequestException as e:
            if attempt < retries - 1:
                logger.warning(f"Metrics check failed with error: {str(e)}, retrying in {retry_delay}s")
                time.sleep(retry_delay)
                continue
            
            return {
                "type": VerificationType.METRICS.value,
                "name": "metrics_check",
                "status": VerificationStatus.FAILED.value,
                "message": f"Metrics check failed with error: {str(e)}",
                "error": str(e),
            }
    
    return {
        "type": VerificationType.METRICS.value,
        "name": "metrics_check",
        "status": VerificationStatus.FAILED.value,
        "message": f"Metrics check failed after {retries} attempts",
    }


def _verify_performance(
    base_url: str,
    service_name: str,
    timeout: int,
    retries: int,
    retry_delay: int,
) -> Dict[str, Any]:
    """
    Verify service performance by checking response times.
    
    Args:
        base_url: The base URL of the service
        service_name: The name of the service
        timeout: Timeout in seconds for the performance check
        retries: Number of retries for the performance check
        retry_delay: Delay in seconds between retries
        
    Returns:
        A dictionary with the performance check result
    """
    logger.info(f"Verifying performance at {base_url}/health")
    
    response_times = []
    
    for attempt in range(retries):
        try:
            start_time = time.time()
            response = requests.get(f"{base_url}/health", timeout=timeout)
            end_time = time.time()
            
            response_time = end_time - start_time
            response_times.append(response_time)
            
            if response.status_code == 200:
                continue
            else:
                if attempt < retries - 1:
                    logger.warning(f"Performance check failed with status {response.status_code}, retrying in {retry_delay}s")
                    time.sleep(retry_delay)
                    continue
                
                return {
                    "type": VerificationType.PERFORMANCE.value,
                    "name": "performance_check",
                    "status": VerificationStatus.FAILED.value,
                    "message": f"Performance check returned status code {response.status_code}",
                    "data": {"status_code": response.status_code},
                }
        except requests.RequestException as e:
            if attempt < retries - 1:
                logger.warning(f"Performance check failed with error: {str(e)}, retrying in {retry_delay}s")
                time.sleep(retry_delay)
                continue
            
            return {
                "type": VerificationType.PERFORMANCE.value,
                "name": "performance_check",
                "status": VerificationStatus.FAILED.value,
                "message": f"Performance check failed with error: {str(e)}",
                "error": str(e),
            }
    
    # Calculate average response time
    avg_response_time = sum(response_times) / len(response_times)
    
    # Record performance metrics
    capture_metric(
        "deployment_verification_response_time",
        avg_response_time,
        {"service": service_name},
    )
    
    # Get historical performance baseline
    baseline = _get_performance_baseline(service_name)
    
    if baseline is None:
        # No baseline available, use current performance as baseline
        _update_performance_baseline(service_name, avg_response_time)
        
        return {
            "type": VerificationType.PERFORMANCE.value,
            "name": "performance_check",
            "status": VerificationStatus.PASSED.value,
            "message": "Performance check passed (no baseline available)",
            "data": {
                "response_times": response_times,
                "avg_response_time": avg_response_time,
            },
        }
    
    # Compare with baseline
    if avg_response_time > baseline * 1.5:
        # More than 50% slower
        return {
            "type": VerificationType.PERFORMANCE.value,
            "name": "performance_check",
            "status": VerificationStatus.FAILED.value,
            "message": f"Performance degraded by more than 50% (baseline: {baseline:.3f}s, current: {avg_response_time:.3f}s)",
            "data": {
                "response_times": response_times,
                "avg_response_time": avg_response_time,
                "baseline": baseline,
                "percent_change": ((avg_response_time - baseline) / baseline) * 100,
            },
        }
    elif avg_response_time > baseline * 1.2:
        # More than 20% slower
        return {
            "type": VerificationType.PERFORMANCE.value,
            "name": "performance_check",
            "status": VerificationStatus.WARNING.value,
            "message": f"Performance degraded by more than 20% (baseline: {baseline:.3f}s, current: {avg_response_time:.3f}s)",
            "data": {
                "response_times": response_times,
                "avg_response_time": avg_response_time,
                "baseline": baseline,
                "percent_change": ((avg_response_time - baseline) / baseline) * 100,
            },
        }
    else:
        # Performance is acceptable
        return {
            "type": VerificationType.PERFORMANCE.value,
            "name": "performance_check",
            "status": VerificationStatus.PASSED.value,
            "message": f"Performance check passed (baseline: {baseline:.3f}s, current: {avg_response_time:.3f}s)",
            "data": {
                "response_times": response_times,
                "avg_response_time": avg_response_time,
                "baseline": baseline,
                "percent_change": ((avg_response_time - baseline) / baseline) * 100,
            },
        }


# Simple in-memory storage for performance baselines
_performance_baselines = {}


def _get_performance_baseline(service_name: str) -> Optional[float]:
    """
    Get the performance baseline for a service.
    
    Args:
        service_name: The name of the service
        
    Returns:
        The performance baseline, or None if not available
    """
    return _performance_baselines.get(service_name)


def _update_performance_baseline(service_name: str, baseline: float) -> None:
    """
    Update the performance baseline for a service.
    
    Args:
        service_name: The name of the service
        baseline: The performance baseline
    """
    _performance_baselines[service_name] = baseline


class CanaryDeploymentMonitor:
    """
    Monitor for canary deployments, comparing metrics between canary and production.
    """
    
    def __init__(
        self,
        service_name: str,
        canary_url: str,
        production_url: str,
        threshold: float = 1.2,
        check_interval: int = 60,
        window_size: int = 5,
    ):
        """
        Initialize the canary deployment monitor.
        
        Args:
            service_name: The name of the service
            canary_url: The URL of the canary deployment
            production_url: The URL of the production deployment
            threshold: The threshold for performance comparison (e.g., 1.2 means 20% degradation is allowed)
            check_interval: The interval in seconds between checks
            window_size: The number of checks to include in the rolling window
        """
        self.service_name = service_name
        self.canary_url = canary_url
        self.production_url = production_url
        self.threshold = threshold
        self.check_interval = check_interval
        self.window_size = window_size
        
        self.canary_metrics = []
        self.production_metrics = []
        self.status = "running"
        self.thread = None
    
    def start(self) -> None:
        """Start monitoring the canary deployment."""
        if self.thread and self.thread.is_alive():
            logger.warning("Canary deployment monitor is already running")
            return
        
        self.status = "running"
        self.thread = threading.Thread(target=self._monitor_loop)
        self.thread.daemon = True
        self.thread.start()
        
        logger.info(f"Started canary deployment monitor for {self.service_name}")
    
    def stop(self) -> None:
        """Stop monitoring the canary deployment."""
        self.status = "stopped"
        if self.thread:
            self.thread.join(timeout=5)
        
        logger.info(f"Stopped canary deployment monitor for {self.service_name}")
    
    def get_results(self) -> Dict[str, Any]:
        """Get the current monitoring results."""
        canary_avg = sum(m["response_time"] for m in self.canary_metrics) / len(self.canary_metrics) if self.canary_metrics else 0
        prod_avg = sum(m["response_time"] for m in self.production_metrics) / len(self.production_metrics) if self.production_metrics else 0
        
        ratio = canary_avg / prod_avg if prod_avg > 0 else 0
        
        return {
            "service": self.service_name,
            "canary_url": self.canary_url,
            "production_url": self.production_url,
            "status": self.status,
            "threshold": self.threshold,
            "canary_avg_response_time": canary_avg,
            "production_avg_response_time": prod_avg,
            "ratio": ratio,
            "pass": ratio <= self.threshold,
            "canary_metrics": self.canary_metrics[-self.window_size:],
            "production_metrics": self.production_metrics[-self.window_size:],
        }
    
    def should_rollback(self) -> bool:
        """Check if the canary deployment should be rolled back."""
        if len(self.canary_metrics) < self.window_size or len(self.production_metrics) < self.window_size:
            # Not enough data yet
            return False
        
        results = self.get_results()
        return not results["pass"]
    
    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        logger.info(f"Starting canary monitoring loop for {self.service_name}")
        
        while self.status == "running":
            try:
                # Check canary
                canary_start = time.time()
                canary_response = requests.get(f"{self.canary_url}/health", timeout=10)
                canary_time = time.time() - canary_start
                
                # Check production
                prod_start = time.time()
                prod_response = requests.get(f"{self.production_url}/health", timeout=10)
                prod_time = time.time() - prod_start
                
                # Store metrics
                self.canary_metrics.append({
                    "timestamp": time.time(),
                    "response_time": canary_time,
                    "status_code": canary_response.status_code,
                })
                
                self.production_metrics.append({
                    "timestamp": time.time(),
                    "response_time": prod_time,
                    "status_code": prod_response.status_code,
                })
                
                # Trim metrics to window size
                if len(self.canary_metrics) > self.window_size * 2:
                    self.canary_metrics = self.canary_metrics[-self.window_size:]
                
                if len(self.production_metrics) > self.window_size * 2:
                    self.production_metrics = self.production_metrics[-self.window_size:]
                
                # Check if we should alert
                if self.should_rollback():
                    logger.warning(f"Canary deployment for {self.service_name} is degraded and should be rolled back")
                    trigger_alert(
                        f"Canary deployment degraded for {self.service_name}",
                        f"Canary deployment for {self.service_name} is showing performance degradation",
                        AlertSeverity.WARNING,
                        {"service": self.service_name, "canary_url": self.canary_url},
                    )
            
            except Exception as e:
                logger.error(f"Error in canary monitoring loop: {str(e)}")
            
            time.sleep(self.check_interval)


def monitor_canary_deployment(
    service_name: str,
    canary_url: str,
    production_url: str,
    threshold: float = 1.2,
    check_interval: int = 60,
    window_size: int = 5,
) -> CanaryDeploymentMonitor:
    """
    Monitor a canary deployment, comparing metrics between canary and production.
    
    Args:
        service_name: The name of the service
        canary_url: The URL of the canary deployment
        production_url: The URL of the production deployment
        threshold: The threshold for performance comparison (e.g., 1.2 means 20% degradation is allowed)
        check_interval: The interval in seconds between checks
        window_size: The number of checks to include in the rolling window
        
    Returns:
        A CanaryDeploymentMonitor instance
    """
    monitor = CanaryDeploymentMonitor(
        service_name=service_name,
        canary_url=canary_url,
        production_url=production_url,
        threshold=threshold,
        check_interval=check_interval,
        window_size=window_size,
    )
    
    monitor.start()
    
    return monitor
