"""
Test reporting and visualization utilities.

This module provides utilities for generating test reports and visualizing test results.
"""

import os
import json
import csv
import datetime
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional, Union, Tuple
import matplotlib.pyplot as plt
import numpy as np


class TestResult:
    """
    Test result data structure.
    
    This class represents a test result, including test name, status, duration, and details.
    """
    
    def __init__(
        self,
        name: str,
        status: str,
        duration: float,
        details: Optional[str] = None,
        error: Optional[str] = None,
        timestamp: Optional[datetime.datetime] = None,
    ):
        """
        Initialize the test result.
        
        Args:
            name: Test name
            status: Test status (passed, failed, skipped, error)
            duration: Test duration in seconds
            details: Optional test details
            error: Optional error message
            timestamp: Optional test timestamp
        """
        self.name = name
        self.status = status
        self.duration = duration
        self.details = details
        self.error = error
        self.timestamp = timestamp or datetime.datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation
        """
        return {
            "name": self.name,
            "status": self.status,
            "duration": self.duration,
            "details": self.details,
            "error": self.error,
            "timestamp": self.timestamp.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestResult':
        """
        Create from dictionary.
        
        Args:
            data: Dictionary representation
            
        Returns:
            TestResult: Test result
        """
        timestamp = data.get("timestamp")
        if timestamp and isinstance(timestamp, str):
            timestamp = datetime.datetime.fromisoformat(timestamp)
        
        return cls(
            name=data["name"],
            status=data["status"],
            duration=data["duration"],
            details=data.get("details"),
            error=data.get("error"),
            timestamp=timestamp,
        )


class TestSuite:
    """
    Test suite data structure.
    
    This class represents a test suite, including suite name and test results.
    """
    
    def __init__(
        self,
        name: str,
        results: Optional[List[TestResult]] = None,
        timestamp: Optional[datetime.datetime] = None,
    ):
        """
        Initialize the test suite.
        
        Args:
            name: Suite name
            results: Optional list of test results
            timestamp: Optional suite timestamp
        """
        self.name = name
        self.results = results or []
        self.timestamp = timestamp or datetime.datetime.now()
    
    def add_result(self, result: TestResult):
        """
        Add a test result.
        
        Args:
            result: Test result
        """
        self.results.append(result)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get suite statistics.
        
        Returns:
            Dict[str, Any]: Suite statistics
        """
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == "passed")
        failed = sum(1 for r in self.results if r.status == "failed")
        skipped = sum(1 for r in self.results if r.status == "skipped")
        error = sum(1 for r in self.results if r.status == "error")
        
        durations = [r.duration for r in self.results if r.duration is not None]
        total_duration = sum(durations)
        
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "error": error,
            "pass_rate": passed / total if total > 0 else 0,
            "total_duration": total_duration,
            "average_duration": total_duration / total if total > 0 else 0,
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation
        """
        return {
            "name": self.name,
            "timestamp": self.timestamp.isoformat(),
            "results": [r.to_dict() for r in self.results],
            "stats": self.get_stats(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestSuite':
        """
        Create from dictionary.
        
        Args:
            data: Dictionary representation
            
        Returns:
            TestSuite: Test suite
        """
        timestamp = data.get("timestamp")
        if timestamp and isinstance(timestamp, str):
            timestamp = datetime.datetime.fromisoformat(timestamp)
        
        suite = cls(
            name=data["name"],
            timestamp=timestamp,
        )
        
        for result_data in data.get("results", []):
            suite.add_result(TestResult.from_dict(result_data))
        
        return suite


class TestReport:
    """
    Test report data structure.
    
    This class represents a test report, including report name and test suites.
    """
    
    def __init__(
        self,
        name: str,
        suites: Optional[List[TestSuite]] = None,
        timestamp: Optional[datetime.datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the test report.
        
        Args:
            name: Report name
            suites: Optional list of test suites
            timestamp: Optional report timestamp
            metadata: Optional report metadata
        """
        self.name = name
        self.suites = suites or []
        self.timestamp = timestamp or datetime.datetime.now()
        self.metadata = metadata or {}
    
    def add_suite(self, suite: TestSuite):
        """
        Add a test suite.
        
        Args:
            suite: Test suite
        """
        self.suites.append(suite)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get report statistics.
        
        Returns:
            Dict[str, Any]: Report statistics
        """
        total_suites = len(self.suites)
        
        total = 0
        passed = 0
        failed = 0
        skipped = 0
        error = 0
        total_duration = 0
        
        for suite in self.suites:
            stats = suite.get_stats()
            total += stats["total"]
            passed += stats["passed"]
            failed += stats["failed"]
            skipped += stats["skipped"]
            error += stats["error"]
            total_duration += stats["total_duration"]
        
        return {
            "total_suites": total_suites,
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "error": error,
            "pass_rate": passed / total if total > 0 else 0,
            "total_duration": total_duration,
            "average_duration": total_duration / total if total > 0 else 0,
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation
        """
        return {
            "name": self.name,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "suites": [s.to_dict() for s in self.suites],
            "stats": self.get_stats(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestReport':
        """
        Create from dictionary.
        
        Args:
            data: Dictionary representation
            
        Returns:
            TestReport: Test report
        """
        timestamp = data.get("timestamp")
        if timestamp and isinstance(timestamp, str):
            timestamp = datetime.datetime.fromisoformat(timestamp)
        
        report = cls(
            name=data["name"],
            timestamp=timestamp,
            metadata=data.get("metadata", {}),
        )
        
        for suite_data in data.get("suites", []):
            report.add_suite(TestSuite.from_dict(suite_data))
        
        return report


class TestReporter:
    """
    Test reporter for generating test reports.
    
    This class provides utilities for generating test reports in various formats.
    """
    
    def __init__(self, report: TestReport):
        """
        Initialize the reporter.
        
        Args:
            report: Test report
        """
        self.report = report
    
    def to_json(self, file_path: Optional[str] = None) -> Optional[str]:
        """
        Generate a JSON report.
        
        Args:
            file_path: Optional file path to write the report
            
        Returns:
            Optional[str]: JSON string if file_path is None
        """
        report_dict = self.report.to_dict()
        json_str = json.dumps(report_dict, indent=2)
        
        if file_path:
            with open(file_path, "w") as f:
                f.write(json_str)
            return None
        
        return json_str
    
    def to_csv(self, file_path: str):
        """
        Generate a CSV report.
        
        Args:
            file_path: File path to write the report
        """
        with open(file_path, "w", newline="") as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow([
                "Suite", "Test", "Status", "Duration", "Timestamp", "Details", "Error"
            ])
            
            # Write results
            for suite in self.report.suites:
                for result in suite.results:
                    writer.writerow([
                        suite.name,
                        result.name,
                        result.status,
                        result.duration,
                        result.timestamp.isoformat(),
                        result.details or "",
                        result.error or "",
                    ])
    
    def to_junit(self, file_path: str):
        """
        Generate a JUnit XML report.
        
        Args:
            file_path: File path to write the report
        """
        # Create root element
        testsuites = ET.Element("testsuites")
        testsuites.set("name", self.report.name)
        testsuites.set("timestamp", self.report.timestamp.isoformat())
        
        # Add suites
        for suite in self.report.suites:
            testsuite = ET.SubElement(testsuites, "testsuite")
            testsuite.set("name", suite.name)
            testsuite.set("timestamp", suite.timestamp.isoformat())
            
            stats = suite.get_stats()
            testsuite.set("tests", str(stats["total"]))
            testsuite.set("failures", str(stats["failed"]))
            testsuite.set("errors", str(stats["error"]))
            testsuite.set("skipped", str(stats["skipped"]))
            testsuite.set("time", str(stats["total_duration"]))
            
            # Add results
            for result in suite.results:
                testcase = ET.SubElement(testsuite, "testcase")
                testcase.set("name", result.name)
                testcase.set("time", str(result.duration))
                
                if result.status == "failed":
                    failure = ET.SubElement(testcase, "failure")
                    failure.set("message", result.error or "")
                    failure.text = result.details or ""
                
                elif result.status == "error":
                    error = ET.SubElement(testcase, "error")
                    error.set("message", result.error or "")
                    error.text = result.details or ""
                
                elif result.status == "skipped":
                    skipped = ET.SubElement(testcase, "skipped")
                    skipped.set("message", result.details or "")
        
        # Write to file
        tree = ET.ElementTree(testsuites)
        tree.write(file_path, encoding="utf-8", xml_declaration=True)
    
    def to_html(self, file_path: str):
        """
        Generate an HTML report.
        
        Args:
            file_path: File path to write the report
        """
        # Get report stats
        stats = self.report.get_stats()
        
        # Create HTML
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{self.report.name}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
        }}
        h1, h2, h3 {{
            color: #333;
        }}
        .summary {{
            margin: 20px 0;
            padding: 10px;
            background-color: #f5f5f5;
            border-radius: 5px;
        }}
        .stats {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }}
        .stat {{
            padding: 10px;
            border-radius: 5px;
            color: white;
            font-weight: bold;
        }}
        .passed {{
            background-color: #4CAF50;
        }}
        .failed {{
            background-color: #F44336;
        }}
        .skipped {{
            background-color: #FFC107;
        }}
        .error {{
            background-color: #9C27B0;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin-top: 20px;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: #f2f2f2;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        .status-passed {{
            color: #4CAF50;
            font-weight: bold;
        }}
        .status-failed {{
            color: #F44336;
            font-weight: bold;
        }}
        .status-skipped {{
            color: #FFC107;
            font-weight: bold;
        }}
        .status-error {{
            color: #9C27B0;
            font-weight: bold;
        }}
        .details {{
            margin-top: 5px;
            padding: 5px;
            background-color: #f5f5f5;
            border-radius: 3px;
            font-family: monospace;
            white-space: pre-wrap;
        }}
        .error-message {{
            margin-top: 5px;
            padding: 5px;
            background-color: #ffebee;
            border-radius: 3px;
            font-family: monospace;
            white-space: pre-wrap;
        }}
    </style>
