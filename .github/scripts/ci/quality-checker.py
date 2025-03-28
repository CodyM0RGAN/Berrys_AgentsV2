#!/usr/bin/env python3
"""
Quality Checker Script

This script collects quality check results from multiple services and generates a consolidated report.
It supports JSON, HTML, and Markdown output formats.
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Collect quality check results and generate a report")
    parser.add_argument(
        "--artifacts-dir",
        type=str,
        required=True,
        help="Directory containing quality check artifacts",
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


def find_quality_results(artifacts_dir: str) -> Dict[str, Dict[str, str]]:
    """Find all quality check result files in the artifacts directory."""
    results = {}
    artifacts_path = Path(artifacts_dir)
    
    # Look for service directories
    for service_dir in artifacts_path.glob("*-quality-results"):
        service_name = service_dir.name.replace("-quality-results", "")
        results[service_name] = {}
        
        # Look for quality check result files
        for result_file in service_dir.glob("**/*"):
            if result_file.is_file():
                tool_name = result_file.name.replace("-results.txt", "").replace("-results.json", "")
                results[service_name][tool_name] = str(result_file)
    
    return results


def parse_flake8_results(result_file: str) -> Dict[str, Any]:
    """Parse flake8 results."""
    try:
        with open(result_file, "r") as f:
            content = f.read()
        
        lines = content.strip().split("\n")
        issues = []
        
        for line in lines:
            if not line.strip():
                continue
            
            parts = line.split(":", 3)
            if len(parts) >= 4:
                file_path = parts[0]
                line_num = int(parts[1])
                col_num = int(parts[2])
                message = parts[3].strip()
                
                issues.append({
                    "file": file_path,
                    "line": line_num,
                    "column": col_num,
                    "message": message,
                })
        
        return {
            "issues": issues,
            "count": len(issues),
            "success": len(issues) == 0,
        }
    except Exception as e:
        print(f"Error parsing flake8 results from {result_file}: {e}")
        return {
            "issues": [],
            "count": 0,
            "success": False,
            "error": str(e),
        }


def parse_pylint_results(result_file: str) -> Dict[str, Any]:
    """Parse pylint results."""
    try:
        with open(result_file, "r") as f:
            content = f.read()
        
        lines = content.strip().split("\n")
        issues = []
        score = 0.0
        
        for line in lines:
            if not line.strip():
                continue
            
            if line.startswith("Your code has been rated at "):
                score_part = line.split("Your code has been rated at ")[1].split("/")[0]
                try:
                    score = float(score_part)
                except ValueError:
                    pass
            elif ":" in line and not line.startswith("*"):
                parts = line.split(":", 2)
                if len(parts) >= 3:
                    file_path = parts[0]
                    line_num = int(parts[1])
                    message_parts = parts[2].strip().split("] ", 1)
                    if len(message_parts) >= 2:
                        code = message_parts[0].strip("[")
                        message = message_parts[1]
                        
                        issues.append({
                            "file": file_path,
                            "line": line_num,
                            "code": code,
                            "message": message,
                        })
        
        return {
            "issues": issues,
            "count": len(issues),
            "score": score,
            "success": score >= 7.0,  # Consider a score of 7.0 or higher as success
        }
    except Exception as e:
        print(f"Error parsing pylint results from {result_file}: {e}")
        return {
            "issues": [],
            "count": 0,
            "score": 0.0,
            "success": False,
            "error": str(e),
        }


def parse_black_results(result_file: str) -> Dict[str, Any]:
    """Parse black results."""
    try:
        with open(result_file, "r") as f:
            content = f.read()
        
        lines = content.strip().split("\n")
        issues = []
        
        for line in lines:
            if not line.strip():
                continue
            
            if "would reformat" in line:
                file_path = line.split("would reformat ")[1]
                issues.append({
                    "file": file_path,
                    "message": "Would be reformatted by black",
                })
        
        return {
            "issues": issues,
            "count": len(issues),
            "success": len(issues) == 0,
        }
    except Exception as e:
        print(f"Error parsing black results from {result_file}: {e}")
        return {
            "issues": [],
            "count": 0,
            "success": False,
            "error": str(e),
        }


def parse_isort_results(result_file: str) -> Dict[str, Any]:
    """Parse isort results."""
    try:
        with open(result_file, "r") as f:
            content = f.read()
        
        lines = content.strip().split("\n")
        issues = []
        
        for line in lines:
            if not line.strip():
                continue
            
            if "ERROR" in line and "Imports are incorrectly sorted" in line:
                file_path = line.split("ERROR: ")[1].split(" Imports are incorrectly sorted")[0]
                issues.append({
                    "file": file_path,
                    "message": "Imports are incorrectly sorted",
                })
        
        return {
            "issues": issues,
            "count": len(issues),
            "success": len(issues) == 0,
        }
    except Exception as e:
        print(f"Error parsing isort results from {result_file}: {e}")
        return {
            "issues": [],
            "count": 0,
            "success": False,
            "error": str(e),
        }


def parse_mypy_results(result_file: str) -> Dict[str, Any]:
    """Parse mypy results."""
    try:
        with open(result_file, "r") as f:
            content = f.read()
        
        lines = content.strip().split("\n")
        issues = []
        
        for line in lines:
            if not line.strip():
                continue
            
            if ":" in line and "error:" in line:
                parts = line.split(":", 2)
                if len(parts) >= 3:
                    file_path = parts[0]
                    line_num = int(parts[1])
                    message = parts[2].strip()
                    
                    issues.append({
                        "file": file_path,
                        "line": line_num,
                        "message": message,
                    })
        
        return {
            "issues": issues,
            "count": len(issues),
            "success": len(issues) == 0,
        }
    except Exception as e:
        print(f"Error parsing mypy results from {result_file}: {e}")
        return {
            "issues": [],
            "count": 0,
            "success": False,
            "error": str(e),
        }


def parse_bandit_results(result_file: str) -> Dict[str, Any]:
    """Parse bandit results."""
    try:
        with open(result_file, "r") as f:
            data = json.load(f)
        
        issues = []
        
        for result in data.get("results", []):
            issues.append({
                "file": result.get("filename", ""),
                "line": result.get("line_number", 0),
                "severity": result.get("issue_severity", ""),
                "confidence": result.get("issue_confidence", ""),
                "code": result.get("test_id", ""),
                "message": result.get("issue_text", ""),
            })
        
        return {
            "issues": issues,
            "count": len(issues),
            "success": len(issues) == 0,
        }
    except Exception as e:
        print(f"Error parsing bandit results from {result_file}: {e}")
        return {
            "issues": [],
            "count": 0,
            "success": False,
            "error": str(e),
        }


def parse_safety_results(result_file: str) -> Dict[str, Any]:
    """Parse safety results."""
    try:
        with open(result_file, "r") as f:
            data = json.load(f)
        
        issues = []
        
        for vulnerability in data.get("vulnerabilities", []):
            issues.append({
                "package": vulnerability.get("package_name", ""),
                "installed_version": vulnerability.get("installed_version", ""),
                "vulnerable_spec": vulnerability.get("vulnerable_spec", ""),
                "id": vulnerability.get("vulnerability_id", ""),
                "message": vulnerability.get("advisory", ""),
            })
        
        return {
            "issues": issues,
            "count": len(issues),
            "success": len(issues) == 0,
        }
    except Exception as e:
        print(f"Error parsing safety results from {result_file}: {e}")
        return {
            "issues": [],
            "count": 0,
            "success": False,
            "error": str(e),
        }


def collect_quality_results(artifacts_dir: str) -> Dict[str, Dict[str, Any]]:
    """Collect quality check results from all services."""
    results = {}
    result_files = find_quality_results(artifacts_dir)
    
    for service_name, tool_files in result_files.items():
        service_results = {}
        
        for tool_name, result_file in tool_files.items():
            if tool_name == "flake8":
                service_results[tool_name] = parse_flake8_results(result_file)
            elif tool_name == "pylint":
                service_results[tool_name] = parse_pylint_results(result_file)
            elif tool_name == "black":
                service_results[tool_name] = parse_black_results(result_file)
            elif tool_name == "isort":
                service_results[tool_name] = parse_isort_results(result_file)
            elif tool_name == "mypy":
                service_results[tool_name] = parse_mypy_results(result_file)
            elif tool_name == "bandit":
                service_results[tool_name] = parse_bandit_results(result_file)
            elif tool_name == "safety":
                service_results[tool_name] = parse_safety_results(result_file)
        
        # Calculate overall success
        lint_success = all(
            service_results.get(tool, {}).get("success", False)
            for tool in ["flake8", "pylint", "black", "isort", "mypy"]
            if tool in service_results
        )
        
        security_success = all(
            service_results.get(tool, {}).get("success", False)
            for tool in ["bandit", "safety"]
            if tool in service_results
        )
        
        service_results["lint_success"] = lint_success
        service_results["security_success"] = security_success
        service_results["overall_success"] = lint_success and security_success
        
        results[service_name] = service_results
    
    return results


def generate_json_report(results: Dict[str, Dict[str, Any]]) -> str:
    """Generate a JSON report from quality check results."""
    # Calculate overall metrics
    services_count = len(results)
    lint_success_count = sum(1 for r in results.values() if r.get("lint_success", False))
    security_success_count = sum(1 for r in results.values() if r.get("security_success", False))
    overall_success_count = sum(1 for r in results.values() if r.get("overall_success", False))
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "services": services_count,
            "lint_success": lint_success_count,
            "security_success": security_success_count,
            "overall_success": overall_success_count,
            "lint_success_rate": lint_success_count / services_count if services_count > 0 else 0,
            "security_success_rate": security_success_count / services_count if services_count > 0 else 0,
            "overall_success_rate": overall_success_count / services_count if services_count > 0 else 0,
        },
        "services": results,
    }
    
    return json.dumps(report, indent=2)


def generate_html_report(results: Dict[str, Dict[str, Any]]) -> str:
    """Generate an HTML report from quality check results."""
    # Calculate overall metrics
    services_count = len(results)
    lint_success_count = sum(1 for r in results.values() if r.get("lint_success", False))
    security_success_count = sum(1 for r in results.values() if r.get("security_success", False))
    overall_success_count = sum(1 for r in results.values() if r.get("overall_success", False))
    
    lint_success_rate = lint_success_count / services_count if services_count > 0 else 0
    security_success_rate = security_success_count / services_count if services_count > 0 else 0
    overall_success_rate = overall_success_count / services_count if services_count > 0 else 0
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Quality Check Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            line-height: 1.6;
        }}
        h1, h2, h3, h4 {{
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
        .issue {{
            margin-bottom: 10px;
            padding: 5px;
            border-left: 3px solid #ddd;
        }}
        .issue.security {{
            border-left-color: red;
        }}
        .issue.lint {{
            border-left-color: orange;
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
        .progress-bar.failure {{
            background-color: #f44336;
        }}
        .collapsible {{
            background-color: #f1f1f1;
            color: #333;
            cursor: pointer;
            padding: 10px;
            width: 100%;
            border: none;
            text-align: left;
            outline: none;
            font-size: 15px;
            margin-bottom: 5px;
            border-radius: 5px;
        }}
        .active, .collapsible:hover {{
            background-color: #ddd;
        }}
        .content {{
            padding: 0 18px;
            display: none;
            overflow: hidden;
            background-color: #f9f9f9;
            border-radius: 5px;
        }}
    </style>
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            var coll = document.getElementsByClassName("collapsible");
            for (var i = 0; i < coll.length; i++) {{
                coll[i].addEventListener("click", function() {{
                    this.classList.toggle("active");
                    var content = this.nextElementSibling;
                    if (content.style.display === "block") {{
                        content.style.display = "none";
                    }} else {{
                        content.style.display = "block";
                    }}
                }});
            }}
        }});
    </script>
</head>
<body>
    <h1>Quality Check Report</h1>
    <div class="summary">
        <h2>Summary</h2>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Services: {services_count}</p>
        <p>Lint Success: {lint_success_count}/{services_count} ({lint_success_rate:.1%})</p>
        <p>Security Success: {security_success_count}/{services_count} ({security_success_rate:.1%})</p>
        <p>Overall Success: {overall_success_count}/{services_count} ({overall_success_rate:.1%})</p>
    </div>
    
    <h2>Services</h2>
    <table>
        <tr>
            <th>Service</th>
            <th>Lint Status</th>
            <th>Security Status</th>
            <th>Overall Status</th>
        </tr>
"""
    
    # Add service rows
    for service_name, result in results.items():
        lint_success = result.get("lint_success", False)
        security_success = result.get("security_success", False)
        overall_success = result.get("overall_success", False)
        
        html += f"""
        <tr>
            <td>{service_name}</td>
            <td class="{'success' if lint_success else 'failure'}">{
                'Success' if lint_success else 'Failure'}</td>
            <td class="{'success' if security_success else 'failure'}">{
                'Success' if security_success else 'Failure'}</td>
            <td class="{'success' if overall_success else 'failure'}">{
                'Success' if overall_success else 'Failure'}</td>
        </tr>"""
    
    html += """
    </table>
    
    <h2>Tool Results</h2>
"""
    
    # Add tool results
    for service_name, result in results.items():
        html += f"""
    <h3>{service_name}</h3>
    <table>
        <tr>
            <th>Tool</th>
            <th>Issues</th>
            <th>Status</th>
        </tr>
"""
        
        for tool_name in ["flake8", "pylint", "black", "isort", "mypy", "bandit", "safety"]:
            if tool_name in result:
                tool_result = result[tool_name]
                issues_count = tool_result.get("count", 0)
                success = tool_result.get("success", False)
                
                html += f"""
        <tr>
            <td>{tool_name}</td>
            <td>{issues_count}</td>
            <td class="{'success' if success else 'failure'}">{
                'Success' if success else 'Failure'}</td>
        </tr>"""
        
        html += """
    </table>
"""
        
        # Add issue details
        html += """
    <h4>Issues</h4>
"""
        
        for tool_name in ["flake8", "pylint", "black", "isort", "mypy", "bandit", "safety"]:
            if tool_name in result and result[tool_name].get("count", 0) > 0:
                issues = result[tool_name].get("issues", [])
                
                html += f"""
    <button class="collapsible">{tool_name} ({len(issues)} issues)</button>
    <div class="content">
"""
                
                for issue in issues:
                    issue_class = "security" if tool_name in ["bandit", "safety"] else "lint"
                    
                    if tool_name == "safety":
                        html += f"""
        <div class="issue {issue_class}">
            <p><strong>Package:</strong> {issue.get('package', '')}</p>
            <p><strong>Installed Version:</strong> {issue.get('installed_version', '')}</p>
            <p><strong>Vulnerable Spec:</strong> {issue.get('vulnerable_spec', '')}</p>
            <p><strong>ID:</strong> {issue.get('id', '')}</p>
            <p><strong>Message:</strong> {issue.get('message', '')}</p>
        </div>
"""
                    elif tool_name == "bandit":
                        html += f"""
        <div class="issue {issue_class}">
            <p><strong>File:</strong> {issue.get('file', '')}</p>
            <p><strong>Line:</strong> {issue.get('line', '')}</p>
            <p><strong>Severity:</strong> {issue.get('severity', '')}</p>
            <p><strong>Confidence:</strong> {issue.get('confidence', '')}</p>
            <p><strong>Code:</strong> {issue.get('code', '')}</p>
            <p><strong>Message:</strong> {issue.get('message', '')}</p>
        </div>
"""
                    elif tool_name == "pylint":
                        html += f"""
        <div class="issue {issue_class}">
            <p><strong>File:</strong> {issue.get('file', '')}</p>
            <p><strong>Line:</strong> {issue.get('line', '')}</p>
            <p><strong>Code:</strong> {issue.get('code', '')}</p>
            <p><strong>Message:</strong> {issue.get('message', '')}</p>
        </div>
"""
                    else:
                        html += f"""
        <div class="issue {issue_class}">
            <p><strong>File:</strong> {issue.get('file', '')}</p>
            <p><strong>Line:</strong> {issue.get('line', '') if 'line' in issue else 'N/A'}</p>
            <p><strong>Message:</strong> {issue.get('message', '')}</p>
        </div>
"""
                
                html += """
    </div>
"""
    
    html += """
</body>
</html>
"""
    
    return html


