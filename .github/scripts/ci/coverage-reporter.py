#!/usr/bin/env python3
"""
Coverage Reporter Script

This script collects coverage results from multiple services and generates a consolidated report.
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
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Collect coverage results and generate a report")
    parser.add_argument(
        "--artifacts-dir",
        type=str,
        required=True,
        help="Directory containing coverage artifacts",
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
    parser.add_argument(
        "--threshold",
        type=float,
        default=80.0,
        help="Coverage threshold percentage",
    )
    return parser.parse_args()


def find_coverage_results(artifacts_dir: str) -> List[Tuple[str, str]]:
    """Find all coverage XML files in the artifacts directory."""
    results = []
    artifacts_path = Path(artifacts_dir)
    
    # Look for service directories
    for service_dir in artifacts_path.glob("*-test-results"):
        service_name = service_dir.name.replace("-test-results", "")
        
        # Look for coverage XML files
        for result_file in service_dir.glob("**/*.xml"):
            if "coverage.xml" in str(result_file):
                results.append((service_name, str(result_file)))
    
    return results


def parse_coverage_results(result_file: str) -> Dict[str, Any]:
    """Parse a coverage XML file."""
    try:
        tree = ET.parse(result_file)
        root = tree.getroot()
        
        # Extract coverage metrics
        line_rate = float(root.attrib.get("line-rate", 0)) * 100
        branch_rate = float(root.attrib.get("branch-rate", 0)) * 100
        complexity = float(root.attrib.get("complexity", 0))
        
        # Extract package metrics
        packages = []
        for package in root.findall(".//package"):
            pkg = {
                "name": package.attrib.get("name", ""),
                "line_rate": float(package.attrib.get("line-rate", 0)) * 100,
                "branch_rate": float(package.attrib.get("branch-rate", 0)) * 100,
                "complexity": float(package.attrib.get("complexity", 0)),
            }
            
            # Extract class metrics
            classes = []
            for cls in package.findall(".//class"):
                cls_data = {
                    "name": cls.attrib.get("name", ""),
                    "filename": cls.attrib.get("filename", ""),
                    "line_rate": float(cls.attrib.get("line-rate", 0)) * 100,
                    "branch_rate": float(cls.attrib.get("branch-rate", 0)) * 100,
                    "complexity": float(cls.attrib.get("complexity", 0)),
                }
                classes.append(cls_data)
            
            pkg["classes"] = classes
            packages.append(pkg)
        
        return {
            "line_rate": line_rate,
            "branch_rate": branch_rate,
            "complexity": complexity,
            "packages": packages,
        }
    except Exception as e:
        print(f"Error parsing coverage results from {result_file}: {e}")
        return {
            "line_rate": 0,
            "branch_rate": 0,
            "complexity": 0,
            "packages": [],
            "error": str(e),
        }


def collect_coverage_results(artifacts_dir: str) -> Dict[str, Any]:
    """Collect coverage results from all services."""
    results = {}
    result_files = find_coverage_results(artifacts_dir)
    
    for service_name, result_file in result_files:
        results[service_name] = parse_coverage_results(result_file)
    
    return results


def generate_coverage_chart(results: Dict[str, Any], output_file: str, threshold: float) -> str:
    """Generate a coverage chart and save it to a file."""
    # Extract service names and line rates
    services = list(results.keys())
    line_rates = [results[service]["line_rate"] for service in services]
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Create bar chart
    bars = ax.bar(services, line_rates, color='skyblue')
    
    # Add threshold line
    ax.axhline(y=threshold, color='r', linestyle='-', label=f'Threshold ({threshold}%)')
    
    # Color bars based on threshold
    for i, bar in enumerate(bars):
        if line_rates[i] < threshold:
            bar.set_color('salmon')
        else:
            bar.set_color('lightgreen')
    
    # Add labels and title
    ax.set_xlabel('Services')
    ax.set_ylabel('Line Coverage (%)')
    ax.set_title('Code Coverage by Service')
    
    # Add value labels on top of bars
    for i, v in enumerate(line_rates):
        ax.text(i, v + 1, f"{v:.1f}%", ha='center')
    
    # Set y-axis range
    ax.set_ylim(0, 105)
    
    # Add legend
    ax.legend()
    
    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45, ha='right')
    
    # Adjust layout
    plt.tight_layout()
    
    # Save chart
    chart_file = f"{os.path.splitext(output_file)[0]}_chart.png"
    plt.savefig(chart_file)
    plt.close()
    
    return chart_file


def generate_json_report(results: Dict[str, Any], threshold: float) -> str:
    """Generate a JSON report from coverage results."""
    # Calculate overall metrics
    services_count = len(results)
    if services_count > 0:
        overall_line_rate = sum(r["line_rate"] for r in results.values()) / services_count
        overall_branch_rate = sum(r["branch_rate"] for r in results.values()) / services_count
        overall_complexity = sum(r["complexity"] for r in results.values())
    else:
        overall_line_rate = 0
        overall_branch_rate = 0
        overall_complexity = 0
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "services": services_count,
            "line_rate": overall_line_rate,
            "branch_rate": overall_branch_rate,
            "complexity": overall_complexity,
            "threshold": threshold,
            "meets_threshold": overall_line_rate >= threshold,
        },
        "services": results,
    }
    
    return json.dumps(report, indent=2)


def generate_html_report(results: Dict[str, Any], threshold: float, chart_file: str) -> str:
    """Generate an HTML report from coverage results."""
    # Calculate overall metrics
    services_count = len(results)
    if services_count > 0:
        overall_line_rate = sum(r["line_rate"] for r in results.values()) / services_count
        overall_branch_rate = sum(r["branch_rate"] for r in results.values()) / services_count
        overall_complexity = sum(r["complexity"] for r in results.values())
    else:
        overall_line_rate = 0
        overall_branch_rate = 0
        overall_complexity = 0
    
    meets_threshold = overall_line_rate >= threshold
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Coverage Report</title>
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
        .chart {{
            margin: 20px 0;
            text-align: center;
        }}
        .chart img {{
            max-width: 100%;
            height: auto;
        }}
        .progress {{
            height: 20px;
            background-color: #f5f5f5;
            border-radius: 5px;
            margin-bottom: 10px;
        }}
        .progress-bar {{
            height: 100%;
            border-radius: 5px;
            background-color: #4CAF50;
        }}
        .progress-bar.below-threshold {{
            background-color: #f44336;
        }}
    </style>
</head>
<body>
    <h1>Coverage Report</h1>
    <div class="summary">
        <h2>Summary</h2>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Services: {services_count}</p>
        <p>Overall Line Coverage: {overall_line_rate:.2f}%</p>
        <p>Overall Branch Coverage: {overall_branch_rate:.2f}%</p>
        <p>Overall Complexity: {overall_complexity:.2f}</p>
        <p>Threshold: {threshold}%</p>
        <p>Status: <span class="{'success' if meets_threshold else 'failure'}">{
            'Meets Threshold' if meets_threshold else 'Below Threshold'}</span></p>
    </div>
    
    <div class="chart">
        <h2>Coverage Chart</h2>
        <img src="{os.path.basename(chart_file)}" alt="Coverage Chart">
    </div>
    
    <h2>Services</h2>
    <table>
        <tr>
            <th>Service</th>
            <th>Line Coverage</th>
            <th>Branch Coverage</th>
            <th>Complexity</th>
            <th>Status</th>
        </tr>
"""
    
    # Add service rows
    for service_name, result in results.items():
        meets_service_threshold = result["line_rate"] >= threshold
        html += f"""
        <tr>
            <td>{service_name}</td>
            <td>
                <div class="progress">
                    <div class="progress-bar{'below-threshold' if not meets_service_threshold else ''}" 
                         style="width: {min(result['line_rate'], 100)}%"></div>
                </div>
                {result['line_rate']:.2f}%
            </td>
            <td>{result['branch_rate']:.2f}%</td>
            <td>{result['complexity']:.2f}</td>
            <td class="{'success' if meets_service_threshold else 'failure'}">{
                'Meets Threshold' if meets_service_threshold else 'Below Threshold'}</td>
        </tr>"""
    
    html += """
    </table>
    
    <h2>Package Details</h2>
"""
    
    # Add package details
    for service_name, result in results.items():
        html += f"""
    <h3>{service_name}</h3>
    <table>
        <tr>
            <th>Package</th>
            <th>Line Coverage</th>
            <th>Branch Coverage</th>
            <th>Complexity</th>
        </tr>
"""
        
        for package in result["packages"]:
            meets_package_threshold = package["line_rate"] >= threshold
            html += f"""
        <tr>
            <td>{package['name']}</td>
            <td>
                <div class="progress">
                    <div class="progress-bar{'below-threshold' if not meets_package_threshold else ''}" 
                         style="width: {min(package['line_rate'], 100)}%"></div>
                </div>
                {package['line_rate']:.2f}%
            </td>
            <td>{package['branch_rate']:.2f}%</td>
            <td>{package['complexity']:.2f}</td>
        </tr>"""
        
        html += """
    </table>
"""
    
    html += """
</body>
</html>
"""
    
    return html


