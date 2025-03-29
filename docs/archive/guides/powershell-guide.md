# PowerShell Best Practices Guide

This guide provides best practices for working with PowerShell in the Berrys_AgentsV2 project, particularly focusing on Windows-specific considerations and common pitfalls that AI agents might encounter.

## Quick Reference

- Use semicolons (`;`) to separate commands, not ampersands (`&&`)
- Use backticks (`` ` ``) for line continuation, not backslashes (`\`)
- Use `$env:VARIABLE` for environment variables, not `$VARIABLE`
- Use `-eq`, `-ne`, `-gt`, etc. for comparisons, not `==`, `!=`, `>`
- Use `Join-Path` for path construction, not string concatenation
- Use `$PSScriptRoot` to reference the script's directory

## Command Syntax

### Command Separators

In PowerShell, commands are separated by semicolons (`;`), not ampersands (`&&`) as in Bash or CMD.

```powershell
# Correct
Get-ChildItem; Write-Host "Done"

# Incorrect (Bash/CMD style)
Get-ChildItem && Write-Host "Done"
```

For conditional execution based on success/failure:

```powershell
# Execute second command only if first succeeds
Get-ChildItem; if ($?) { Write-Host "Success" }

# Execute second command only if first fails
Get-ChildItem; if (-not $?) { Write-Host "Failed" }
```

### Line Continuation

PowerShell uses backticks (`` ` ``) for line continuation, not backslashes (`\`).

```powershell
# Correct
Get-ChildItem `
    -Path C:\Users `
    -Recurse

# Incorrect (Bash style)
Get-ChildItem \
    -Path C:\Users \
    -Recurse
```

Alternatively, natural line breaks work within parentheses, brackets, and braces:

```powershell
# Natural line breaks within parentheses
Get-ChildItem -Path (
    "C:\Users",
    "C:\Program Files"
)
```

## Path Handling

### Path Separators

PowerShell accepts both forward slashes (`/`) and backslashes (`\`) as path separators, but backslashes are the Windows standard.

```powershell
# Both work in PowerShell
Get-ChildItem -Path C:\Users\Administrator
Get-ChildItem -Path C:/Users/Administrator
```

### Path Construction

Use `Join-Path` for path construction instead of string concatenation:

```powershell
# Correct
$path = Join-Path -Path "C:\Users" -ChildPath "Administrator"

# Avoid
$path = "C:\Users" + "\Administrator"  # Could result in double backslash
$path = "C:\Users\Administrator"  # Hardcoded paths are less flexible
```

### Current Script Path

Use `$PSScriptRoot` to reference the directory containing the current script:

```powershell
# Get a file in the same directory as the script
$configPath = Join-Path -Path $PSScriptRoot -ChildPath "config.json"
```

## Variables and Environment

### Environment Variables

Access environment variables using the `$env:` prefix:

```powershell
# Correct
$username = $env:USERNAME

# Incorrect (Bash style)
$username = $USERNAME
```

### Variable Assignment

PowerShell uses `=` for variable assignment:

```powershell
# Correct
$name = "John"

# No need for export keyword (Bash style)
# export name="John"  # This doesn't work in PowerShell
```

## Comparison Operators

PowerShell uses different comparison operators than most other languages:

```powershell
# Equality
if ($a -eq $b) { ... }  # Not: if ($a == $b)

# Inequality
if ($a -ne $b) { ... }  # Not: if ($a != $b)

# Greater than
if ($a -gt $b) { ... }  # Not: if ($a > $b)

# Less than
if ($a -lt $b) { ... }  # Not: if ($a < $b)

# Greater than or equal
if ($a -ge $b) { ... }  # Not: if ($a >= $b)

# Less than or equal
if ($a -le $b) { ... }  # Not: if ($a <= $b)
```

## Error Handling

### Try-Catch Blocks

Use try-catch blocks for error handling:

```powershell
try {
    # Code that might throw an error
    $result = Invoke-RestMethod -Uri "https://api.example.com"
}
catch {
    # Error handling
    Write-Error "API call failed: $_"
}
finally {
    # Cleanup code that runs regardless of success/failure
    Write-Host "Operation completed"
}
```

### Error Preference

Control how PowerShell responds to errors:

```powershell
# Stop on any error (recommended for scripts)
$ErrorActionPreference = "Stop"

# Or specify for individual commands
Get-ChildItem -Path "C:\NonExistentFolder" -ErrorAction Stop
```

## File Operations

### Check If File Exists

```powershell
if (Test-Path -Path "C:\path\to\file.txt") {
    # File exists
}
```

### Create Directory If Not Exists

```powershell
if (-not (Test-Path -Path "C:\path\to\directory")) {
    New-Item -Path "C:\path\to\directory" -ItemType Directory
}
```

### Read File Content

```powershell
$content = Get-Content -Path "C:\path\to\file.txt"
```

### Write File Content

```powershell
Set-Content -Path "C:\path\to\file.txt" -Value "File content"
```

## Process Management

### Start Process

```powershell
# Start a process
Start-Process -FilePath "notepad.exe" -ArgumentList "C:\path\to\file.txt"
```

### Wait for Process

```powershell
# Start a process and wait for it to complete
$process = Start-Process -FilePath "python" -ArgumentList "script.py" -PassThru
$process.WaitForExit()
```

## Common Pitfalls for AI Agents

### 1. Absolute vs. Relative Paths

Always use absolute paths in scripts that might run from different working directories:

```powershell
# Correct
$configPath = Join-Path -Path $PSScriptRoot -ChildPath "config.json"

# Problematic (depends on working directory)
$configPath = ".\config.json"
```

### 2. String Quoting

PowerShell has different rules for single and double quotes:

```powershell
# Double quotes allow variable expansion
$name = "John"
Write-Host "Hello, $name"  # Outputs: Hello, John

# Single quotes are literal
Write-Host 'Hello, $name'  # Outputs: Hello, $name
```

### 3. Parameter Syntax

PowerShell uses named parameters with dashes:

```powershell
# Correct
Get-ChildItem -Path "C:\Users" -Recurse

# Incorrect (Bash/Unix style)
# Get-ChildItem --path "C:\Users" --recurse
```

### 4. Script Execution Policy

PowerShell has an execution policy that might prevent scripts from running:

```powershell
# Check current execution policy
Get-ExecutionPolicy

# Set execution policy (requires admin)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 5. Command Output Handling

PowerShell commands return objects, not text:

```powershell
# This captures objects, not text
$files = Get-ChildItem

# Access properties of the objects
foreach ($file in $files) {
    Write-Host $file.Name
}
```

## PowerShell vs. CMD

PowerShell and CMD have different commands for similar operations:

| Operation | PowerShell | CMD |
|-----------|------------|-----|
| List files | `Get-ChildItem` or `dir` | `dir` |
| Change directory | `Set-Location` or `cd` | `cd` |
| Copy file | `Copy-Item` | `copy` |
| Move file | `Move-Item` | `move` |
| Delete file | `Remove-Item` | `del` |
| Create directory | `New-Item -ItemType Directory` | `mkdir` |
| Clear screen | `Clear-Host` or `cls` | `cls` |
| Show help | `Get-Help` | `help` |

## PowerShell in Berrys_AgentsV2

### Running Scripts

To run PowerShell scripts in the project:

```powershell
# From PowerShell
.\scripts\setup-dev.ps1

# From CMD
powershell -ExecutionPolicy Bypass -File scripts\setup-dev.ps1
```

### Environment Setup

The project includes PowerShell scripts for environment setup:

```powershell
# Set up development environment
.\setup-env.ps1

# Run tests
.\run_tests.ps1
```

## Conclusion

Following these PowerShell best practices will help ensure that scripts work correctly on Windows systems and avoid common pitfalls. Remember that PowerShell is object-oriented and has different syntax than Bash or CMD, so scripts need to be written specifically for PowerShell rather than adapted from other shells.
