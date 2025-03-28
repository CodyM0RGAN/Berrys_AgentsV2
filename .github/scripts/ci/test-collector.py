#!/usr/bin/env python3
"""
Test Collector Script

This script collects test results from multiple services and generates a consolidated report.
It supports JSON, HTML, and Markdown output formats.
"""

import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Collect test results and generate a report")
    parser.add_argument(
        "--artifacts-dir",
        type=str,
        required=True,
        help="Directory containing test artifacts",
    )
    parser.add_argument(
        "--output-file",
        type=str,
        required=True,
        help="Output file path",
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["json", "html", "markdown"],
        default="json",
        help="Output format",
    )
    return parser.parse_args()


def find_test_results(artifacts_dir: str) -> List[Tuple[str, str]]:
    """Find all test result XML files in the artifacts directory."""
    results = []
    artifacts_path = Path(artifacts_dir)
    
    # Look for service directories
    for service_dir in artifacts_path.glob("*-test-results"):
        service_name = service_dir.name.replace("-test-results", "")
        
        # Look for test result XML files
        for result_file in service_dir.glob("**/*.xml"):
            if "test-results.xml" in str(result_file):
                results.append((service_name, str(result_file)))
    
    return results


def parse_test_results(result_file: str) -> Dict[str, Any]:
    """Parse a JUnit XML test result file."""
    try:
        tree = ET.parse(result_file)
        root = tree.getroot()
        
        # Extract test counts
        tests = int(root.attrib.get("tests", 0))
        failures = int(root.attrib.get("failures", 0))
        errors = int(root.attrib.get("errors", 0))
        skipped = int(root.attrib.get("skipped", 0))
        time = float(root.attrib.get("time", 0))
        
        # Extract test cases
        test_cases = []
        for test_case in root.findall(".//testcase"):
            case = {
                "name": test_case.attrib.get("name", ""),
                "classname": test_case.attrib.get("classname", ""),
                "time": float(test_case.attrib.get("time", 0)),
                "status": "passed",
                "message": "",
            }
            
            # Check for failures
            failure = test_case.find("failure")
            if failure is not None:
                case["status"] = "failed"
                case["message"] = failure.attrib.get("message", "")
            
            # Check for errors
            error = test_case.find("error")
            if error is not None:
                case["status"] = "error"
                case["message"] = error.attrib.get("message", "")
            
            # Check for skipped
            skipped_elem = test_case.find("skipped")
            if skipped_elem is not None:
                case["status"] = "skipped"
                case["message"] = skipped_elem.attrib.get("message", "")
            
            test_cases.append(case)
        
        return {
            "tests": tests,
            "failures": failures,
            "errors": errors,
            "skipped": skipped,
            "time": time,
            "test_cases": test_cases,
            "success": failures == 0 and errors == 0,
        }
    except Exception as e:
        print(f"Error parsing test results from {result_file}: {e}")
        return {
            "tests": 0,
            "failures": 0,
            "errors": 0,
            "skipped": 0,
            "time": 0,
            "test_cases": [],
            "success": False,
            "error": str(e),
        }


def collect_test_results(artifacts_dir: str) -> Dict[str, Any]:
    """Collect test results from all services."""
    results = {}
    result_files = find_test_results(artifacts_dir)
    
    for service_name, result_file in result_files:
        results[service_name] = parse_test_results(result_file)
    
    return results


def generate_json_report(results: Dict[str, Any]) -> str:
    """Generate a JSON report from test results."""
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "services": len(results),
            "tests": sum(r["tests"] for r in results.values()),
            "failures": sum(r["failures"] for r in results.values()),
            "errors": sum(r["errors"] for r in results.values()),
            "skipped": sum(r["skipped"] for r in results.values()),
            "time": sum(r["time"] for r in results.values()),
            "success": all(r["success"] for r in results.values()),
        },
        "services": results,
    }
    
    return json.dumps(report, indent=2)


