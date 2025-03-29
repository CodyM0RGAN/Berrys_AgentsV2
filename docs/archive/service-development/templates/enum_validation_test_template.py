"""
Enum Validation Test Template

This template provides examples of tests for verifying enum validation in models.
It includes tests for both SQLAlchemy models and Pydantic API models.

Usage:
1. Copy relevant test cases to your service's test directory
2. Adapt the tests to your specific model structure
3. Run the tests to verify that enum validation is working correctly
"""

import pytest
import uuid
import warnings
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Import your models and enums
from shared.models.src.enums import AgentType, AgentStatus
from your_service.src.models.internal import AgentModel  # SQLAlchemy model
from your_service.src.models.api import AgentCreate, AgentResponse  # Pydantic models

# ----------------------------------------------------------------------------------
# SQLAlchemy Model Tests
# ----------------------------------------------------------------------------------

class TestSQLAlchemyEnumValidation:
    """Tests for enum validation in SQLAlchemy models."""
    
    @pytest.fixture
    def db_session(self):
        """Create a test database session."""
        # Create an in-memory SQLite database for testing
        engine = create_engine('sqlite:///:memory:')
        
        # Create all tables
        from your_service.src.models.internal import Base
        Base.metadata.create_all(engine)
        
        # Create a session
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        
        yield session
        
        # Clean up
        session.close()
    
    def test_create_with_enum_instance(self, db_session: Session):
        """Test creating a model with enum instances."""
        # Create a model with enum instances
        agent = AgentModel(
            name="Test Agent",
            type=AgentType.DEVELOPER,
            status=AgentStatus.CREATED,
            project_id=uuid.uuid4()
        )
        
        # Add to session and commit
        db_session.add(agent)
        db_session.commit()
        
        # Retrieve from database
        db_agent = db_session.query(AgentModel).filter_by(name="Test Agent").first()
        
        # Verify
        assert db_agent is not None
        assert db_agent.type == AgentType.DEVELOPER.value
        assert db_agent.status == AgentStatus.CREATED.value
    
    def test_create_with_valid_string(self, db_session: Session):
        """Test creating a model with valid string values."""
        # Create a model with string values
        agent = AgentModel(
            name="Test Agent",
            type="DEVELOPER",
            status="CREATED",
            project_id=uuid.uuid4()
        )
        
        # Add to session and commit
        db_session.add(agent)
        db_session.commit()
        
        # Retrieve from database
        db_agent = db_session.query(AgentModel).filter_by(name="Test Agent").first()
        
        # Verify
        assert db_agent is not None
        assert db_agent.type == "DEVELOPER"
        assert db_agent.status == "CREATED"
    
    def test_create_with_lowercase_string(self, db_session: Session):
        """Test creating a model with lowercase string values (should be converted to uppercase)."""
        # Catch deprecation warnings
        with warnings.catch_warnings(record=True) as w:
            # Create a model with lowercase string values
            agent = AgentModel(
                name="Test Agent",
                type="developer",  # lowercase
                status="created",  # lowercase
                project_id=uuid.uuid4()
            )
            
            # Add to session and commit
            db_session.add(agent)
            db_session.commit()
            
            # Verify warnings were issued
            assert len(w) == 2
            assert issubclass(w[0].category, DeprecationWarning)
            assert issubclass(w[1].category, DeprecationWarning)
        
        # Retrieve from database
        db_agent = db_session.query(AgentModel).filter_by(name="Test Agent").first()
        
        # Verify values were converted to uppercase
        assert db_agent is not None
        assert db_agent.type == "DEVELOPER"
        assert db_agent.status == "CREATED"
    
    def test_create_with_invalid_value(self, db_session: Session):
        """Test creating a model with invalid enum values (should raise ValueError)."""
        # Create a model with invalid values
        with pytest.raises(ValueError) as excinfo:
            agent = AgentModel(
                name="Test Agent",
                type="INVALID_TYPE",  # invalid
                status=AgentStatus.CREATED,
                project_id=uuid.uuid4()
            )
            
            # Try to add to session and commit
            db_session.add(agent)
            db_session.commit()
        
        # Verify error message
        assert "Invalid value 'INVALID_TYPE' for enum AgentType" in str(excinfo.value)


# ----------------------------------------------------------------------------------
# Pydantic API Model Tests
# ----------------------------------------------------------------------------------

