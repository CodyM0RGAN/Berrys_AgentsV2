"""
Performance testing utilities for Berrys_AgentsV2.

This module provides utilities for performance testing, including:
- Performance benchmarking
- Load testing
- Resource utilization analysis
- Performance regression detection
"""

import time
import statistics
import functools
import asyncio
import threading
import multiprocessing
from typing import Dict, List, Any, Optional, Callable, Union, Tuple, TypeVar, Generic
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

import numpy as np
import requests
import aiohttp
from tqdm import tqdm

# Try to import the monitoring system
try:
    from shared.utils.src.monitoring.metrics import (
        increment_counter, gauge, histogram, 
        configure_metrics, MetricsBackend
    )
    HAS_MONITORING = True
except ImportError:
    HAS_MONITORING = False
    
    # Define dummy metric functions for when the monitoring system is not available
    def increment_counter(name, value=1, tags=None):
        pass
        
    def gauge(name, value, tags=None):
        pass
        
    def histogram(name, value, tags=None):
        pass
        
    class MetricsBackend:
        PROMETHEUS = "prometheus"
        CONSOLE = "console"
        
    def configure_metrics(**kwargs):
        pass


class PerformanceMeasurement:
    """
    Measurement of a performance metric.
    
    This class stores the measured value, timestamp, and metadata
    for a performance metric.
    """
    
    def __init__(
        self,
        value: float,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a performance measurement.
        
        Args:
            value: Measured value.
            timestamp: Timestamp of the measurement.
            metadata: Additional metadata about the measurement.
        """
        self.value = value
        self.timestamp = timestamp or datetime.now()
        self.metadata = metadata or {}
        
    def __repr__(self) -> str:
        """
        Get string representation of the measurement.
        
        Returns:
            String representation.
        """
        return f"PerformanceMeasurement(value={self.value}, timestamp={self.timestamp})"
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the measurement to a dictionary.
        
        Returns:
            Dictionary representation of the measurement.
        """
        return {
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PerformanceMeasurement":
        """
        Create a measurement from a dictionary.
        
        Args:
            data: Dictionary representation of a measurement.
            
        Returns:
            Performance measurement.
        """
        return cls(
            value=data["value"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {})
        )


class PerformanceMetric:
    """
    Performance metric.
    
    This class represents a performance metric with multiple measurements
    and provides methods for analyzing the measurements.
    """
    
    def __init__(
        self,
        name: str,
        unit: str,
        description: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None
    ):
        """
        Initialize a performance metric.
        
        Args:
            name: Name of the metric.
            unit: Unit of the metric.
            description: Description of the metric.
            tags: Tags for the metric.
        """
        self.name = name
        self.unit = unit
        self.description = description
        self.tags = tags or {}
        self.measurements: List[PerformanceMeasurement] = []
        
    def add_measurement(
        self,
        value: float,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PerformanceMeasurement:
        """
        Add a measurement to the metric.
        
        Args:
            value: Measured value.
            timestamp: Timestamp of the measurement.
            metadata: Additional metadata about the measurement.
            
        Returns:
            The added measurement.
        """
        measurement = PerformanceMeasurement(
            value=value,
            timestamp=timestamp,
            metadata=metadata
        )
        
        self.measurements.append(measurement)
        
        # Report the measurement to the monitoring system
        if HAS_MONITORING:
            histogram(
                f"performance.{self.name}",
                value,
                {**self.tags, **(metadata or {})}
            )
            
        return measurement
        
    def clear_measurements(self) -> None:
        """Clear all measurements from the metric."""
        self.measurements = []
        
    def get_values(self) -> List[float]:
        """
        Get all measured values.
        
        Returns:
            List of measured values.
        """
        return [m.value for m in self.measurements]
        
    def get_statistics(self) -> Dict[str, float]:
        """
        Get statistics for the metric.
        
        Returns:
            Dictionary of statistics.
        """
        values = self.get_values()
        
        if not values:
            return {
                "count": 0
            }
            
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "stdev": statistics.stdev(values) if len(values) > 1 else 0,
            "percentile_90": np.percentile(values, 90),
            "percentile_95": np.percentile(values, 95),
            "percentile_99": np.percentile(values, 99)
        }
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the metric to a dictionary.
        
        Returns:
            Dictionary representation of the metric.
        """
        return {
            "name": self.name,
            "unit": self.unit,
            "description": self.description,
            "tags": self.tags,
            "measurements": [m.to_dict() for m in self.measurements],
            "statistics": self.get_statistics()
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PerformanceMetric":
        """
        Create a metric from a dictionary.
        
        Args:
            data: Dictionary representation of a metric.
            
        Returns:
            Performance metric.
        """
        metric = cls(
            name=data["name"],
            unit=data["unit"],
            description=data.get("description"),
            tags=data.get("tags", {})
        )
        
        for measurement_data in data.get("measurements", []):
            metric.measurements.append(
                PerformanceMeasurement.from_dict(measurement_data)
            )
            
        return metric


class PerformanceBenchmark:
    """
    Performance benchmark.
    
    This class provides methods for running benchmarks and collecting
    performance metrics.
    """
    
    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None
    ):
        """
        Initialize a performance benchmark.
        
        Args:
            name: Name of the benchmark.
            description: Description of the benchmark.
            tags: Tags for the benchmark.
        """
        self.name = name
        self.description = description
        self.tags = tags or {}
        self.metrics: Dict[str, PerformanceMetric] = {}
        
    def add_metric(
        self,
        name: str,
        unit: str,
        description: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> PerformanceMetric:
        """
        Add a metric to the benchmark.
        
        Args:
            name: Name of the metric.
            unit: Unit of the metric.
            description: Description of the metric.
            tags: Tags for the metric.
            
        Returns:
            The added metric.
        """
        metric = PerformanceMetric(
            name=name,
            unit=unit,
            description=description,
            tags={**self.tags, **(tags or {})}
        )
        
        self.metrics[name] = metric
        return metric
        
    def get_metric(self, name: str) -> PerformanceMetric:
        """
        Get a metric by name.
        
        Args:
            name: Name of the metric.
            
        Returns:
            The metric.
            
        Raises:
            KeyError: If the metric is not found.
        """
        if name not in self.metrics:
            raise KeyError(f"Metric {name} not found in benchmark {self.name}")
            
        return self.metrics[name]
        
    def measure(
        self,
        metric_name: str,
        value: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PerformanceMeasurement:
        """
        Add a measurement to a metric.
        
        Args:
            metric_name: Name of the metric.
            value: Measured value.
            metadata: Additional metadata about the measurement.
            
        Returns:
            The added measurement.
            
        Raises:
            KeyError: If the metric is not found.
        """
        return self.get_metric(metric_name).add_measurement(
            value=value,
            metadata=metadata
        )
        
    def clear_metrics(self) -> None:
        """Clear all metrics from the benchmark."""
        for metric in self.metrics.values():
            metric.clear_measurements()
            
    def run(
        self,
        func: Callable,
        iterations: int = 1,
        warmup: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run a benchmark.
        
        Args:
            func: Function to benchmark.
            iterations: Number of iterations to run.
            warmup: Number of warmup iterations to run.
            metadata: Additional metadata about the benchmark run.
            
        Returns:
            Dictionary of benchmark results.
        """
        # Create a duration metric if it doesn't exist
        if "duration" not in self.metrics:
            self.add_metric(
                name="duration",
                unit="ms",
                description="Duration of the function execution"
            )
            
        # Run warmup iterations
        for _ in range(warmup):
            func()
            
        # Run benchmark iterations
        results = []
        for i in range(iterations):
            start_time = time.time()
            result = func()
            end_time = time.time()
            
            duration_ms = (end_time - start_time) * 1000
            measurement = self.measure(
                metric_name="duration",
                value=duration_ms,
                metadata={**(metadata or {}), "iteration": i}
            )
            
            results.append(result)
            
        # Get statistics
        stats = self.get_metric("duration").get_statistics()
        
        return {
            "benchmark": self.name,
            "iterations": iterations,
            "warmup": warmup,
            "statistics": stats,
            "results": results
        }
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the benchmark to a dictionary.
        
        Returns:
            Dictionary representation of the benchmark.
        """
        return {
            "name": self.name,
            "description": self.description,
            "tags": self.tags,
            "metrics": {
                name: metric.to_dict()
                for name, metric in self.metrics.items()
            }
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PerformanceBenchmark":
        """
        Create a benchmark from a dictionary.
        
        Args:
            data: Dictionary representation of a benchmark.
            
        Returns:
            Performance benchmark.
        """
        benchmark = cls(
            name=data["name"],
            description=data.get("description"),
            tags=data.get("tags", {})
        )
        
        for name, metric_data in data.get("metrics", {}).items():
            benchmark.metrics[name] = PerformanceMetric.from_dict(metric_data)
            
        return benchmark


T = TypeVar("T")


def benchmark(
    iterations: int = 1,
    warmup: int = 0,
    name: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[Dict[str, str]] = None
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for benchmarking a function.
    
    Args:
        iterations: Number of iterations to run.
        warmup: Number of warmup iterations to run.
        name: Name of the benchmark. Defaults to the function name.
        description: Description of the benchmark.
        tags: Tags for the benchmark.
        
    Returns:
        Decorated function.
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            nonlocal name
            name = name or func.__name__
            
            benchmark = PerformanceBenchmark(
                name=name,
                description=description,
                tags=tags
            )
            
            # Create a duration metric
            benchmark.add_metric(
                name="duration",
                unit="ms",
                description="Duration of the function execution"
            )
            
            # Run warmup iterations
            for _ in range(warmup):
                func(*args, **kwargs)
                
            # Run benchmark iterations
            results = None
            for i in range(iterations):
                start_time = time.time()
                results = func(*args, **kwargs)
                end_time = time.time()
                
                duration_ms = (end_time - start_time) * 1000
                benchmark.measure(
                    metric_name="duration",
                    value=duration_ms,
                    metadata={"iteration": i}
                )
                
            # Get statistics
            stats = benchmark.get_metric("duration").get_statistics()
            
            print(f"Benchmark results for {name}:")
            print(f"  Iterations: {iterations}")
            print(f"  Warmup: {warmup}")
            print(f"  Mean: {stats['mean']:.2f} ms")
            print(f"  Median: {stats['median']:.2f} ms")
            print(f"  Min: {stats['min']:.2f} ms")
            print(f"  Max: {stats['max']:.2f} ms")
            print(f"  Stdev: {stats.get('stdev', 0):.2f} ms")
            
            return results
            
        return wrapper
        
    return decorator


class LoadTest:
    """
    Load test for a service.
    
    This class provides methods for running load tests on a service
    and collecting performance metrics.
    """
    
    def __init__(
        self,
        name: str,
        url: str,
        description: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        """
        Initialize a load test.
        
        Args:
            name: Name of the load test.
            url: URL of the service to test.
            description: Description of the load test.
            tags: Tags for the load test.
            headers: Headers to include in requests.
        """
        self.name = name
        self.url = url
        self.description = description
        self.tags = tags or {}
        self.headers = headers or {}
        self.benchmark = PerformanceBenchmark(
            name=name,
            description=description,
            tags=tags
        )
        
        # Create metrics
        self.benchmark.add_metric(
            name="response_time",
            unit="ms",
            description="Response time of the service"
        )
        
        self.benchmark.add_metric(
            name="requests_per_second",
            unit="rps",
            description="Number of requests per second"
        )
        
        self.benchmark.add_metric(
            name="success_rate",
            unit="%",
            description="Percentage of successful requests"
        )
        
    def run_test(
        self,
        endpoint: str,
        method: str = "GET",
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, str]] = None,
        duration: Optional[int] = None,
        requests: Optional[int] = None,
        concurrency: int = 1,
        ramp_up: int = 0,
        timeout: int = 30,
        quiet: bool = False
    ) -> Dict[str, Any]:
        """
        Run a load test.
        
        Args:
            endpoint: Endpoint to test.
            method: HTTP method to use (default: "GET").
            data: Data to include in the request body.
            params: Query parameters to include in the request.
            duration: Duration of the test in seconds.
            requests: Number of requests to send.
            concurrency: Number of concurrent requests.
            ramp_up: Ramp-up time in seconds.
            timeout: Timeout for requests in seconds.
            quiet: Whether to suppress progress output.
            
        Returns:
            Dictionary of load test results.
            
        Note:
            Either duration or requests must be specified.
        """
        if duration is None and requests is None:
            raise ValueError("Either duration or requests must be specified")
            
        url = f"{self.url}{endpoint}"
        
        # Create a session for connection pooling
        session = requests.Session()
        
        # Set up metrics
        response_times = []
        success_count = 0
        error_count = 0
        request_count = 0
        
        # Set up threads
        executor = ThreadPoolExecutor(max_workers=concurrency)
        start_time = time.time()
        
        # Define the request function
        def make_request():
            try:
                req_start_time = time.time()
                
                # Make the request
                if method.upper() == "GET":
                    response = session.get(
                        url,
                        params=params,
                        headers=self.headers,
                        timeout=timeout
                    )
                elif method.upper() == "POST":
                    response = session.post(
                        url,
                        json=data,
                        params=params,
                        headers=self.headers,
                        timeout=timeout
                    )
                elif method.upper() == "PUT":
                    response = session.put(
                        url,
                        json=data,
                        params=params,
                        headers=self.headers,
                        timeout=timeout
                    )
                elif method.upper() == "DELETE":
                    response = session.delete(
                        url,
                        params=params,
                        headers=self.headers,
                        timeout=timeout
                    )
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                    
                req_end_time = time.time()
                
                # Calculate response time
                response_time = (req_end_time - req_start_time) * 1000
                
                # Record metrics
                response_times.append(response_time)
                
                # Check if the request was successful
                if response.status_code < 400:
                    return True, response_time
                else:
                    return False, response_time
                    
            except Exception as e:
                # Record error
                return False, None
                
        # Run the test
        futures = []
        
        if duration is not None:
            # Run for a fixed duration
            end_time = start_time + duration
            
            # Create a progress bar if not quiet
            if not quiet:
                with tqdm(total=duration, desc="Running load test") as pbar:
                    while time.time() < end_time:
                        # Submit a request
                        future = executor.submit(make_request)
                        futures.append(future)
                        request_count += 1
                        
                        # Update the progress bar
                        elapsed = min(time.time() - start_time, duration)
                        pbar.update(elapsed - pbar.n)
                        
                        # Sleep to control the request rate during ramp-up
                        if ramp_up > 0 and time.time() - start_time < ramp_up:
                            sleep_time = ramp_up / (concurrency * 10)
                            time.sleep(sleep_time)
            else:
                # Run without a progress bar
                while time.time() < end_time:
                    # Submit a request
                    future = executor.submit(make_request)
                    futures.append(future)
                    request_count += 1
                    
                    # Sleep to control the request rate during ramp-up
                    if ramp_up > 0 and time.time() - start_time < ramp_up:
                        sleep_time = ramp_up / (concurrency * 10)
                        time.sleep(sleep_time)
        else:
            # Run a fixed number of requests
            if not quiet:
                with tqdm(total=requests, desc="Running load test") as pbar:
                    for i in range(requests):
                        # Submit a request
                        future = executor.submit(make_request)
                        futures.append(future)
                        request_count += 1
                        
                        # Update the progress bar
                        pbar.update(1)
                        
                        # Sleep to control the request rate during ramp-up
                        if ramp_up > 0 and time.time() - start_time < ramp_up:
                            sleep_time = ramp_up / requests
                            time.sleep(sleep_time)
            else:
                # Run without a progress bar
                for i in range(requests):
                    # Submit a request
                    future = executor.submit(make_request)
                    futures.append(future)
                    request_count += 1
                    
                    # Sleep to control the request rate during ramp-up
                    if ramp_up > 0 and time.time() - start_time < ramp_up:
                        sleep_time = ramp_up / requests
                        time.sleep(sleep_time)
                        
        # Wait for all requests to complete
        for future in futures:
            success, response_time = future.result()
            if success:
                success_count += 1
            else:
                error_count += 1
                
        # Calculate metrics
        end_time = time.time()
        total_time = end_time - start_time
        
        # Record metrics
        if response_times:
            for response_time in response_times:
                self.benchmark.measure(
                    metric_name="response_time",
                    value=response_time
                )
                
        self.benchmark.measure(
            metric_name="requests_per_second",
            value=request_count / total_time
        )
        
        self.benchmark.measure(
            metric_name="success_rate",
            value=(success_count / request_count) * 100 if request_count > 0 else 0
        )
        
        # Return results
        return {
            "load_test": self.name,
            "url": url,
            "method": method,
            "duration": total_time,
            "requests": request_count,
            "concurrency": concurrency,
            "success_count": success_count,
            "error_count": error_count,
            "success_rate": (success_count / request_count) * 100 if request_count > 0 else 0,
            "requests_per_second": request_count / total_time,
            "response_time": {
                "min": min(response_times) if response_times else None,
                "max": max(response_times) if response_times else None,
                "mean": statistics.mean(response_times) if response_times else None,
                "median": statistics.median(response_times) if response_times else None,
                "percentile_90": np.percentile(response_times, 90) if response_times else None,
                "percentile_95": np.percentile(response_times, 95) if response_times else None,
                "percentile_99": np.percentile(response_times, 99) if response_times else None
            }
        }
        
    async def run_async_test(
        self,
        endpoint: str,
        method: str = "GET",
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, str]] = None,
        duration: Optional[int] = None,
        requests: Optional[int] = None,
        concurrency: int = 1,
        ramp_up: int = 0,
        timeout: int = 30,
        quiet: bool = False
    ) -> Dict[str, Any]:
        """
        Run an asynchronous load test.
        
        Args:
            endpoint: Endpoint to test.
            method: HTTP method to use (default: "GET").
            data: Data to include in the request body.
            params: Query parameters to include in the request.
            duration: Duration of the test in seconds.
            requests: Number of requests to send.
            concurrency: Number of concurrent requests.
            ramp_up: Ramp-up time in seconds.
            timeout: Timeout for requests in seconds.
            quiet: Whether to suppress progress output.
            
        Returns:
            Dictionary of load test results.
            
        Note:
            Either duration or requests must be specified.
        """
        if duration is None and requests is None:
            raise ValueError("Either duration or requests must be specified")
            
        url = f"{self.url}{endpoint}"
        
        # Set up metrics
        response_times = []
        success_count = 0
        error_count = 0
        request_count = 0
        
        # Set up async session
        async with aiohttp.ClientSession() as session:
            # Define the request function
            async def make_request():
                try:
                    req_start_time = time.time()
                    
                    # Make the request
                    if method.upper() == "GET":
                        async with session.get(
                            url,
                            params=params,
                            headers=self.headers,
                            timeout=timeout
                        ) as response:
                            await response.text()
                    elif method.upper() == "POST":
                        async with session.post(
                            url,
                            json=data,
                            params=params,
                            headers=self.headers,
                            timeout=timeout
                        ) as response:
                            await response.text()
                    elif method.upper() == "PUT":
                        async with session.put(
                            url,
                            json=data,
                            params=params,
                            headers=self.headers,
                            timeout=timeout
                        ) as response:
                            await response.text()
                    elif method.upper() == "DELETE":
                        async with session.delete(
                            url,
                            params=params,
                            headers=self.headers,
                            timeout=timeout
                        ) as response:
                            await response.text()
                    else:
                        raise ValueError(f"Unsupported HTTP method: {method}")
                        
                    req_end_time = time.time()
                    
                    # Calculate response time
                    response_time = (req_end_time - req_start_time) * 1000
                    
                    # Record metrics
                    response_times.append(response_time)
                    
                    # Check if the request was successful
                    if response.status < 400:
                        return True, response_time
                    else:
                        return False, response_time
                        
                except Exception as e:
                    # Record error
                    return False, None
                    
            # Run the test
            start_time = time.time()
            tasks = []
            
            if duration is not None:
                # Run for a fixed duration
                end_time = start_time + duration
                
                # Create a semaphore to limit concurrency
                semaphore = asyncio.Semaphore(concurrency)
                
                # Create tasks
                async def worker():
                    nonlocal request_count
                    async with semaphore:
                        request_count += 1
                        return await make_request()
                        
                # Create a progress bar if not quiet
                if not quiet:
                    with tqdm(total=duration, desc="Running load test") as pbar:
                        while time.time() < end_time:
                            # Create a task
                            task = asyncio.create_task(worker())
                            tasks.append(task)
                            
                            # Update the progress bar
                            elapsed = min(time.time() - start_time, duration)
                            pbar.update(elapsed - pbar.n)
                            
                            # Sleep to control the request rate during ramp-up
                            if ramp_up > 0 and time.time() - start_time < ramp_up:
                                sleep_time = ramp_up / (concurrency * 10)
                                await asyncio.sleep(sleep_time)
                else:
                    # Run without a progress bar
                    while time.time() < end_time:
                        # Create a task
                        task = asyncio.create_task(worker())
                        tasks.append(task)
                        
                        # Sleep to control the request rate during ramp-up
                        if ramp_up > 0 and time.time() - start_time < ramp_up:
                            sleep_time = ramp_up / (concurrency * 10)
                            await asyncio.sleep(sleep_time)
            else:
                # Run a fixed number of requests
                if not quiet:
                    with tqdm(total=requests, desc="Running load test") as pbar:
                        for i in range(requests):
                            # Create a task
                            task = asyncio.create_task(make_request())
                            tasks.append(task)
                            request_count += 1
                            
                            # Update the progress bar
                            pbar.update(1)
                            
                            # Sleep to control the request rate during ramp-up
                            if ramp_up > 0 and time.time() - start_time < ramp_up:
                                sleep_time = ramp_up / requests
                                await asyncio.sleep(sleep_time)
                else:
                    # Run without a progress bar
                    for i in range(requests):
                        # Create a task
                        task = asyncio.create_task(make_request())
                        tasks.append(task)
                        request_count += 1
                        
                        # Sleep to control the request rate during ramp-up
                        if ramp_up > 0 and time.time() - start_time < ramp_up:
                            sleep_time = ramp_up / requests
                            await asyncio.sleep(sleep_time)
                            
            # Wait for all tasks to complete
            for task in tasks:
                success, response_time = await task
                if success:
                    success_count += 1
                else:
                    error_count += 1
                    
            # Calculate metrics
            end_time = time.time()
            total_time = end_time - start_time
            
            # Record metrics
            if response_times:
                for response_time in response_times:
                    self.benchmark.measure(
                        metric_name="response_time",
                        value=response_time
                    )
                    
            self.benchmark.measure(
                metric_name="requests_per_second",
                value=request_count / total_time
            )
            
            self.benchmark.measure(
                metric_name="success_rate",
                value=(success_count / request_count) * 100 if request_count > 0 else 0
            )
            
            # Return results
            return {
                "load_test": self.name,
                "url": url,
                "method": method,
                "duration": total_time,
                "requests": request_count,
                "concurrency": concurrency,
                "success_count": success_count,
                "error_count": error_count,
                "success_rate": (success_count / request_count) * 100 if request_count > 0 else 0,
                "requests_per_second": request_count / total_time,
                "response_time": {
                    "min": min(response_times) if response_times else None,
                    "max": max(response_times) if response_times else None,
                    "mean": statistics.mean(response_times) if response_times else None,
                    "median": statistics.median(response_times) if response_times else None,
                    "percentile_90": np.percentile(response_times, 90) if response_times else None,
                    "percentile_95": np.percentile(response_times, 95) if response_times else None,
                    "percentile_99": np.percentile(response_times, 99) if response_times else None
                }
            }
