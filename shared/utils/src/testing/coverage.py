"""
Test coverage utilities for Berrys_AgentsV2.

This module provides utilities for collecting and reporting test coverage, including:
- Test coverage collection
- Coverage report generation
- Coverage trend analysis
- Coverage visualization
"""

import os
import sys
import json
import shutil
import re
import subprocess
from typing import Dict, List, Any, Optional, Union, Set, Tuple
from pathlib import Path

import coverage


class CoverageConfig:
    """
    Configuration for test coverage collection.
    
    This class provides a configuration object for test coverage collection,
    including source directories, exclusion patterns, and report settings.
    """
    
    def __init__(
        self,
        source_dirs: Optional[List[str]] = None,
        omit_patterns: Optional[List[str]] = None,
        include_patterns: Optional[List[str]] = None,
        fail_under: float = 80.0,
        exclude_lines: Optional[List[str]] = None,
        report_formats: Optional[List[str]] = None,
        output_dir: str = "coverage_reports"
    ):
        """
        Initialize coverage configuration.
        
        Args:
            source_dirs: List of source directories to collect coverage for.
            omit_patterns: List of file patterns to exclude from coverage.
            include_patterns: List of file patterns to include in coverage.
            fail_under: Threshold for failing if coverage is below this percentage.
            exclude_lines: List of line patterns to exclude from coverage.
            report_formats: List of report formats to generate (default: ["xml", "html", "json"]).
            output_dir: Directory to store coverage reports.
        """
        self.source_dirs = source_dirs or ["src"]
        self.omit_patterns = omit_patterns or [
            "*/tests/*",
            "*/test_*",
            "*/__pycache__/*",
            "*/\\.git/*",
            "*/\\.venv/*",
            "*/venv/*",
            "*/migrations/*",
            "*/alembic/*",
            "*/docs/*",
            "*/node_modules/*"
        ]
        self.include_patterns = include_patterns or ["*.py"]
        self.fail_under = fail_under
        self.exclude_lines = exclude_lines or [
            "pragma: no cover",
            "def __repr__",
            "raise NotImplementedError",
            "pass",
            "raise ImportError",
            "if TYPE_CHECKING:",
            "if __name__ == .__main__.:",
            "class .*\\bProtocol\\):",
            "@(abc\\.)?abstractmethod"
        ]
        self.report_formats = report_formats or ["xml", "html", "json"]
        self.output_dir = output_dir
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the configuration to a dictionary.
        
        Returns:
            Dictionary representation of the configuration.
        """
        return {
            "source_dirs": self.source_dirs,
            "omit_patterns": self.omit_patterns,
            "include_patterns": self.include_patterns,
            "fail_under": self.fail_under,
            "exclude_lines": self.exclude_lines,
            "report_formats": self.report_formats,
            "output_dir": self.output_dir
        }
        
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "CoverageConfig":
        """
        Create a configuration from a dictionary.
        
        Args:
            config_dict: Dictionary representation of a configuration.
            
        Returns:
            Coverage configuration.
        """
        return cls(
            source_dirs=config_dict.get("source_dirs"),
            omit_patterns=config_dict.get("omit_patterns"),
            include_patterns=config_dict.get("include_patterns"),
            fail_under=config_dict.get("fail_under", 80.0),
            exclude_lines=config_dict.get("exclude_lines"),
            report_formats=config_dict.get("report_formats"),
            output_dir=config_dict.get("output_dir", "coverage_reports")
        )
        
    def to_json(self, file_path: str) -> None:
        """
        Save the configuration to a JSON file.
        
        Args:
            file_path: Path to save the configuration.
        """
        with open(file_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
            
    @classmethod
    def from_json(cls, file_path: str) -> "CoverageConfig":
        """
        Load a configuration from a JSON file.
        
        Args:
            file_path: Path to load the configuration from.
            
        Returns:
            Coverage configuration.
        """
        with open(file_path, "r") as f:
            config_dict = json.load(f)
            
        return cls.from_dict(config_dict)
        
    def to_coverage_config(self) -> Dict[str, Any]:
        """
        Convert the configuration to a coverage.py configuration.
        
        Returns:
            Configuration dictionary for coverage.py.
        """
        return {
            "source": self.source_dirs,
            "omit": self.omit_patterns,
            "include": self.include_patterns,
            "report": {
                "exclude_lines": self.exclude_lines,
                "fail_under": self.fail_under
            }
        }


class CoverageCollector:
    """
    Collector for test coverage.
    
    This class provides methods for collecting, generating, and reporting
    test coverage data.
    """
    
    def __init__(
        self,
        config: Optional[CoverageConfig] = None,
        base_dir: Optional[str] = None
    ):
        """
        Initialize the coverage collector.
        
        Args:
            config: Coverage configuration.
            base_dir: Base directory for coverage data.
        """
        self.config = config or CoverageConfig()
        self.base_dir = base_dir or os.getcwd()
        self.cov = self._create_coverage()
        
    def _create_coverage(self) -> coverage.Coverage:
        """
        Create a coverage.py Coverage object.
        
        Returns:
            Coverage object.
        """
        return coverage.Coverage(
            source=self.config.source_dirs,
            omit=self.config.omit_patterns,
            include=self.config.include_patterns,
            config_file=False
        )
        
    def start(self) -> None:
        """Start collecting coverage data."""
        self.cov.start()
        
    def stop(self) -> None:
        """Stop collecting coverage data."""
        self.cov.stop()
        
    def save(self) -> None:
        """Save coverage data."""
        self.cov.save()
        
    def load(self) -> None:
        """Load coverage data."""
        self.cov.load()
        
    def combine(self, data_files: Optional[List[str]] = None) -> None:
        """
        Combine coverage data from multiple files.
        
        Args:
            data_files: List of coverage data files to combine.
        """
        self.cov.combine(data_files)
        
    def generate_reports(
        self,
        output_dir: Optional[str] = None,
        formats: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate coverage reports.
        
        Args:
            output_dir: Directory to store coverage reports.
            formats: List of report formats to generate.
            
        Returns:
            Dictionary of report paths.
        """
        output_dir = output_dir or self.config.output_dir
        formats = formats or self.config.report_formats
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        report_paths = {}
        
        # Generate reports
        for report_format in formats:
            if report_format == "xml":
                xml_path = os.path.join(output_dir, "coverage.xml")
                self.cov.xml_report(outfile=xml_path)
                report_paths["xml"] = xml_path
                
            elif report_format == "html":
                html_dir = os.path.join(output_dir, "html")
                self.cov.html_report(directory=html_dir)
                report_paths["html"] = html_dir
                
            elif report_format == "json":
                json_path = os.path.join(output_dir, "coverage.json")
                self.cov.json_report(outfile=json_path)
                report_paths["json"] = json_path
                
            elif report_format == "text":
                text_path = os.path.join(output_dir, "coverage.txt")
                with open(text_path, "w") as f:
                    self.cov.report(file=f)
                report_paths["text"] = text_path
                
        # Generate summary file
        summary_path = os.path.join(output_dir, "summary.json")
        self.save_coverage_summary(summary_path)
        report_paths["summary"] = summary_path
        
        return report_paths
        
    def get_coverage_data(self) -> Dict[str, Any]:
        """
        Get coverage data.
        
        Returns:
            Dictionary of coverage data.
        """
        data = self.cov.get_data()
        
        # Get overall coverage percentage
        total_statements = 0
        total_missing = 0
        
        file_coverage = {}
        
        for file_path in data.measured_files():
            # Skip files that match omit patterns
            if any(re.match(pattern, file_path) for pattern in self.config.omit_patterns):
                continue
                
            # Get file coverage
            statements = set(data.lines(file_path))
            missing = set(data.missing_lines(file_path))
            
            if statements:
                coverage_percentage = 100.0 * (len(statements) - len(missing)) / len(statements)
            else:
                coverage_percentage = 100.0
                
            file_coverage[file_path] = {
                "statements": len(statements),
                "missing": len(missing),
                "excluded": len(data.excluded_lines(file_path)),
                "coverage": coverage_percentage
            }
            
            total_statements += len(statements)
            total_missing += len(missing)
            
        # Calculate overall coverage
        if total_statements:
            overall_coverage = 100.0 * (total_statements - total_missing) / total_statements
        else:
            overall_coverage = 100.0
            
        return {
            "overall_coverage": overall_coverage,
            "total_statements": total_statements,
            "total_missing": total_missing,
            "file_coverage": file_coverage
        }
        
    def save_coverage_summary(self, output_path: str) -> None:
        """
        Save a coverage summary to a file.
        
        Args:
            output_path: Path to save the summary.
        """
        summary = self.get_coverage_summary()
        
        with open(output_path, "w") as f:
            json.dump(summary, f, indent=2)
            
    def get_coverage_summary(self) -> Dict[str, Any]:
        """
        Get a summary of coverage data.
        
        Returns:
            Dictionary of coverage summary data.
        """
        coverage_data = self.get_coverage_data()
        
        # Get top 5 most covered files
        most_covered = sorted(
            coverage_data["file_coverage"].items(),
            key=lambda x: x[1]["coverage"],
            reverse=True
        )[:5]
        
        # Get top 5 least covered files
        least_covered = sorted(
            coverage_data["file_coverage"].items(),
            key=lambda x: x[1]["coverage"]
        )[:5]
        
        return {
            "overall_coverage": coverage_data["overall_coverage"],
            "total_statements": coverage_data["total_statements"],
            "total_missing": coverage_data["total_missing"],
            "num_files": len(coverage_data["file_coverage"]),
            "most_covered": {
                file_path: data["coverage"]
                for file_path, data in most_covered
            },
            "least_covered": {
                file_path: data["coverage"]
                for file_path, data in least_covered
            },
            "threshold": self.config.fail_under,
            "passed": coverage_data["overall_coverage"] >= self.config.fail_under
        }
        
    def check_coverage(self) -> bool:
        """
        Check if coverage meets the threshold.
        
        Returns:
            True if coverage meets or exceeds the threshold.
        """
        coverage_data = self.get_coverage_data()
        return coverage_data["overall_coverage"] >= self.config.fail_under


