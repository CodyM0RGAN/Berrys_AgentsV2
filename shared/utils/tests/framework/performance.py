"""
Performance testing utilities.

This module provides utilities for performance testing, including timing,
profiling, and benchmarking.
"""

import time
import cProfile
import pstats
import io
import statistics
import functools
import asyncio
from typing import Dict, Any, List, Optional, Callable, TypeVar, Union, Tuple
import matplotlib.pyplot as plt
import numpy as np

T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])


class Timer:
    """
    Timer for measuring execution time.
    
    This class provides a context manager for measuring execution time.
    """
    
    def __init__(self, name: Optional[str] = None):
        """
        Initialize the timer.
        
        Args:
            name: Optional timer name
        """
        self.name = name or "Timer"
        self.start_time = None
        self.end_time = None
        self.elapsed_time = None
    
    def __enter__(self):
        """Start the timer."""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop the timer."""
        self.end_time = time.time()
        self.elapsed_time = self.end_time - self.start_time
        print(f"{self.name}: {self.elapsed_time:.6f} seconds")
    
    @property
    def elapsed(self) -> float:
        """
        Get the elapsed time.
        
        Returns:
            float: Elapsed time in seconds
        """
        if self.elapsed_time is None:
            raise ValueError("Timer has not been run")
        
        return self.elapsed_time


class AsyncTimer:
    """
    Timer for measuring asynchronous execution time.
    
    This class provides a context manager for measuring asynchronous execution time.
    """
    
    def __init__(self, name: Optional[str] = None):
        """
        Initialize the timer.
        
        Args:
            name: Optional timer name
        """
        self.name = name or "AsyncTimer"
        self.start_time = None
        self.end_time = None
        self.elapsed_time = None
    
    async def __aenter__(self):
        """Start the timer."""
        self.start_time = time.time()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Stop the timer."""
        self.end_time = time.time()
        self.elapsed_time = self.end_time - self.start_time
        print(f"{self.name}: {self.elapsed_time:.6f} seconds")
    
    @property
    def elapsed(self) -> float:
        """
        Get the elapsed time.
        
        Returns:
            float: Elapsed time in seconds
        """
        if self.elapsed_time is None:
            raise ValueError("Timer has not been run")
        
        return self.elapsed_time


def timeit(func: F) -> F:
    """
    Decorator for timing function execution.
    
    Args:
        func: Function to time
        
    Returns:
        F: Wrapped function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"{func.__name__}: {elapsed_time:.6f} seconds")
        return result
    
    return wrapper


def async_timeit(func: F) -> F:
    """
    Decorator for timing asynchronous function execution.
    
    Args:
        func: Asynchronous function to time
        
    Returns:
        F: Wrapped function
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"{func.__name__}: {elapsed_time:.6f} seconds")
        return result
    
    return wrapper


class Profiler:
    """
    Profiler for measuring function execution.
    
    This class provides a context manager for profiling function execution.
    """
    
    def __init__(self, name: Optional[str] = None, sort_by: str = "cumulative"):
        """
        Initialize the profiler.
        
        Args:
            name: Optional profiler name
            sort_by: Sort key for profile stats
        """
        self.name = name or "Profiler"
        self.sort_by = sort_by
        self.profiler = None
    
    def __enter__(self):
        """Start the profiler."""
        self.profiler = cProfile.Profile()
        self.profiler.enable()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop the profiler and print stats."""
        self.profiler.disable()
        
        # Print stats
        s = io.StringIO()
        ps = pstats.Stats(self.profiler, stream=s).sort_stats(self.sort_by)
        ps.print_stats()
        print(f"{self.name} Profile:")
        print(s.getvalue())
    
    def get_stats(self) -> pstats.Stats:
        """
        Get profile stats.
        
        Returns:
            pstats.Stats: Profile stats
        """
        if self.profiler is None:
            raise ValueError("Profiler has not been run")
        
        return pstats.Stats(self.profiler)


def profile(func: F) -> F:
    """
    Decorator for profiling function execution.
    
    Args:
        func: Function to profile
        
    Returns:
        F: Wrapped function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        profiler = cProfile.Profile()
        profiler.enable()
        result = func(*args, **kwargs)
        profiler.disable()
        
        # Print stats
        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s).sort_stats("cumulative")
        ps.print_stats()
        print(f"{func.__name__} Profile:")
        print(s.getvalue())
        
        return result
    
    return wrapper


