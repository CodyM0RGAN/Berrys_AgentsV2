"""
Contract tests for the agent-orchestrator service.

This module tests the contracts between the agent-orchestrator service
and other services it interacts with, ensuring all API interactions conform
to the defined contracts.
"""

import json
import pytest
from unittest.mock import patch

from shared.utils.src.testing.contract import (
    ContractDefinition,
    ContractRegistry,
    ContractVerifier
)

# Define contracts between agent-orchestrator and other services
# These would typically be loaded from a central repository
CONTRACTS = [
    # Contract with model-orchestration service
    {
        "consumer": "agent-orchestrator",
        "provider": "model-orchestration",
        "endpoint": "/v1/models/generate",
        "method": "POST",
        "request": {
            "type": "object",
            "properties": {
                "model": {"type": "string"},
                "prompt": {"type": "string"},
                "max_tokens": {"type": "integer"},
                "temperature": {"type": "number"},
                "top_p": {"type": "number"},
                "frequency_penalty": {"type": "number"},
                "presence_penalty": {"type": "number"},
                "stop": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["model", "prompt"]
        },
        "response": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "model": {"type": "string"},
                "choices": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string"},
                            "index": {"type": "integer"},
                            "finish_reason": {"type": "string"}
                        }
                    }
                },
                "usage": {
                    "type": "object",
                    "properties": {
                        "prompt_tokens": {"type": "integer"},
                        "completion_tokens": {"type": "integer"},
                        "total_tokens": {"type": "integer"}
                    }
                }
            }
        }
    },
    # Contract with project-coordinator service
    {
        "consumer": "agent-orchestrator",
        "provider": "project-coordinator",
        "endpoint": "/v1/projects/{project_id}",
        "method": "GET",
        "response": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string"},
                "description": {"type": "string"},
                "status": {"type": "string"},
                "created_at": {"type": "string", "format": "date-time"},
                "updated_at": {"type": "string", "format": "date-time"}
            },
            "required": ["id", "name", "status"]
        }
    }
]


class TestContractValidation:
    """Test contract validation between services."""
    
    @pytest.fixture
    def contract_registry(self):
        """Create a contract registry with predefined contracts."""
        registry = ContractRegistry()
        
        for contract_dict in CONTRACTS:
            contract = ContractDefinition.from_dict(contract_dict)
            registry.register_contract(contract)
            
        return registry
        
    @pytest.fixture
    def contract_verifier(self, contract_registry):
        """Create a contract verifier with the contract registry."""
        return ContractVerifier(contract_registry)
        
    def test_model_orchestration_contract_request(self, contract_verifier):
        """Test that requests to model-orchestration conform to the contract."""
        # Example request data
        request_data = {
            "model": "gpt-4",
            "prompt": "Generate a story about a robot learning to paint.",
            "max_tokens": 500,
            "temperature": 0.7,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
            "stop": ["\n\n"]
        }
        
        # Verify request
        validated_data = contract_verifier.verify_request(
            consumer_name="agent-orchestrator",
            provider_name="model-orchestration",
            endpoint="/v1/models/generate",
            method="POST",
            request_data=request_data
        )
        
        # Should not raise any validation errors
        assert validated_data is not None
        
    def test_model_orchestration_contract_response(self, contract_verifier):
        """Test that responses from model-orchestration conform to the contract."""
        # Example response data
        response_data = {
            "id": "gen-123456",
            "model": "gpt-4",
            "choices": [
                {
                    "text": "The robot picked up the brush...",
                    "index": 0,
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 15,
                "completion_tokens": 42,
                "total_tokens": 57
            }
        }
        
        # Verify response
        validated_data = contract_verifier.verify_response(
            consumer_name="agent-orchestrator",
            provider_name="model-orchestration",
            endpoint="/v1/models/generate",
            method="POST",
            response_data=response_data
        )
        
        # Should not raise any validation errors
        assert validated_data is not None
        
    def test_project_coordinator_contract_response(self, contract_verifier):
        """Test that responses from project-coordinator conform to the contract."""
        # Example response data
        response_data = {
            "id": "project-123",
            "name": "Test Project",
            "description": "A test project",
            "status": "ACTIVE",
            "created_at": "2025-03-15T12:00:00Z",
            "updated_at": "2025-03-15T14:30:00Z"
        }
        
        # Verify response
        validated_data = contract_verifier.verify_response(
            consumer_name="agent-orchestrator",
            provider_name="project-coordinator",
            endpoint="/v1/projects/{project_id}",
            method="GET",
            response_data=response_data
        )
        
        # Should not raise any validation errors
        assert validated_data is not None
        

@patch('requests.post')
def test_model_orchestration_api_conformance(mock_post, contract_registry):
    """Test that the model-orchestration API client conforms to the contract."""
    from src.services.model_client import ModelClient  # Import the service client
    
    # Create a contract verifier with the contract registry
    verifier = ContractVerifier(contract_registry)
    
    # Set up mock response
    mock_response = {
        "id": "gen-123456",
        "model": "gpt-4",
        "choices": [
            {
                "text": "The robot picked up the brush...",
                "index": 0,
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 15,
            "completion_tokens": 42,
            "total_tokens": 57
        }
    }
    
    mock_post.return_value.json.return_value = mock_response
    mock_post.return_value.status_code = 200
    
    # Create client and call API
    client = ModelClient()
    response = client.generate_text(
        model="gpt-4",
        prompt="Generate a story about a robot learning to paint.",
        max_tokens=500
    )
    
    # Check that the request conforms to the contract
    called_args = mock_post.call_args
    url = called_args[0][0]
    assert url.endswith('/v1/models/generate')
    
    request_json = called_args[1]['json']
    
    # Verify request against contract
    try:
        verifier.verify_request(
            consumer_name="agent-orchestrator",
            provider_name="model-orchestration",
            endpoint="/v1/models/generate",
            method="POST",
            request_data=request_json
        )
    except Exception as e:
        pytest.fail(f"Request does not match contract: {e}")
        
    # Verify response against contract
    try:
        verifier.verify_response(
            consumer_name="agent-orchestrator",
            provider_name="model-orchestration", 
            endpoint="/v1/models/generate",
            method="POST",
            response_data=response
        )
    except Exception as e:
        pytest.fail(f"Response does not match contract: {e}")