def run_pytest_with_coverage(
    test_paths: List[str],
    output_dir: str = "coverage_reports",
    config: Optional[CoverageConfig] = None,
    pytest_args: Optional[List[str]] = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Run pytest with coverage.
    
    Args:
        test_paths: List of paths to test files or directories.
        output_dir: Directory to store coverage reports.
        config: Coverage configuration.
        pytest_args: Additional arguments to pass to pytest.
        
    Returns:
        Tuple of (success, coverage_data).
    """
    config = config or CoverageConfig(output_dir=output_dir)
    pytest_args = pytest_args or []
    
    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # Initialize coverage
    collector = CoverageCollector(config)
    
    try:
        # Start coverage collection
        collector.start()
        
        # Run pytest
        import pytest
        result = pytest.main(test_paths + pytest_args)
        
        # Stop coverage collection
        collector.stop()
        
        # Generate reports
        report_paths = collector.generate_reports(output_dir)
        
        # Get coverage data
        coverage_data = collector.get_coverage_data()
        
        # Add report paths to coverage data
        coverage_data["report_paths"] = report_paths
        
        return result == 0, coverage_data
        
    except Exception as e:
        print(f"Error running pytest with coverage: {e}")
        return False, {}
        

def run_pytest_coverage_command(
    test_paths: List[str],
    output_dir: str = "coverage_reports",
    config: Optional[CoverageConfig] = None,
    pytest_args: Optional[List[str]] = None
) -> Tuple[bool, str]:
    """
    Run pytest coverage command.
    
    This function runs pytest with coverage by executing the pytest command
    with the pytest-cov plugin.
    
    Args:
        test_paths: List of paths to test files or directories.
        output_dir: Directory to store coverage reports.
        config: Coverage configuration.
        pytest_args: Additional arguments to pass to pytest.
        
    Returns:
        Tuple of (success, output).
    """
    config = config or CoverageConfig(output_dir=output_dir)
    pytest_args = pytest_args or []
    
    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # Construct pytest command
    cmd = [
        sys.executable, "-m", "pytest",
        *test_paths,
        "--cov=" + ",".join(config.source_dirs),
        f"--cov-report=html:{os.path.join(output_dir, 'html')}",
        f"--cov-report=xml:{os.path.join(output_dir, 'coverage.xml')}",
        f"--cov-report=json:{os.path.join(output_dir, 'coverage.json')}",
        f"--cov-fail-under={config.fail_under}",
        *pytest_args
    ]
    
    try:
        # Run pytest command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        
        # Write output to file
        output_path = os.path.join(output_dir, "pytest_output.txt")
        with open(output_path, "w") as f:
            f.write(result.stdout)
            f.write("\n\n")
            f.write(result.stderr)
            
        return result.returncode == 0, result.stdout
        
    except Exception as e:
        print(f"Error running pytest coverage command: {e}")
        return False, str(e)


def combine_coverage_data(
    data_files: List[str],
    output_file: str = ".coverage"
) -> bool:
    """
    Combine coverage data from multiple files.
    
    Args:
        data_files: List of coverage data files to combine.
        output_file: Output file for combined coverage data.
        
    Returns:
        True if combining was successful.
    """
    try:
        cov = coverage.Coverage()
        cov.combine(data_files, strict=True)
        cov.save()
        return True
    except Exception as e:
        print(f"Error combining coverage data: {e}")
        return False


def aggregate_coverage_reports(
    report_dirs: List[str],
    output_dir: str = "combined_coverage",
    config: Optional[CoverageConfig] = None
) -> Dict[str, Any]:
    """
    Aggregate coverage reports from multiple directories.
    
    Args:
        report_dirs: List of directories containing coverage reports.
        output_dir: Directory to store aggregated coverage reports.
        config: Coverage configuration.
        
    Returns:
        Dictionary of aggregated coverage data.
    """
    config = config or CoverageConfig(output_dir=output_dir)
    
    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # Find all coverage data files
    data_files = []
    for report_dir in report_dirs:
        for root, _, files in os.walk(report_dir):
            for file in files:
                if file == ".coverage" or file.startswith(".coverage."):
                    data_files.append(os.path.join(root, file))
                    
    # Combine coverage data
    collector = CoverageCollector(config)
    collector.combine(data_files)
    
    # Generate reports
    report_paths = collector.generate_reports(output_dir)
    
    # Get coverage data
    coverage_data = collector.get_coverage_data()
    
    # Add report paths to coverage data
    coverage_data["report_paths"] = report_paths
    
    return coverage_data


def track_coverage_history(
    summary_file: str,
    history_file: str = "coverage_history.json"
) -> Dict[str, Any]:
    """
    Track coverage history over time.
    
    Args:
        summary_file: Path to coverage summary file.
        history_file: Path to coverage history file.
        
    Returns:
        Dictionary of coverage history data.
    """
    # Load summary
    with open(summary_file, "r") as f:
        summary = json.load(f)
        
    # Load history
    history = []
    if os.path.exists(history_file):
        with open(history_file, "r") as f:
            history = json.load(f)
            
    # Add summary to history
    from datetime import datetime
    
    entry = {
        "date": datetime.now().isoformat(),
        "overall_coverage": summary["overall_coverage"],
        "total_statements": summary["total_statements"],
        "total_missing": summary["total_missing"],
        "num_files": summary["num_files"],
        "threshold": summary["threshold"],
        "passed": summary["passed"]
    }
    
    history.append(entry)
    
    # Save history
    with open(history_file, "w") as f:
        json.dump(history, f, indent=2)
        
    return {
        "history": history,
        "current": entry
    }


def get_coverage_badge_color(coverage: float) -> str:
    """
    Get a color for a coverage badge based on the coverage percentage.
    
    Args:
        coverage: Coverage percentage.
        
    Returns:
        Color string.
    """
    if coverage >= 90:
        return "brightgreen"
    elif coverage >= 80:
        return "green"
    elif coverage >= 70:
        return "yellowgreen"
    elif coverage >= 60:
        return "yellow"
    elif coverage >= 50:
        return "orange"
    else:
        return "red"


def generate_coverage_badge(
    coverage: float,
    output_file: str = "coverage_badge.svg"
) -> str:
    """
    Generate a coverage badge image.
    
    Args:
        coverage: Coverage percentage.
        output_file: Path to save the badge image.
        
    Returns:
        Path to the badge image.
    """
    color = get_coverage_badge_color(coverage)
    
    try:
        import requests
        
        # Generate badge using shields.io
        url = f"https://img.shields.io/badge/coverage-{coverage:.1f}%25-{color}"
        response = requests.get(url)
        
        with open(output_file, "wb") as f:
            f.write(response.content)
            
        return output_file
        
    except ImportError:
        print("Requests library not installed. Install it with: pip install requests")
        return ""
    except Exception as e:
        print(f"Error generating coverage badge: {e}")
        return ""
