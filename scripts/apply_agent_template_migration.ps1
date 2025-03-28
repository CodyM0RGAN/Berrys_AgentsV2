# Apply Agent Template Migration Script
# This script applies the agent_template_migration.sql script to the database.

# Set the current directory to the script directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -Path $scriptPath

# Get the project root directory
$projectRoot = Split-Path -Parent $scriptPath

# Set the path to the migration script
$migrationScriptPath = Join-Path -Path $projectRoot -ChildPath "shared\database\agent_template_migration.sql"

# Check if the migration script exists
if (-not (Test-Path $migrationScriptPath)) {
    Write-Error "Migration script not found at $migrationScriptPath"
    exit 1
}

# Load environment variables from .env file
$envFile = Join-Path -Path $projectRoot -ChildPath ".env"
if (Test-Path $envFile) {
    Write-Host "Loading environment variables from .env file..."
    Get-Content $envFile | ForEach-Object {
        if ($_ -match "^\s*([^#][^=]+)=(.*)$") {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            # Remove quotes if present
            if ($value -match '^"(.*)"$' -or $value -match "^'(.*)'$") {
                $value = $matches[1]
            }
            # Set environment variable
            [Environment]::SetEnvironmentVariable($key, $value, "Process")
            Write-Host "Set $key environment variable"
        }
    }
}

# Get database connection parameters from environment variables
$dbHost = $env:DB_HOST
$dbPort = $env:DB_PORT
$dbName = $env:DB_NAME
$dbUser = $env:DB_USER
$dbPassword = $env:DB_PASSWORD

# Validate required environment variables
if (-not $dbHost -or -not $dbPort -or -not $dbName -or -not $dbUser -or -not $dbPassword) {
    Write-Error "Missing required database environment variables. Please check your .env file."
    Write-Host "Required variables: DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD"
    exit 1
}

# If DB_HOST is "postgres" (Docker service name), use "localhost" for local execution
if ($dbHost -eq "postgres") {
    Write-Host "Converting Docker service name 'postgres' to 'localhost' for local execution..."
    $dbHost = "localhost"
}

# Construct the connection string
$connectionString = "host=$dbHost port=$dbPort dbname=$dbName user=$dbUser password=$dbPassword"

# Apply the migration script
Write-Host "Applying Agent Template migration script to database $dbName on $dbHost..."
try {
    # Check if psql is available
    $psqlPath = Get-Command psql -ErrorAction SilentlyContinue
    if ($null -eq $psqlPath) {
        Write-Error "psql command not found. Please ensure PostgreSQL is installed and added to your PATH."
        exit 1
    }

    # Apply the migration script using psql
    $env:PGPASSWORD = $dbPassword
    & psql -h $dbHost -p $dbPort -d $dbName -U $dbUser -f $migrationScriptPath
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to apply migration script. Exit code: $LASTEXITCODE"
        exit 1
    }
    
    Write-Host "Migration script applied successfully."
}
catch {
    Write-Error "Error applying migration script: $_"
    exit 1
}
finally {
    # Clear the password from environment
    $env:PGPASSWORD = ""
}

# Return to the original directory
Set-Location -Path $projectRoot

Write-Host "Agent Template migration completed successfully."
