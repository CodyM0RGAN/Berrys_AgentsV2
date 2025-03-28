import pytest
from httpx import AsyncClient
from uuid import UUID, uuid4
import json
from typing import Dict, Any


@pytest.mark.asyncio
async def test_create_template(client: AsyncClient):
    """
    Test creating an agent template.
    """
    # Prepare template data
    template_data = {
        "id": f"test_template_{uuid4().hex[:8]}",
        "name": "Test Template",
        "description": "A test template created via API",
        "agent_type": "RESEARCHER",
        "configuration_schema": {
            "type": "object",
            "properties": {
                "key1": {"type": "string"},
                "key2": {"type": "number"}
            },
            "required": ["key1"]
        },
        "default_configuration": {
            "key1": "default-value",
            "key2": 50
        },
        "prompt_template": "You are a {{agent_type}} agent named {{name}}."
    }
    
    # Send request
    response = await client.post("/api/templates", json=template_data)
    
    # Check response
    assert response.status_code == 201
    data = response.json()
    
    # Validate response data
    assert data["id"] == template_data["id"]
    assert data["name"] == template_data["name"]
    assert data["description"] == template_data["description"]
    assert data["agent_type"] == template_data["agent_type"]
    assert data["configuration_schema"] == template_data["configuration_schema"]
    assert data["default_configuration"] == template_data["default_configuration"]
    assert data["prompt_template"] == template_data["prompt_template"]
    
    return data


@pytest.mark.asyncio
async def test_get_template(client: AsyncClient, agent_template: Dict[str, Any]):
    """
    Test getting a template by ID.
    """
    # Send request
    response = await client.get(f"/api/templates/{agent_template['id']}")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    
    # Validate response data
    assert data["id"] == agent_template["id"]
    assert data["name"] == agent_template["name"]
    assert data["description"] == agent_template["description"]
    assert data["agent_type"] == agent_template["agent_type"]


@pytest.mark.asyncio
async def test_list_templates(client: AsyncClient, agent_template: Dict[str, Any]):
    """
    Test listing templates.
    """
    # Send request
    response = await client.get("/api/templates")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    
    # Validate response data
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert data["total"] >= 1
    
    # Check if our template is in the list
    template_ids = [item["id"] for item in data["items"]]
    assert agent_template["id"] in template_ids


@pytest.mark.asyncio
async def test_update_template(client: AsyncClient):
    """
    Test updating a template.
    """
    # First create a template
    template = await test_create_template(client)
    
    # Prepare update data
    update_data = {
        "name": "Updated Template Name",
        "description": "Updated description",
        "default_configuration": {
            "key1": "updated-value",
            "key3": "new-value"
        }
    }
    
    # Send request
    response = await client.put(f"/api/templates/{template['id']}", json=update_data)
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    
    # Validate response data
    assert data["id"] == template["id"]
    assert data["name"] == update_data["name"]
    assert data["description"] == update_data["description"]
    
    # Check if default_configuration was merged correctly
    assert data["default_configuration"]["key1"] == "updated-value"
    assert data["default_configuration"]["key2"] == 50  # Original value
    assert data["default_configuration"]["key3"] == "new-value"  # New value
    
    # Other fields should remain unchanged
    assert data["agent_type"] == template["agent_type"]
    assert data["configuration_schema"] == template["configuration_schema"]
    assert data["prompt_template"] == template["prompt_template"]


@pytest.mark.asyncio
async def test_template_validation(client: AsyncClient):
    """
    Test template validation.
    """
    # Prepare invalid template data (missing required name)
    invalid_template = {
        "id": f"invalid_template_{uuid4().hex[:8]}",
        "description": "An invalid template",
        "agent_type": "RESEARCHER",
        "configuration_schema": {
            "type": "object",
            "properties": {
                "key1": {"type": "string"}
            },
            "required": ["key1"]
        },
        "default_configuration": {
            "key2": "value"  # Missing required key1
        }
    }
    
    # Send request
    response = await client.post("/api/templates", json=invalid_template)
    
    # Check response (should be error)
    assert response.status_code == 400
    data = response.json()
    
    # Error message should mention validation
    assert "validation" in data["detail"].lower() or "invalid" in data["detail"].lower()


@pytest.mark.asyncio
async def test_delete_template(client: AsyncClient):
    """
    Test deleting a template.
    """
    # First create a template
    template = await test_create_template(client)
    
    # Send delete request
    response = await client.delete(f"/api/templates/{template['id']}")
    
    # Check response
    assert response.status_code == 204
    
    # Verify template is deleted
    get_response = await client.get(f"/api/templates/{template['id']}")
    assert get_response.status_code == 404