def generate_html_report(results: Dict[str, Any]) -> str:
    """Generate an HTML report from test results."""
    total_tests = sum(r["tests"] for r in results.values())
    total_failures = sum(r["failures"] for r in results.values())
    total_errors = sum(r["errors"] for r in results.values())
    total_skipped = sum(r["skipped"] for r in results.values())
    total_time = sum(r["time"] for r in results.values())
    overall_success = all(r["success"] for r in results.values())
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Test Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            line-height: 1.6;
        }}
        h1, h2, h3 {{
            color: #333;
        }}
        .summary {{
            margin-bottom: 20px;
            padding: 10px;
            background-color: #f5f5f5;
            border-radius: 5px;
        }}
        .success {{
            color: green;
        }}
        .failure {{
            color: red;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin-bottom: 20px;
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
        .test-case {{
            margin-bottom: 10px;
            padding: 5px;
            border-left: 3px solid #ddd;
        }}
        .test-case.passed {{
            border-left-color: green;
        }}
        .test-case.failed {{
            border-left-color: red;
        }}
        .test-case.error {{
            border-left-color: orange;
        }}
        .test-case.skipped {{
            border-left-color: gray;
        }}
    </style>
</head>
<body>
    <h1>Test Report</h1>
    <div class="summary">
        <h2>Summary</h2>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Services: {len(results)}</p>
        <p>Tests: {total_tests}</p>
        <p>Failures: {total_failures}</p>
        <p>Errors: {total_errors}</p>
        <p>Skipped: {total_skipped}</p>
        <p>Time: {total_time:.2f}s</p>
        <p>Status: <span class="{'success' if overall_success else 'failure'}">{
            'Success' if overall_success else 'Failure'}</span></p>
    </div>
    
    <h2>Services</h2>
    <table>
        <tr>
            <th>Service</th>
            <th>Tests</th>
            <th>Failures</th>
            <th>Errors</th>
            <th>Skipped</th>
            <th>Time</th>
            <th>Status</th>
        </tr>
"""
    
    # Add service rows
    for service_name, result in results.items():
        html += f"""
        <tr>
            <td>{service_name}</td>
            <td>{result['tests']}</td>
            <td>{result['failures']}</td>
            <td>{result['errors']}</td>
            <td>{result['skipped']}</td>
            <td>{result['time']:.2f}s</td>
            <td class="{'success' if result['success'] else 'failure'}">{
                'Success' if result['success'] else 'Failure'}</td>
        </tr>"""
    
    html += """
    </table>
    
    <h2>Test Cases</h2>
"""
    
    # Add test cases
    for service_name, result in results.items():
        html += f"""
    <h3>{service_name}</h3>
"""
        
        for test_case in result["test_cases"]:
            html += f"""
    <div class="test-case {test_case['status']}">
        <p><strong>{test_case['classname']}.{test_case['name']}</strong> ({test_case['time']:.2f}s)</p>
        <p>Status: {test_case['status'].capitalize()}</p>
"""
            
            if test_case["message"]:
                html += f"""
        <p>Message: {test_case['message']}</p>
"""
            
            html += """
    </div>
"""
    
    html += """
</body>
</html>
"""
    
    return html


def generate_markdown_report(results: Dict[str, Any]) -> str:
    """Generate a Markdown report from test results."""
    total_tests = sum(r["tests"] for r in results.values())
    total_failures = sum(r["failures"] for r in results.values())
    total_errors = sum(r["errors"] for r in results.values())
    total_skipped = sum(r["skipped"] for r in results.values())
    total_time = sum(r["time"] for r in results.values())
    overall_success = all(r["success"] for r in results.values())
    
    markdown = f"""# Test Report

## Summary

- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Services: {len(results)}
- Tests: {total_tests}
- Failures: {total_failures}
- Errors: {total_errors}
- Skipped: {total_skipped}
- Time: {total_time:.2f}s
- Status: {'Success' if overall_success else 'Failure'}

## Services

| Service | Tests | Failures | Errors | Skipped | Time | Status |
|---------|-------|----------|--------|---------|------|--------|
"""
    
    # Add service rows
    for service_name, result in results.items():
        markdown += f"| {service_name} | {result['tests']} | {result['failures']} | {result['errors']} | {result['skipped']} | {result['time']:.2f}s | {'Success' if result['success'] else 'Failure'} |\n"
    
    markdown += "\n## Test Cases\n"
    
    # Add test cases
    for service_name, result in results.items():
        markdown += f"\n### {service_name}\n\n"
        
        for test_case in result["test_cases"]:
            markdown += f"- **{test_case['classname']}.{test_case['name']}** ({test_case['time']:.2f}s)\n"
            markdown += f"  - Status: {test_case['status'].capitalize()}\n"
            
            if test_case["message"]:
                markdown += f"  - Message: {test_case['message']}\n"
    
    return markdown


def main() -> int:
    """Main function."""
    args = parse_args()
    
    # Collect test results
    results = collect_test_results(args.artifacts_dir)
    
    # Generate report
    if args.format == "json":
        report = generate_json_report(results)
    elif args.format == "html":
        report = generate_html_report(results)
    elif args.format == "markdown":
        report = generate_markdown_report(results)
    else:
        print(f"Unsupported format: {args.format}")
        return 1
    
    # Write report to file
    with open(args.output_file, "w") as f:
        f.write(report)
    
    print(f"Report written to {args.output_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
