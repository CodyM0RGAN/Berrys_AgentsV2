# Service Standardization Templates

This directory contains templates and examples to help implement the service standardization plan. These templates provide starting points for common standardization tasks and demonstrate best practices for consistent implementation across services.

## Available Templates

### 1. Database Migration Templates

- **[enum_standardization_migration.py](enum_standardization_migration.py)**: Template for creating Alembic migrations to standardize enum values in a service's database. Includes table renaming, adding check constraints, and converting data from lowercase to uppercase.

### 2. Model Update Templates

- **[enum_model_update_template.py](enum_model_update_template.py)**: Template for updating SQLAlchemy models to use standardized enum handling. Shows before and after versions of a model class to illustrate the changes needed.

- **[enum_api_model_update_template.py](enum_api_model_update_template.py)**: Template for updating Pydantic API models to use standardized enum handling. Shows before and after versions of model classes to illustrate the changes needed.

### 3. Testing Templates

- **[enum_validation_test_template.py](enum_validation_test_template.py)**: Template for testing enum validation in both SQLAlchemy and Pydantic models. Includes tests for various scenarios like valid/invalid values and case sensitivity.

### 4. Shared Component Templates

- **[uuid_type_implementation.py](uuid_type_implementation.py)**: Implementation for a centralized UUID type that can be used across all services. Extracted from the Model Orchestration service and enhanced for cross-database compatibility.

## How to Use These Templates

1. **For Database Migrations**:
   - Copy the migration template to your service's migrations/versions directory
   - Rename it with a timestamp and descriptive name
   - Customize the variables and SQL statements for your specific service
   - Run the migration using Alembic

2. **For Model Updates**:
   - Use the model templates as references when updating your service's models
   - Adapt the patterns to your specific model structure
   - Ensure all enum columns/fields are properly validated

3. **For Shared Components**:
   - Add the implementation to the appropriate shared directory
   - Update services to use the centralized implementation
   - Remove any service-specific implementations

## Best Practices

1. **Testing**:
   - Always test migrations in a development environment before applying to production
   - Write unit tests for updated models to verify validation logic
   - Test both success and failure cases

2. **Backward Compatibility**:
   - Add validators to handle both uppercase and lowercase values during the transition period
   - Issue deprecation warnings for lowercase values
   - Ensure API endpoints can handle both enum instances and string values

3. **Documentation**:
   - Document any changes to model interfaces
   - Update API documentation to reflect enum standardization
   - Add comments explaining validation logic

## Related Documentation

- [Service Standardization Plan](../service-standardization-plan.md): Comprehensive implementation plan
- [Service Standardization Assessment](../service-standardization-assessment.md): Detailed assessment of each service
- [Enum Standardization Guide](../enum_standardization.md): Detailed guide on enum standardization
- [Model Standardization Progress](../model-standardization-progress.md): Progress report on model standardization