</head>
<body>
    <h1>{self.report.name}</h1>
    <p>Generated on {self.report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <div class="summary">
        <h2>Summary</h2>
        <div class="stats">
            <div class="stat passed">Passed: {stats['passed']}</div>
            <div class="stat failed">Failed: {stats['failed']}</div>
            <div class="stat skipped">Skipped: {stats['skipped']}</div>
            <div class="stat error">Error: {stats['error']}</div>
        </div>
        <p>Pass Rate: {stats['pass_rate'] * 100:.2f}%</p>
        <p>Total Duration: {stats['total_duration']:.2f} seconds</p>
        <p>Average Duration: {stats['average_duration']:.2f} seconds</p>
    </div>
"""
        
        # Add suites
        for suite in self.report.suites:
            suite_stats = suite.get_stats()
            
            html += f"""
    <h2>Suite: {suite.name}</h2>
    <div class="summary">
        <div class="stats">
            <div class="stat passed">Passed: {suite_stats['passed']}</div>
            <div class="stat failed">Failed: {suite_stats['failed']}</div>
            <div class="stat skipped">Skipped: {suite_stats['skipped']}</div>
            <div class="stat error">Error: {suite_stats['error']}</div>
        </div>
        <p>Pass Rate: {suite_stats['pass_rate'] * 100:.2f}%</p>
        <p>Total Duration: {suite_stats['total_duration']:.2f} seconds</p>
        <p>Average Duration: {suite_stats['average_duration']:.2f} seconds</p>
    </div>
    
    <table>
        <tr>
            <th>Test</th>
            <th>Status</th>
            <th>Duration</th>
            <th>Details</th>
        </tr>
"""
            
            # Add results
            for result in suite.results:
                html += f"""
        <tr>
            <td>{result.name}</td>
            <td class="status-{result.status}">{result.status}</td>
            <td>{result.duration:.2f} seconds</td>
            <td>
"""
                
                if result.details:
                    html += f"""
                <div class="details">{result.details}</div>
"""
                
                if result.error:
                    html += f"""
                <div class="error-message">{result.error}</div>
"""
                
                html += """
            </td>
        </tr>
"""
            
            html += """
    </table>
"""
        
        html += """
</body>
</html>
"""
        
        # Write to file
        with open(file_path, "w") as f:
            f.write(html)


class TestVisualizer:
    """
    Test visualizer for visualizing test results.
    
    This class provides utilities for visualizing test results.
    """
    
    def __init__(self, report: TestReport):
        """
        Initialize the visualizer.
        
        Args:
            report: Test report
        """
        self.report = report
    
    def plot_summary(self, title: Optional[str] = None, show: bool = True, save_path: Optional[str] = None):
        """
        Plot a summary of test results.
        
        Args:
            title: Optional plot title
            show: Whether to show the plot
            save_path: Optional path to save the plot
        """
        stats = self.report.get_stats()
        
        # Create figure
        plt.figure(figsize=(10, 6))
        
        # Plot pie chart
        plt.subplot(1, 2, 1)
        labels = ["Passed", "Failed", "Skipped", "Error"]
        sizes = [stats["passed"], stats["failed"], stats["skipped"], stats["error"]]
        colors = ["#4CAF50", "#F44336", "#FFC107", "#9C27B0"]
        
        plt.pie(
            sizes,
            labels=labels,
            colors=colors,
            autopct="%1.1f%%",
            startangle=90,
        )
        plt.axis("equal")
        
        # Plot bar chart
        plt.subplot(1, 2, 2)
        x = np.arange(len(labels))
        
        plt.bar(x, sizes, color=colors)
        plt.xticks(x, labels)
        plt.ylabel("Count")
        
        # Set title
        plt.suptitle(title or f"{self.report.name} - Test Summary")
        
        plt.tight_layout()
        
        # Save or show
        if save_path:
            plt.savefig(save_path)
        
        if show:
            plt.show()
    
    def plot_duration(self, title: Optional[str] = None, show: bool = True, save_path: Optional[str] = None):
        """
        Plot test durations.
        
        Args:
            title: Optional plot title
            show: Whether to show the plot
            save_path: Optional path to save the plot
        """
        # Collect data
        suite_names = []
        suite_durations = []
        
        for suite in self.report.suites:
            suite_names.append(suite.name)
            suite_durations.append(suite.get_stats()["total_duration"])
        
        # Create figure
        plt.figure(figsize=(10, 6))
        
        # Plot bar chart
        plt.bar(suite_names, suite_durations)
        plt.xlabel("Suite")
        plt.ylabel("Duration (seconds)")
        plt.title(title or f"{self.report.name} - Test Durations")
        
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        
        # Save or show
        if save_path:
            plt.savefig(save_path)
        
        if show:
            plt.show()
    
    def plot_pass_rate(self, title: Optional[str] = None, show: bool = True, save_path: Optional[str] = None):
        """
        Plot pass rates.
        
        Args:
            title: Optional plot title
            show: Whether to show the plot
            save_path: Optional path to save the plot
        """
        # Collect data
        suite_names = []
        pass_rates = []
        
        for suite in self.report.suites:
            suite_names.append(suite.name)
            pass_rates.append(suite.get_stats()["pass_rate"] * 100)
        
        # Create figure
        plt.figure(figsize=(10, 6))
        
        # Plot bar chart
        plt.bar(suite_names, pass_rates)
        plt.xlabel("Suite")
        plt.ylabel("Pass Rate (%)")
        plt.title(title or f"{self.report.name} - Pass Rates")
        
        plt.axhline(y=100, color="green", linestyle="--")
        plt.ylim(0, 105)
        
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        
        # Save or show
        if save_path:
            plt.savefig(save_path)
        
        if show:
            plt.show()
    
    def plot_status_by_suite(self, title: Optional[str] = None, show: bool = True, save_path: Optional[str] = None):
        """
        Plot test status by suite.
        
        Args:
            title: Optional plot title
            show: Whether to show the plot
            save_path: Optional path to save the plot
        """
        # Collect data
        suite_names = []
        passed_counts = []
        failed_counts = []
        skipped_counts = []
        error_counts = []
        
        for suite in self.report.suites:
            stats = suite.get_stats()
            suite_names.append(suite.name)
            passed_counts.append(stats["passed"])
            failed_counts.append(stats["failed"])
            skipped_counts.append(stats["skipped"])
            error_counts.append(stats["error"])
        
        # Create figure
        plt.figure(figsize=(12, 6))
        
        # Plot stacked bar chart
        x = np.arange(len(suite_names))
        width = 0.6
        
        plt.bar(x, passed_counts, width, label="Passed", color="#4CAF50")
        plt.bar(x, failed_counts, width, bottom=passed_counts, label="Failed", color="#F44336")
        
        bottom = np.add(passed_counts, failed_counts)
        plt.bar(x, skipped_counts, width, bottom=bottom, label="Skipped", color="#FFC107")
        
        bottom = np.add(bottom, skipped_counts)
        plt.bar(x, error_counts, width, bottom=bottom, label="Error", color="#9C27B0")
        
        plt.xlabel("Suite")
        plt.ylabel("Count")
        plt.title(title or f"{self.report.name} - Test Status by Suite")
        plt.xticks(x, suite_names, rotation=45, ha="right")
        plt.legend()
        
        plt.tight_layout()
        
        # Save or show
        if save_path:
            plt.savefig(save_path)
        
        if show:
            plt.show()