class Benchmark:
    """
    Benchmark for measuring function performance.
    
    This class provides utilities for benchmarking function performance.
    """
    
    def __init__(self, name: Optional[str] = None):
        """
        Initialize the benchmark.
        
        Args:
            name: Optional benchmark name
        """
        self.name = name or "Benchmark"
        self.results = []
    
    def run(self, func: Callable[[], T], iterations: int = 10) -> List[float]:
        """
        Run a benchmark.
        
        Args:
            func: Function to benchmark
            iterations: Number of iterations
            
        Returns:
            List[float]: Execution times
        """
        times = []
        
        for _ in range(iterations):
            start_time = time.time()
            func()
            end_time = time.time()
            elapsed_time = end_time - start_time
            times.append(elapsed_time)
        
        self.results = times
        return times
    
    async def run_async(self, func: Callable[[], Any], iterations: int = 10) -> List[float]:
        """
        Run an asynchronous benchmark.
        
        Args:
            func: Asynchronous function to benchmark
            iterations: Number of iterations
            
        Returns:
            List[float]: Execution times
        """
        times = []
        
        for _ in range(iterations):
            start_time = time.time()
            await func()
            end_time = time.time()
            elapsed_time = end_time - start_time
            times.append(elapsed_time)
        
        self.results = times
        return times
    
    def get_stats(self) -> Dict[str, float]:
        """
        Get benchmark statistics.
        
        Returns:
            Dict[str, float]: Benchmark statistics
        """
        if not self.results:
            raise ValueError("Benchmark has not been run")
        
        return {
            "min": min(self.results),
            "max": max(self.results),
            "mean": statistics.mean(self.results),
            "median": statistics.median(self.results),
            "stdev": statistics.stdev(self.results) if len(self.results) > 1 else 0,
        }
    
    def print_stats(self):
        """Print benchmark statistics."""
        stats = self.get_stats()
        
        print(f"{self.name} Benchmark Statistics:")
        print(f"  Min: {stats['min']:.6f} seconds")
        print(f"  Max: {stats['max']:.6f} seconds")
        print(f"  Mean: {stats['mean']:.6f} seconds")
        print(f"  Median: {stats['median']:.6f} seconds")
        print(f"  Stdev: {stats['stdev']:.6f} seconds")
    
    def plot(self, title: Optional[str] = None, show: bool = True, save_path: Optional[str] = None):
        """
        Plot benchmark results.
        
        Args:
            title: Optional plot title
            show: Whether to show the plot
            save_path: Optional path to save the plot
        """
        if not self.results:
            raise ValueError("Benchmark has not been run")
        
        plt.figure(figsize=(10, 6))
        
        # Plot execution times
        plt.subplot(2, 1, 1)
        plt.plot(self.results, marker='o')
        plt.title(title or f"{self.name} Benchmark Results")
        plt.xlabel("Iteration")
        plt.ylabel("Execution Time (s)")
        plt.grid(True)
        
        # Plot histogram
        plt.subplot(2, 1, 2)
        plt.hist(self.results, bins=10)
        plt.xlabel("Execution Time (s)")
        plt.ylabel("Frequency")
        plt.grid(True)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path)
        
        if show:
            plt.show()


