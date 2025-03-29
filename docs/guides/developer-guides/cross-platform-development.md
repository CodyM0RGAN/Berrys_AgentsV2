# Cross-Platform Development Guide

This guide provides best practices for developing cross-platform applications in the Berrys_AgentsV2 project, focusing on compatibility between Windows, Linux, and macOS.

## Quick Reference

- Use path separators appropriately with `os.path` or `pathlib`
- Be aware of case sensitivity differences between platforms
- Use cross-platform libraries and tools when possible
- Test on all target platforms
- Document platform-specific requirements and behaviors

## Path Handling

### Path Separators

Different operating systems use different path separators:
- Windows: Backslash (`\`)
- Linux/macOS: Forward slash (`/`)

To handle this correctly, use the appropriate libraries:

#### Python

```python
# Using os.path (works on all platforms)
import os

# Join path components
path = os.path.join('directory', 'subdirectory', 'file.txt')

# Split path into components
directory, filename = os.path.split(path)

# Get directory name
dirname = os.path.dirname(path)

# Get file name
filename = os.path.basename(path)
```

```python
# Using pathlib (modern, object-oriented approach)
from pathlib import Path

# Create path object
path = Path('directory') / 'subdirectory' / 'file.txt'

# Get parent directory
parent = path.parent

# Get file name
filename = path.name

# Get stem (file name without extension)
stem = path.stem

# Get suffix (file extension)
suffix = path.suffix
```

#### PowerShell

```powershell
# Join path components
$path = Join-Path -Path "directory" -ChildPath "subdirectory" | Join-Path -ChildPath "file.txt"

# Split path into components
$directory = Split-Path -Path $path -Parent
$filename = Split-Path -Path $path -Leaf
```

#### Bash

```bash
# Join path components
path="directory/subdirectory/file.txt"

# Split path into components
directory=$(dirname "$path")
filename=$(basename "$path")
```

### Absolute vs. Relative Paths

Be careful with absolute paths, as they are platform-specific:

```python
# Bad (Windows-specific)
path = "C:\\Users\\username\\documents\\file.txt"

# Bad (Linux/macOS-specific)
path = "/home/username/documents/file.txt"

# Good (cross-platform)
import os
from pathlib import Path

# Using os.path
home_dir = os.path.expanduser("~")
path = os.path.join(home_dir, "documents", "file.txt")

# Using pathlib
home_dir = Path.home()
path = home_dir / "documents" / "file.txt"
```

## Case Sensitivity

File systems on different platforms have different case sensitivity behaviors:
- Windows: Case-insensitive (typically)
- Linux: Case-sensitive
- macOS: Case-insensitive by default, but can be case-sensitive

To ensure cross-platform compatibility:

1. **Be consistent with case**: Always use the same case for the same files and directories
2. **Avoid files that differ only by case**: Don't create files like `Config.json` and `config.json` in the same directory
3. **Use case-sensitive comparisons**: When comparing file names, use case-sensitive comparisons

```python
# Case-sensitive comparison (safer for cross-platform)
if file_name == "config.json":
    # Do something

# Case-insensitive comparison (may be needed in some cases)
if file_name.lower() == "config.json".lower():
    # Do something
```

## Line Endings

Different platforms use different line ending conventions:
- Windows: Carriage Return + Line Feed (`\r\n`)
- Linux/macOS: Line Feed (`\n`)

To handle this correctly:

1. **Use text mode for file operations**: This automatically converts line endings

```python
# Good (handles line endings automatically)
with open("file.txt", "r") as f:
    content = f.read()

# Also good (explicit text mode)
with open("file.txt", "rt") as f:
    content = f.read()

# Bad (binary mode doesn't handle line endings)
with open("file.txt", "rb") as f:
    content = f.read().decode("utf-8")
```

2. **Configure Git to handle line endings**:

Create a `.gitattributes` file in your repository:

```
# Set default behavior to automatically normalize line endings
* text=auto

# Explicitly declare text files to be normalized
*.py text
*.md text
*.json text

# Declare files that will always have specific line endings
*.bat text eol=crlf
*.sh text eol=lf
```

## Environment Variables

Environment variables are accessed differently on different platforms:

#### Python (cross-platform)

```python
import os

# Get environment variable
value = os.environ.get("VARIABLE_NAME", "default_value")

# Set environment variable
os.environ["VARIABLE_NAME"] = "value"
```

#### PowerShell (Windows)

```powershell
# Get environment variable
$value = $env:VARIABLE_NAME

# Set environment variable
$env:VARIABLE_NAME = "value"
```

#### Bash (Linux/macOS)

```bash
# Get environment variable
value=$VARIABLE_NAME

# Set environment variable
export VARIABLE_NAME="value"
```

## File and Directory Operations

### Creating Directories

```python
# Python (cross-platform)
import os
from pathlib import Path

# Using os
if not os.path.exists("directory"):
    os.makedirs("directory")

# Using pathlib
directory = Path("directory")
directory.mkdir(exist_ok=True, parents=True)
```

```powershell
# PowerShell (Windows)
if (-not (Test-Path -Path "directory")) {
    New-Item -Path "directory" -ItemType Directory
}
```

```bash
# Bash (Linux/macOS)
mkdir -p directory
```

### Checking if File Exists

```python
# Python (cross-platform)
import os
from pathlib import Path

# Using os
if os.path.exists("file.txt"):
    # File exists

# Using pathlib
if Path("file.txt").exists():
    # File exists
```

```powershell
# PowerShell (Windows)
if (Test-Path -Path "file.txt") {
    # File exists
}
```

```bash
# Bash (Linux/macOS)
if [ -f "file.txt" ]; then
    # File exists
fi
```

## Process Management

### Running External Commands

```python
# Python (cross-platform)
import subprocess

# Run command and wait for it to complete
result = subprocess.run(["command", "arg1", "arg2"], capture_output=True, text=True)
print(result.stdout)

# Run command and get output
output = subprocess.check_output(["command", "arg1", "arg2"], text=True)
print(output)
```

```powershell
# PowerShell (Windows)
$output = & command arg1 arg2
```

```bash
# Bash (Linux/macOS)
output=$(command arg1 arg2)
```

### Setting Environment Variables for Child Processes

```python
# Python (cross-platform)
import subprocess
import os

env = os.environ.copy()
env["VARIABLE_NAME"] = "value"

subprocess.run(["command", "arg1", "arg2"], env=env)
```

```powershell
# PowerShell (Windows)
$env:VARIABLE_NAME = "value"
& command arg1 arg2
```

```bash
# Bash (Linux/macOS)
VARIABLE_NAME="value" command arg1 arg2
```

## Platform-Specific Code

Sometimes you need to write platform-specific code. Use the `platform` or `sys` module to detect the platform:

```python
import platform
import sys

if platform.system() == "Windows":
    # Windows-specific code
elif platform.system() == "Linux":
    # Linux-specific code
elif platform.system() == "Darwin":  # macOS
    # macOS-specific code
else:
    # Default code

# Alternative approach
if sys.platform.startswith("win"):
    # Windows-specific code
elif sys.platform.startswith("linux"):
    # Linux-specific code
elif sys.platform.startswith("darwin"):
    # macOS-specific code
else:
    # Default code
```

## Testing on Multiple Platforms

To ensure cross-platform compatibility:

1. **Use CI/CD pipelines that test on multiple platforms**:
   - GitHub Actions, Azure Pipelines, and other CI/CD services support multi-platform testing
   - Configure your CI/CD pipeline to run tests on Windows, Linux, and macOS

2. **Use Docker for testing**:
   - Docker can help simulate different environments
   - Use Docker containers to test on different Linux distributions

3. **Use virtual machines**:
   - Virtual machines can provide a more complete testing environment
   - Tools like VirtualBox, VMware, or Hyper-V can be used to create VMs for testing

## Documentation

Document platform-specific requirements and behaviors:

1. **System requirements**:
   - Document minimum OS versions
   - Document required dependencies for each platform

2. **Installation instructions**:
   - Provide platform-specific installation instructions
   - Document any platform-specific configuration

3. **Known issues**:
   - Document any known platform-specific issues
   - Provide workarounds for platform-specific issues

## Best Practices for Berrys_AgentsV2

1. **Use the shared utilities**:
   - The `shared/utils` package contains cross-platform utilities
   - Use these utilities instead of writing platform-specific code

2. **Follow the project's conventions**:
   - Use the same directory structure on all platforms
   - Use the same naming conventions on all platforms

3. **Use Docker for development**:
   - Docker provides a consistent development environment
   - Docker containers can help isolate platform-specific issues

4. **Document platform-specific requirements**:
   - Update the documentation when adding platform-specific code
   - Document any platform-specific configuration

5. **Test on all target platforms**:
   - Test your changes on all target platforms before submitting a pull request
   - Use the CI/CD pipeline to verify cross-platform compatibility
