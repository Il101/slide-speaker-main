#!/usr/bin/env python3
"""
Validation script for load testing setup
Checks if all required components are properly configured
"""

import sys
import subprocess
from pathlib import Path
from typing import List, Tuple


class Color:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'


def check_command(command: str) -> bool:
    """Check if a command is available"""
    try:
        subprocess.run(
            [command, '--version'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def check_python_package(package: str) -> bool:
    """Check if a Python package is installed"""
    try:
        __import__(package)
        return True
    except ImportError:
        return False


def check_file_exists(filepath: Path) -> bool:
    """Check if file exists"""
    return filepath.exists()


def check_file_executable(filepath: Path) -> bool:
    """Check if file is executable"""
    return filepath.exists() and filepath.stat().st_mode & 0o111


def print_status(check_name: str, passed: bool, details: str = ""):
    """Print check status with color"""
    status = f"{Color.GREEN}✓{Color.END}" if passed else f"{Color.RED}✗{Color.END}"
    print(f"  {status} {check_name}", end="")
    if details:
        print(f" - {details}", end="")
    print()


def main():
    """Run all validation checks"""
    print(f"\n{Color.BLUE}=== Load Testing Setup Validation ==={Color.END}\n")
    
    all_checks: List[Tuple[str, bool, str]] = []
    
    # Check system requirements
    print(f"{Color.BLUE}System Requirements:{Color.END}")
    
    python_ok = check_command('python3')
    all_checks.append(("Python 3", python_ok, "Required for running tests"))
    print_status("Python 3", python_ok, "Required for running tests")
    
    pip_ok = check_command('pip3')
    all_checks.append(("pip3", pip_ok, "Required for installing packages"))
    print_status("pip3", pip_ok, "Required for installing packages")
    
    curl_ok = check_command('curl')
    all_checks.append(("curl", curl_ok, "Used for health checks"))
    print_status("curl", curl_ok, "Used for health checks")
    
    docker_ok = check_command('docker')
    all_checks.append(("Docker", docker_ok, "Optional - for distributed testing"))
    print_status("Docker", docker_ok, "Optional - for distributed testing")
    
    print()
    
    # Check Python packages
    print(f"{Color.BLUE}Python Packages:{Color.END}")
    
    locust_ok = check_python_package('locust')
    all_checks.append(("Locust", locust_ok, "Core load testing framework"))
    print_status("Locust", locust_ok, "Core load testing framework")
    
    httpx_ok = check_python_package('httpx')
    all_checks.append(("httpx", httpx_ok, "HTTP client"))
    print_status("httpx", httpx_ok, "HTTP client")
    
    pptx_ok = check_python_package('pptx')
    all_checks.append(("python-pptx", pptx_ok, "For test data generation"))
    print_status("python-pptx", pptx_ok, "For test data generation")
    
    print()
    
    # Check files
    print(f"{Color.BLUE}Load Testing Files:{Color.END}")
    
    base_dir = Path(__file__).parent
    
    files_to_check = [
        ("locustfile.py", "Main test scenarios"),
        ("config.py", "Test configuration"),
        ("requirements.txt", "Python dependencies"),
        ("README.md", "Documentation"),
        ("analyze_results.py", "Results analysis"),
        ("check_thresholds.py", "Threshold validation"),
        ("generate_test_data.py", "Test data generator"),
    ]
    
    for filename, description in files_to_check:
        filepath = base_dir / filename
        exists = check_file_exists(filepath)
        all_checks.append((filename, exists, description))
        print_status(filename, exists, description)
    
    print()
    
    # Check executable scripts
    print(f"{Color.BLUE}Executable Scripts:{Color.END}")
    
    scripts_to_check = [
        ("run_load_tests.sh", "Main test runner"),
        ("quickstart.sh", "Quick start script"),
        ("monitor_resources.sh", "Resource monitoring"),
    ]
    
    for filename, description in scripts_to_check:
        filepath = base_dir / filename
        is_executable = check_file_executable(filepath)
        all_checks.append((filename, is_executable, description))
        print_status(
            filename,
            is_executable,
            f"{description} - {'executable' if is_executable else 'NOT executable'}"
        )
    
    print()
    
    # Check backend availability (optional)
    print(f"{Color.BLUE}Backend Availability (Optional):{Color.END}")
    try:
        result = subprocess.run(
            ['curl', '-sf', 'http://localhost:8000/health'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5
        )
        backend_ok = result.returncode == 0
    except:
        backend_ok = False
    
    print_status(
        "Backend at localhost:8000",
        backend_ok,
        "OK" if backend_ok else "Not running (docker-compose up -d)"
    )
    
    print()
    
    # Summary
    print(f"{Color.BLUE}=== Summary ==={Color.END}")
    
    required_checks = [c for c in all_checks if "Optional" not in c[2]]
    passed = sum(1 for _, status, _ in required_checks if status)
    total = len(required_checks)
    
    print(f"Passed: {passed}/{total} required checks")
    
    if passed == total:
        print(f"\n{Color.GREEN}✓ All required checks passed!{Color.END}")
        print(f"\n{Color.BLUE}Ready to run load tests:{Color.END}")
        print(f"  ./quickstart.sh")
        print(f"  ./run_load_tests.sh light http://localhost:8000")
        return 0
    else:
        print(f"\n{Color.RED}✗ Some required checks failed{Color.END}")
        print(f"\n{Color.YELLOW}To fix:{Color.END}")
        
        if not locust_ok:
            print(f"  pip3 install -r requirements.txt")
        
        for filename, description in scripts_to_check:
            filepath = base_dir / filename
            if not check_file_executable(filepath):
                print(f"  chmod +x {filename}")
        
        if not backend_ok:
            print(f"  docker-compose up -d  # (optional, for testing)")
        
        return 1


if __name__ == "__main__":
    sys.exit(main())
