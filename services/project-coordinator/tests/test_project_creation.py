"""
Test script for project creation with status field.

This script tests that the ProjectCreateRequest model correctly handles the status field.
"""
import pytest
from uuid import UUID

from src.models.api import ProjectCreateRequest
from shared.models.src.project import ProjectStatus


def test_project_create_request_with_status():
    """Test that ProjectCreateRequest accepts a status field."""
    # Create a project with status field
    project_data = ProjectCreateRequest(
        name="Test Project",
        description="A test project",
        status=ProjectStatus.PLANNING
    )
    
    # Verify that the status field is set correctly
    assert project_data.status == ProjectStatus.PLANNING


def test_project_create_request_without_status():
    """Test that ProjectCreateRequest works without a status field."""
    # Create a project without status field
    project_data = ProjectCreateRequest(
        name="Test Project",
        description="A test project"
    )
    
    # Verify that the status field is None
    assert project_data.status is None


def test_create_project_api_with_status(client):
    """Test creating a project via API with status field."""
    # Create a project with status field
    response = client.post(
        "/projects/",
        json={
            "name": "Test Project",
            "description": "A test project",
            "status": "PLANNING"
        }
    )
    
    # Verify that the project was created successfully
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Project"
    assert data["description"] == "A test project"
    assert data["status"] == "PLANNING"


def test_create_project_api_without_status(client):
    """Test creating a project via API without status field."""
    # Create a project without status field
    response = client.post(
        "/projects/",
        json={
            "name": "Test Project",
            "description": "A test project"
        }
    )
    
    # Verify that the project was created successfully
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Project"
    assert data["description"] == "A test project"
    # Default status should be DRAFT
    assert data["status"] == "DRAFT"