def generate_markdown_report(results: Dict[str, Dict[str, Any]]) -> str:
    """Generate a Markdown report from quality check results."""
    # Calculate overall metrics
    services_count = len(results)
    lint_success_count = sum(1 for r in results.values() if r.get("lint_success", False))
    security_success_count = sum(1 for r in results.values() if r.get("security_success", False))
    overall_success_count = sum(1 for r in results.values() if r.get("overall_success", False))
    
    lint_success_rate = lint_success_count / services_count if services_count > 0 else 0
    security_success_rate = security_success_count / services_count if services_count > 0 else 0
    overall_success_rate = overall_success_count / services_count if services_count > 0 else 0
    
    markdown = f"""# Quality Check Report

## Summary

- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Services: {services_count}
- Lint Success: {lint_success_count}/{services_count} ({lint_success_rate:.1%})
- Security Success: {security_success_count}/{services_count} ({security_success_rate:.1%})
- Overall Success: {overall_success_count}/{services_count} ({overall_success_rate:.1%})

## Services

| Service | Lint Status | Security Status | Overall Status |
|---------|------------|----------------|----------------|
"""
    
    # Add service rows
    for service_name, result in results.items():
        lint_success = result.get("lint_success", False)
        security_success = result.get("security_success", False)
        overall_success = result.get("overall_success", False)
        
        markdown += f"| {service_name} | {'Success' if lint_success else 'Failure'} | {'Success' if security_success else 'Failure'} | {'Success' if overall_success else 'Failure'} |\n"
    
    markdown += "\n## Tool Results\n"
    
    # Add tool results
    for service_name, result in results.items():
        markdown += f"\n### {service_name}\n\n"
        markdown += "| Tool | Issues | Status |\n"
        markdown += "|------|--------|--------|\n"
        
        for tool_name in ["flake8", "pylint", "black", "isort", "mypy", "bandit", "safety"]:
            if tool_name in result:
                tool_result = result[tool_name]
                issues_count = tool_result.get("count", 0)
                success = tool_result.get("success", False)
                
                markdown += f"| {tool_name} | {issues_count} | {'Success' if success else 'Failure'} |\n"
        
        # Add issue details
        markdown += "\n#### Issues\n\n"
        
        for tool_name in ["flake8", "pylint", "black", "isort", "mypy", "bandit", "safety"]:
            if tool_name in result and result[tool_name].get("count", 0) > 0:
                issues = result[tool_name].get("issues", [])
                
                markdown += f"**{tool_name}** ({len(issues)} issues)\n\n"
                
                for i, issue in enumerate(issues[:10]):  # Limit to 10 issues per tool
                    if tool_name == "safety":
                        markdown += f"- **Package:** {issue.get('package', '')}\n"
                        markdown += f"  - **Installed Version:** {issue.get('installed_version', '')}\n"
                        markdown += f"  - **Vulnerable Spec:** {issue.get('vulnerable_spec', '')}\n"
                        markdown += f"  - **ID:** {issue.get('id', '')}\n"
                        markdown += f"  - **Message:** {issue.get('message', '')}\n"
                    elif tool_name == "bandit":
                        markdown += f"- **File:** {issue.get('file', '')}\n"
                        markdown += f"  - **Line:** {issue.get('line', '')}\n"
                        markdown += f"  - **Severity:** {issue.get('severity', '')}\n"
                        markdown += f"  - **Confidence:** {issue.get('confidence', '')}\n"
                        markdown += f"  - **Code:** {issue.get('code', '')}\n"
                        markdown += f"  - **Message:** {issue.get('message', '')}\n"
                    elif tool_name == "pylint":
                        markdown += f"- **File:** {issue.get('file', '')}\n"
                        markdown += f"  - **Line:** {issue.get('line', '')}\n"
                        markdown += f"  - **Code:** {issue.get('code', '')}\n"
                        markdown += f"  - **Message:** {issue.get('message', '')}\n"
                    else:
                        markdown += f"- **File:** {issue.get('file', '')}\n"
                        if 'line' in issue:
                            markdown += f"  - **Line:** {issue.get('line', '')}\n"
                        markdown += f"  - **Message:** {issue.get('message', '')}\n"
                
                if len(issues) > 10:
                    markdown += f"\n... and {len(issues) - 10} more issues\n"
                
                markdown += "\n"
    
    return markdown


def main() -> int:
    """Main function."""
    args = parse_args()
    
    # Collect quality check results
    results = collect_quality_results(args.artifacts_dir)
    
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
    
    # Check if all services passed
    all_passed = all(result.get("overall_success", False) for result in results.values())
    
    if not all_passed:
        print("Some quality checks failed!")
        return 1
    
    print("All quality checks passed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