class PerformanceTest:
    """
    Performance test for measuring and comparing function performance.
    
    This class provides utilities for measuring and comparing function performance.
    """
    
    def __init__(self, name: Optional[str] = None):
        """
        Initialize the performance test.
        
        Args:
            name: Optional test name
        """
        self.name = name or "PerformanceTest"
        self.results = {}
    
    def run(
        self,
        funcs: Dict[str, Callable[[], T]],
        iterations: int = 10,
        warmup: int = 1,
    ) -> Dict[str, List[float]]:
        """
        Run a performance test.
        
        Args:
            funcs: Dictionary of functions to test
            iterations: Number of iterations
            warmup: Number of warmup iterations
            
        Returns:
            Dict[str, List[float]]: Execution times by function name
        """
        results = {}
        
        for name, func in funcs.items():
            # Warmup
            for _ in range(warmup):
                func()
            
            # Benchmark
            times = []
            for _ in range(iterations):
                start_time = time.time()
                func()
                end_time = time.time()
                elapsed_time = end_time - start_time
                times.append(elapsed_time)
            
            results[name] = times
        
        self.results = results
        return results
    
    async def run_async(
        self,
        funcs: Dict[str, Callable[[], Any]],
        iterations: int = 10,
        warmup: int = 1,
    ) -> Dict[str, List[float]]:
        """
        Run an asynchronous performance test.
        
        Args:
            funcs: Dictionary of asynchronous functions to test
            iterations: Number of iterations
            warmup: Number of warmup iterations
            
        Returns:
            Dict[str, List[float]]: Execution times by function name
        """
        results = {}
        
        for name, func in funcs.items():
            # Warmup
            for _ in range(warmup):
                await func()
            
            # Benchmark
            times = []
            for _ in range(iterations):
                start_time = time.time()
                await func()
                end_time = time.time()
                elapsed_time = end_time - start_time
                times.append(elapsed_time)
            
            results[name] = times
        
        self.results = results
        return results
    
    def get_stats(self) -> Dict[str, Dict[str, float]]:
        """
        Get performance test statistics.
        
        Returns:
            Dict[str, Dict[str, float]]: Statistics by function name
        """
        if not self.results:
            raise ValueError("Performance test has not been run")
        
        stats = {}
        
        for name, times in self.results.items():
            stats[name] = {
                "min": min(times),
                "max": max(times),
                "mean": statistics.mean(times),
                "median": statistics.median(times),
                "stdev": statistics.stdev(times) if len(times) > 1 else 0,
            }
        
        return stats
    
    def print_stats(self):
        """Print performance test statistics."""
        stats = self.get_stats()
        
        print(f"{self.name} Performance Test Statistics:")
        
        for name, func_stats in stats.items():
            print(f"\n{name}:")
            print(f"  Min: {func_stats['min']:.6f} seconds")
            print(f"  Max: {func_stats['max']:.6f} seconds")
            print(f"  Mean: {func_stats['mean']:.6f} seconds")
            print(f"  Median: {func_stats['median']:.6f} seconds")
            print(f"  Stdev: {func_stats['stdev']:.6f} seconds")
    
    def plot(self, title: Optional[str] = None, show: bool = True, save_path: Optional[str] = None):
        """
        Plot performance test results.
        
        Args:
            title: Optional plot title
            show: Whether to show the plot
            save_path: Optional path to save the plot
        """
        if not self.results:
            raise ValueError("Performance test has not been run")
        
        plt.figure(figsize=(12, 8))
        
        # Plot execution times
        plt.subplot(2, 1, 1)
        
        for name, times in self.results.items():
            plt.plot(times, marker='o', label=name)
        
        plt.title(title or f"{self.name} Performance Test Results")
        plt.xlabel("Iteration")
        plt.ylabel("Execution Time (s)")
        plt.legend()
        plt.grid(True)
        
        # Plot box plot
        plt.subplot(2, 1, 2)
        
        data = [times for times in self.results.values()]
        labels = list(self.results.keys())
        
        plt.boxplot(data, labels=labels)
        plt.ylabel("Execution Time (s)")
        plt.grid(True)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path)
        
        if show:
            plt.show()


