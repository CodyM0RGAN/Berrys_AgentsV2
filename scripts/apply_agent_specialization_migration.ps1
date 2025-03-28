# Apply agent specialization migration script
# This script applies the agent specialization migration to the database

# Get environment variables from .env file
$envFile = ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match "^\s*([^#][^=]+)=(.*)$") {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($key, $value, "Process")
        }
    }
}

# Set default values if not in .env
if (-not $env:DB_USER) { $env:DB_USER = "postgres" }
if (-not $env:DB_PASSWORD) { $env:DB_PASSWORD = "postgres" }
if (-not $env:DB_NAME) { $env:DB_NAME = "mas_framework" }
# Always use localhost for the host when running outside Docker
$env:DB_HOST = "localhost"
if (-not $env:DB_PORT) { $env:DB_PORT = "5432" }

# Set PGPASSWORD environment variable for psql
$env:PGPASSWORD = $env:DB_PASSWORD

# Display migration information
Write-Host "Applying agent specialization migration to database $env:DB_NAME on $env:DB_HOST"

# Execute the migration script
try {
    psql -h $env:DB_HOST -U $env:DB_USER -d $env:DB_NAME -f shared/database/agent_specialization_migration.sql
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Migration applied successfully" -ForegroundColor Green
    }
    else {
        Write-Host "Error applying migration" -ForegroundColor Red
        exit 1
    }
}
catch {
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}