class TestPydanticEnumValidation:
    """Tests for enum validation in Pydantic API models."""
    
    def test_create_with_enum_instance(self):
        """Test creating a model with enum instances."""
        # Create a model with enum instances
        agent = AgentCreate(
            name="Test Agent",
            type=AgentType.DEVELOPER,
            project_id=uuid.uuid4()
        )
        
        # Verify
        assert agent.type == AgentType.DEVELOPER
    
    def test_create_with_valid_string(self):
        """Test creating a model with valid string values."""
        # Create a model with string values
        agent = AgentCreate(
            name="Test Agent",
            type="DEVELOPER",
            project_id=uuid.uuid4()
        )
        
        # Verify
        assert agent.type == AgentType.DEVELOPER
    
    def test_create_with_lowercase_string(self):
        """Test creating a model with lowercase string values (should be converted to enum)."""
        # Create a model with lowercase string values
        agent = AgentCreate(
            name="Test Agent",
            type="developer",  # lowercase
            project_id=uuid.uuid4()
        )
        
        # Verify values were converted to enum instances
        assert agent.type == AgentType.DEVELOPER
    
    def test_create_with_invalid_value(self):
        """Test creating a model with invalid enum values (should raise ValueError)."""
        # Create a model with invalid values
        with pytest.raises(ValueError) as excinfo:
            agent = AgentCreate(
                name="Test Agent",
                type="INVALID_TYPE",  # invalid
                project_id=uuid.uuid4()
            )
        
        # Verify error message contains validation error
        assert "validation error" in str(excinfo.value).lower()
    
    def test_model_serialization(self):
        """Test serializing a model with enum values."""
        # Create a response model
        agent = AgentResponse(
            id=uuid.uuid4(),
            name="Test Agent",
            type=AgentType.DEVELOPER,
            status=AgentStatus.CREATED,
            project_id=uuid.uuid4(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Convert to dictionary
        data = agent.model_dump()
        
        # Verify enum values are serialized as strings
        assert data["type"] == "DEVELOPER"
        assert data["status"] == "CREATED"
    
    def test_model_deserialization(self):
        """Test deserializing a model with enum values."""
        # Create a dictionary with string values
        data = {
            "id": str(uuid.uuid4()),
            "name": "Test Agent",
            "type": "DEVELOPER",
            "status": "CREATED",
            "project_id": str(uuid.uuid4()),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Convert to model
        agent = AgentResponse.model_validate(data)
        
        # Verify string values are converted to enum instances
        assert agent.type == AgentType.DEVELOPER
        assert agent.status == AgentStatus.CREATED


# ----------------------------------------------------------------------------------
# Integration Tests
# ----------------------------------------------------------------------------------

class TestEnumIntegration:
    """Integration tests for enum handling across model layers."""
    
    @pytest.fixture
    def db_session(self):
        """Create a test database session."""
        # Create an in-memory SQLite database for testing
        engine = create_engine('sqlite:///:memory:')
        
        # Create all tables
        from your_service.src.models.internal import Base
        Base.metadata.create_all(engine)
        
        # Create a session
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        
        yield session
        
        # Clean up
        session.close()
    
    def test_orm_to_api_conversion(self, db_session: Session):
        """Test converting from ORM model to API model."""
        # Create an ORM model
        agent_orm = AgentModel(
            name="Test Agent",
            type=AgentType.DEVELOPER,
            status=AgentStatus.CREATED,
            project_id=uuid.uuid4()
        )
        
        # Add to session and commit
        db_session.add(agent_orm)
        db_session.commit()
        db_session.refresh(agent_orm)
        
        # Convert to API model
        # This assumes you have a to_api_model method or similar
        agent_api = AgentResponse.model_validate(agent_orm)
        
        # Verify
        assert agent_api.name == agent_orm.name
        assert agent_api.type == AgentType.DEVELOPER
        assert agent_api.status == AgentStatus.CREATED
        assert str(agent_api.project_id) == str(agent_orm.project_id)
    
    def test_api_to_orm_conversion(self, db_session: Session):
        """Test converting from API model to ORM model."""
        # Create an API model
        agent_api = AgentCreate(
            name="Test Agent",
            type=AgentType.DEVELOPER,
            project_id=uuid.uuid4()
        )
        
        # Convert to ORM model
        # This assumes you have a from_api_model method or similar
        agent_orm = AgentModel(
            name=agent_api.name,
            type=agent_api.type.value,  # Convert enum to string
            status=AgentStatus.CREATED.value,  # Default value
            project_id=agent_api.project_id
        )
        
        # Add to session and commit
        db_session.add(agent_orm)
        db_session.commit()
        db_session.refresh(agent_orm)
        
        # Verify
        assert agent_orm.name == agent_api.name
        assert agent_orm.type == agent_api.type.value
        assert str(agent_orm.project_id) == str(agent_api.project_id)
