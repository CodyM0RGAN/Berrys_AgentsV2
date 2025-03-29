"""
Centralized UUID Type Implementation

This template provides the implementation for a centralized UUID type that can be used
across all services. It is extracted from the Model Orchestration service and enhanced
for cross-database compatibility.

Usage:
1. Add this implementation to shared/utils/src/database.py
2. Update services to use this centralized implementation
3. Remove any service-specific UUID type implementations
"""

from sqlalchemy import TypeDecorator, String
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
import uuid


class UUID(TypeDecorator):
    """Platform-independent UUID type.
    
    Uses PostgreSQL's UUID type when available, otherwise uses String(36).
    This implementation ensures consistent UUID handling across different database backends.
    
    Attributes:
        impl: The SQLAlchemy type to use as the base implementation
        cache_ok: Whether this type is safe to cache
        as_uuid: Whether to return Python uuid.UUID objects or strings
    
    Example:
        ```python
        class MyModel(Base):
            __tablename__ = 'my_model'
            
            id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
            related_id = Column(UUID(as_uuid=True), ForeignKey('other_model.id'))
        ```
    """
    impl = String
    cache_ok = True

    def __init__(self, as_uuid=True):
        """Initialize the UUID type.
        
        Args:
            as_uuid: Whether to return Python uuid.UUID objects (True) or strings (False)
        """
        self.as_uuid = as_uuid
        super().__init__()

    def load_dialect_impl(self, dialect):
        """Load the dialect-specific implementation.
        
        Uses PostgreSQL's native UUID type when available, otherwise falls back to String(36).
        
        Args:
            dialect: The SQLAlchemy dialect
            
        Returns:
            The dialect-specific type implementation
        """
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PostgresUUID())
        else:
            return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        """Process the value before binding to a statement.
        
        Converts UUID objects to strings for non-PostgreSQL databases.
        
        Args:
            value: The value to bind
            dialect: The SQLAlchemy dialect
            
        Returns:
            The processed value
        """
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            if isinstance(value, uuid.UUID):
                return str(value)
            return value

    def process_result_value(self, value, dialect):
        """Process the value retrieved from the database.
        
        Converts string UUIDs to UUID objects if as_uuid=True.
        
        Args:
            value: The value from the database
            dialect: The SQLAlchemy dialect
            
        Returns:
            The processed value
        """
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            if not isinstance(value, uuid.UUID) and self.as_uuid and value is not None:
                try:
                    return uuid.UUID(value)
                except (ValueError, TypeError):
                    return value
            return value


# Example usage
def example_usage():
    """Example of how to use the UUID type."""
    from sqlalchemy import Column, ForeignKey, create_engine
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import relationship, sessionmaker
    
    Base = declarative_base()
    
    class Parent(Base):
        __tablename__ = 'parent'
        
        id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        name = Column(String(50), nullable=False)
        
        children = relationship("Child", back_populates="parent")
    
    class Child(Base):
        __tablename__ = 'child'
        
        id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        name = Column(String(50), nullable=False)
        parent_id = Column(UUID(as_uuid=True), ForeignKey('parent.id'))
        
        parent = relationship("Parent", back_populates="children")
    
    # Create engine and tables
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    
    # Create session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Create parent
    parent = Parent(name="Parent 1")
    session.add(parent)
    session.commit()
    
    # Create child
    child = Child(name="Child 1", parent=parent)
    session.add(child)
    session.commit()
    
    # Query
    result = session.query(Child).filter(Child.parent_id == parent.id).first()
    print(f"Found child: {result.name}, parent: {result.parent.name}")
    
    # Clean up
    session.close()