def generate_markdown_report(results: Dict[str, Any], threshold: float, chart_file: str) -> str:
    """Generate a Markdown report from coverage results."""
    # Calculate overall metrics
    services_count = len(results)
    if services_count > 0:
        overall_line_rate = sum(r["line_rate"] for r in results.values()) / services_count
        overall_branch_rate = sum(r["branch_rate"] for r in results.values()) / services_count
        overall_complexity = sum(r["complexity"] for r in results.values())
    else:
        overall_line_rate = 0
        overall_branch_rate = 0
        overall_complexity = 0
    
    meets_threshold = overall_line_rate >= threshold
    
    markdown = f"""# Coverage Report

## Summary

- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Services: {services_count}
- Overall Line Coverage: {overall_line_rate:.2f}%
- Overall Branch Coverage: {overall_branch_rate:.2f}%
- Overall Complexity: {overall_complexity:.2f}
- Threshold: {threshold}%
- Status: {'Meets Threshold' if meets_threshold else 'Below Threshold'}

## Coverage Chart

![Coverage Chart]({os.path.basename(chart_file)})

## Services

| Service | Line Coverage | Branch Coverage | Complexity | Status |
|---------|--------------|----------------|------------|--------|
"""
    
    # Add service rows
    for service_name, result in results.items():
        meets_service_threshold = result["line_rate"] >= threshold
        markdown += f"| {service_name} | {result['line_rate']:.2f}% | {result['branch_rate']:.2f}% | {result['complexity']:.2f} | {'Meets Threshold' if meets_service_threshold else 'Below Threshold'} |\n"
    
    markdown += "\n## Package Details\n"
    
    # Add package details
    for service_name, result in results.items():
        markdown += f"\n### {service_name}\n\n"
        markdown += "| Package | Line Coverage | Branch Coverage | Complexity |\n"
        markdown += "|---------|--------------|----------------|------------|\n"
        
        for package in result["packages"]:
            markdown += f"| {package['name']} | {package['line_rate']:.2f}% | {package['branch_rate']:.2f}% | {package['complexity']:.2f} |\n"
    
    return markdown


def main() -> int:
    """Main function."""
    args = parse_args()
    
    # Collect coverage results
    results = collect_coverage_results(args.artifacts_dir)
    
    # Generate coverage chart
    chart_file = generate_coverage_chart(results, args.output_file, args.threshold)
    
    # Generate report
    if args.format == "json":
        report = generate_json_report(results, args.threshold)
    elif args.format == "html":
        report = generate_html_report(results, args.threshold, chart_file)
    elif args.format == "markdown":
        report = generate_markdown_report(results, args.threshold, chart_file)
    else:
        print(f"Unsupported format: {args.format}")
        return 1
    
    # Write report to file
    with open(args.output_file, "w") as f:
        f.write(report)
    
    print(f"Report written to {args.output_file}")
    
    # Calculate overall line rate
    services_count = len(results)
    if services_count > 0:
        overall_line_rate = sum(r["line_rate"] for r in results.values()) / services_count
    else:
        overall_line_rate = 0
    
    # Check if coverage meets threshold
    if overall_line_rate < args.threshold:
        print(f"Coverage of {overall_line_rate:.2f}% does not meet the threshold of {args.threshold}%")
        return 1
    
    print(f"Coverage of {overall_line_rate:.2f}% meets the threshold of {args.threshold}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
