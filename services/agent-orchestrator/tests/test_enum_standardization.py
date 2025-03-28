"""
Tests for enum standardization in the Agent Orchestrator service.
"""

import pytest
import uuid
import sys
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import from src and shared modules
from src.models.internal import AgentModel, Base
from src.models.enums import AgentStateDetail
from shared.models.src.enums import AgentStatus, AgentType


class TestEnumStandardization:
    """Tests for enum standardization."""
    
    @pytest.fixture
    def db_session(self):
        """Create a test database session."""
        # Create an in-memory SQLite database for testing
        engine = create_engine('sqlite:///:memory:')
        
        # Create all tables
        Base.metadata.create_all(engine)
        
        # Create a session
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        
        yield session
        
        # Clean up
        session.close()
    
    def test_create_with_enum_instance(self, db_session):
        """Test creating an agent with enum instances."""
        # Create an agent with enum instances
        agent = AgentModel(
            name="Test Agent",
            type=AgentType.DEVELOPER,
            status=AgentStatus.ACTIVE,
            state_detail=AgentStateDetail.READY,
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
        assert db_agent.status == AgentStatus.ACTIVE.value
        assert db_agent.state_detail == AgentStateDetail.READY.value
    
    def test_create_with_valid_string(self, db_session):
        """Test creating an agent with valid string values."""
        # Create an agent with string values
        agent = AgentModel(
            name="Test Agent",
            type="DEVELOPER",
            status="ACTIVE",
            state_detail="READY",
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
        assert db_agent.status == "ACTIVE"
        assert db_agent.state_detail == "READY"
    
    def test_create_with_invalid_value(self, db_session):
        """Test creating an agent with invalid enum values (should raise ValueError)."""
        # Create an agent with invalid values
        with pytest.raises(ValueError) as excinfo:
            agent = AgentModel(
                name="Test Agent",
                type="INVALID_TYPE",  # invalid
                status=AgentStatus.ACTIVE,
                project_id=uuid.uuid4()
            )
            
            # Try to add to session and commit
            db_session.add(agent)
            db_session.commit()
        
        # Verify error message
        assert "Invalid value 'INVALID_TYPE' for enum AgentType" in str(excinfo.value)
