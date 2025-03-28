#!/usr/bin/env python3
"""
Deployment Verifier Script

This script verifies that a deployed service is running correctly by checking its health endpoint.
It supports JSON output format.
"""

import argparse
import json
import sys
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
import requests


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Verify a deployed service")
    parser.add_argument(
        "--service-url",
        type=str,
        required=True,
        help="URL of the deployed service",
    )
    parser.add_argument(
        "--health-endpoint",
        type=str,
        default="/health",
        help="Health endpoint to check",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Timeout in seconds",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=5,
        help="Interval between checks in seconds",
    )
    parser.add_argument(
        "--output-file",
        type=str,
        required=True,
        help="Output file path",
    )
    parser.add_argument(
        "--headers",
        type=str,
        default="{}",
        help="Headers to include in the request (JSON string)",
    )
    return parser.parse_args()


def check_health(url: str, headers: Dict[str, str]) -> Dict[str, Any]:
    """Check the health of a service."""
    try:
        response = requests.get(url, headers=headers, timeout=10)
        return {
            "status_code": response.status_code,
            "success": response.status_code == 200,
            "response": response.text,
            "timestamp": datetime.now().isoformat(),
        }
    except requests.exceptions.RequestException as e:
        return {
            "status_code": 0,
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


def verify_deployment(
    service_url: str,
    health_endpoint: str,
    timeout: int,
    interval: int,
    headers: Dict[str, str],
) -> Dict[str, Any]:
    """Verify that a deployed service is running correctly."""
    health_url = f"{service_url.rstrip('/')}/{health_endpoint.lstrip('/')}"
    print(f"Verifying deployment at {health_url}")
    
    start_time = time.time()
    end_time = start_time + timeout
    
    checks = []
    success = False
    
    while time.time() < end_time:
        check_result = check_health(health_url, headers)
        checks.append(check_result)
        
        if check_result["success"]:
            success = True
            break
        
        print(f"Health check failed: {check_result.get('error', f'Status code: {check_result.get('status_code', 0)}')}")
        print(f"Retrying in {interval} seconds...")
        time.sleep(interval)
    
    elapsed_time = time.time() - start_time
    
    return {
        "service_url": service_url,
        "health_endpoint": health_endpoint,
        "success": success,
        "elapsed_time": elapsed_time,
        "checks": checks,
        "timestamp": datetime.now().isoformat(),
    }


def main() -> int:
    """Main function."""
    args = parse_args()
    
    try:
        headers = json.loads(args.headers)
    except json.JSONDecodeError:
        print(f"Error parsing headers: {args.headers}")
        return 1
    
    # Verify deployment
    result = verify_deployment(
        args.service_url,
        args.health_endpoint,
        args.timeout,
        args.interval,
        headers,
    )
    
    # Write result to file
    with open(args.output_file, "w") as f:
        json.dump(result, f, indent=2)
    
    print(f"Verification result written to {args.output_file}")
    
    # Return success or failure
    return 0 if result["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
