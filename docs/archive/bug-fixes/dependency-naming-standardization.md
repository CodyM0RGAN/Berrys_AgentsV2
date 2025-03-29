# Dependency Naming Standardization

## Issue: Inconsistent Database Session Dependency Names

We identified inconsistencies in database session dependency naming across different services in the project. Some services were using `get_db()` while others were using `get_db_session()` for the same functionality.

This inconsistency created several problems:
- Confusion during code reviews
- Potential errors when copying code between services
- Increased cognitive load when working across multiple services
- Inconsistent documentation

## Resolution

We've standardized all database dependency injection to use `get_db()` as the consistent function name across all services:

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Changes Made

1. Identified all instances of `get_db_session()` in the codebase
2. Replaced them with `get_db()` to maintain consistency
3. Updated SQLAlchemy documentation to reflect this standard
4. Added explicit guidance in documentation to use `get_db()` rather than alternatives

### Benefits

- Consistent API across services
- Easier knowledge transfer between services
- Reduced cognitive load when working with different services
- Clear standard for new code development

### Verification

We've verified this change in the following services:
- agent-orchestrator
- model-orchestration
- planning-system
- project-coordinator
- tool-integration

### Date Implemented

March 28, 2025
