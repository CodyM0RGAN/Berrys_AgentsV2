# Service Migration Guide

This guide provides instructions on how to migrate a service to a new environment.

## Prerequisites

- Access to the source and target environments
- Necessary credentials for database and other services
- Docker and Docker Compose installed

## Steps

1.  **Backup the database**:
    -   Create a backup of the source database.

2.  **Copy the application code**:
    -   Copy the application code to the target environment.

3.  **Configure the environment**:
    -   Set the necessary environment variables in the target environment.
        -   `DATABASE_URL` or `ASYNC_DATABASE_URL`: Database connection string.
        -   `DB_USER`: Database username.
        -   `DB_PASSWORD`: Database password.
        -   `DB_HOST`: Database host.
        -   `DB_PORT`: Database port.
        -   `REDIS_URL`: Redis connection string.
        -   `JWT_SECRET`: JWT secret key.
        -   `ENVIRONMENT`: Environment name (DEVELOPMENT, TEST, PRODUCTION).
    -   Ensure that the environment variables are set correctly for the target environment.

4.  **Restore the database**:
    -   Create a new database in the target environment.
    -   Restore the database backup to the new database.

5.  **Update the service configuration**:
    -   Update the service configuration to point to the new database.
    -   Update any other service dependencies.

6.  **Build the Docker image**:
    -   Build the Docker image for the service in the target environment.

7.  **Run the service**:
    -   Run the service in the target environment using Docker Compose.

8.  **Test the service**:
    -   Test the service to ensure that it is working correctly.
    -   Verify that the service can connect to the database.
    -   Verify that the service can communicate with other services.

## Database Connections

When migrating a service, ensure that the database connection is properly configured in the new environment. This involves:

- Setting the `ASYNC_DATABASE_URL` or `SYNC_DATABASE_URL` environment variable to the correct database connection string
- Ensuring that the database user has the necessary permissions to access the database
- Verifying that the database server is accessible from the service

If you are not using the `ASYNC_DATABASE_URL` or `SYNC_DATABASE_URL` environment variables, you will need to set the following environment variables:

- `DB_USER`: Database username
- `DB_PASSWORD`: Database password
- `DB_HOST`: Database host
- `DB_PORT`: Database port
- `DB_NAME`: Database name

## Verification

After migrating the service, verify that it is working correctly by:

- Checking the service logs for errors
- Testing the service's API endpoints
- Monitoring the service's performance

## Troubleshooting

If you encounter any issues during the migration process, consult the troubleshooting guide for assistance.