class LoadTest:
    """
    Load test for measuring system performance under load.
    
    This class provides utilities for measuring system performance under load.
    """
    
    def __init__(self, name: Optional[str] = None):
        """
        Initialize the load test.
        
        Args:
            name: Optional test name
        """
        self.name = name or "LoadTest"
        self.results = {}
    
    async def run(
        self,
        func: Callable[[], Any],
        concurrency: List[int],
        duration: float = 10.0,
    ) -> Dict[int, List[float]]:
        """
        Run a load test.
        
        Args:
            func: Function to test
            concurrency: List of concurrency levels
            duration: Test duration in seconds
            
        Returns:
            Dict[int, List[float]]: Execution times by concurrency level
        """
        results = {}
        
        for level in concurrency:
            print(f"Running load test with concurrency level {level}...")
            
            # Create tasks
            tasks = []
            times = []
            
            async def worker():
                start_time = time.time()
                await func()
                end_time = time.time()
                elapsed_time = end_time - start_time
                times.append(elapsed_time)
            
            # Start initial tasks
            for _ in range(level):
                tasks.append(asyncio.create_task(worker()))
            
            # Run for duration
            end_time = time.time() + duration
            while time.time() < end_time:
                # Wait for a task to complete
                done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                
                # Replace completed tasks
                for task in done:
                    tasks.remove(task)
                    tasks.append(asyncio.create_task(worker()))
            
            # Cancel remaining tasks
            for task in tasks:
                task.cancel()
            
            # Wait for tasks to cancel
            await asyncio.gather(*tasks, return_exceptions=True)
            
            results[level] = times
        
        self.results = results
        return results
    
    def get_stats(self) -> Dict[int, Dict[str, float]]:
        """
        Get load test statistics.
        
        Returns:
            Dict[int, Dict[str, float]]: Statistics by concurrency level
        """
        if not self.results:
            raise ValueError("Load test has not been run")
        
        stats = {}
        
        for level, times in self.results.items():
            stats[level] = {
                "min": min(times),
                "max": max(times),
                "mean": statistics.mean(times),
                "median": statistics.median(times),
                "stdev": statistics.stdev(times) if len(times) > 1 else 0,
                "throughput": len(times) / sum(times),
            }
        
        return stats
    
    def print_stats(self):
        """Print load test statistics."""
        stats = self.get_stats()
        
        print(f"{self.name} Load Test Statistics:")
        
        for level, level_stats in stats.items():
            print(f"\nConcurrency Level {level}:")
            print(f"  Min: {level_stats['min']:.6f} seconds")
            print(f"  Max: {level_stats['max']:.6f} seconds")
            print(f"  Mean: {level_stats['mean']:.6f} seconds")
            print(f"  Median: {level_stats['median']:.6f} seconds")
            print(f"  Stdev: {level_stats['stdev']:.6f} seconds")
            print(f"  Throughput: {level_stats['throughput']:.2f} requests/second")
    
    def plot(self, title: Optional[str] = None, show: bool = True, save_path: Optional[str] = None):
        """
        Plot load test results.
        
        Args:
            title: Optional plot title
            show: Whether to show the plot
            save_path: Optional path to save the plot
        """
        if not self.results:
            raise ValueError("Load test has not been run")
        
        stats = self.get_stats()
        
        plt.figure(figsize=(12, 8))
        
        # Plot response times
        plt.subplot(2, 1, 1)
        
        levels = sorted(self.results.keys())
        means = [stats[level]["mean"] for level in levels]
        stdevs = [stats[level]["stdev"] for level in levels]
        
        plt.errorbar(levels, means, yerr=stdevs, marker='o')
        plt.title(title or f"{self.name} Load Test Results")
        plt.xlabel("Concurrency Level")
        plt.ylabel("Response Time (s)")
        plt.grid(True)
        
        # Plot throughput
        plt.subplot(2, 1, 2)
        
        throughputs = [stats[level]["throughput"] for level in levels]
        
        plt.plot(levels, throughputs, marker='o')
        plt.xlabel("Concurrency Level")
        plt.ylabel("Throughput (requests/s)")
        plt.grid(True)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path)
        
        if show:
            plt.show()
