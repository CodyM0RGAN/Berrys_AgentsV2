"""
Contract testing utilities for Berrys_AgentsV2.

This module provides utilities for contract testing between services, including:
- Creating contract definitions
- Verifying contracts between consumer and provider services
- Generating contract test reports
"""

import os
import json
import shutil
import tempfile
from typing import Dict, List, Any, Optional, Callable, Union, Type

import pytest
from pydantic import BaseModel, create_model, ValidationError


class ContractDefinition:
    """
    Definition of a contract between a consumer and provider.
    
    A contract defines the expected format of requests and responses
    between a consumer service and a provider service.
    """
    
    def __init__(
        self,
        consumer_name: str,
        provider_name: str,
        endpoint: str,
        method: str = "GET",
        request_schema: Optional[Type[BaseModel]] = None,
        response_schema: Optional[Type[BaseModel]] = None,
        description: Optional[str] = None
    ):
        """
        Initialize a contract definition.
        
        Args:
            consumer_name: Name of the consumer service.
            provider_name: Name of the provider service.
            endpoint: API endpoint path.
            method: HTTP method (default: "GET").
            request_schema: Pydantic model for request validation.
            response_schema: Pydantic model for response validation.
            description: Optional description of the contract.
        """
        self.consumer_name = consumer_name
        self.provider_name = provider_name
        self.endpoint = endpoint
        self.method = method.upper()
        self.request_schema = request_schema
        self.response_schema = response_schema
        self.description = description
        
    def validate_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a request against the contract.
        
        Args:
            request_data: Request data to validate.
            
        Returns:
            Validated request data.
            
        Raises:
            ValidationError: If the request does not match the contract.
        """
        if self.request_schema is None:
            return request_data
            
        model = self.request_schema.parse_obj(request_data)
        return model.dict()
        
    def validate_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a response against the contract.
        
        Args:
            response_data: Response data to validate.
            
        Returns:
            Validated response data.
            
        Raises:
            ValidationError: If the response does not match the contract.
        """
        if self.response_schema is None:
            return response_data
            
        model = self.response_schema.parse_obj(response_data)
        return model.dict()
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the contract to a dictionary.
        
        Returns:
            Dictionary representation of the contract.
        """
        request_schema = None
        if self.request_schema is not None:
            schema = self.request_schema.schema()
            # Remove validator information which isn't needed for contracts
            if "title" in schema and schema["title"] == self.request_schema.__name__:
                del schema["title"]
            request_schema = schema
            
        response_schema = None
        if self.response_schema is not None:
            schema = self.response_schema.schema()
            # Remove validator information which isn't needed for contracts
            if "title" in schema and schema["title"] == self.response_schema.__name__:
                del schema["title"]
            response_schema = schema
            
        return {
            "consumer": self.consumer_name,
            "provider": self.provider_name,
            "endpoint": self.endpoint,
            "method": self.method,
            "request": request_schema,
            "response": response_schema,
            "description": self.description
        }
        
    @classmethod
    def from_dict(cls, contract_dict: Dict[str, Any]) -> "ContractDefinition":
        """
        Create a contract from a dictionary.
        
        Args:
            contract_dict: Dictionary representation of a contract.
            
        Returns:
            Contract definition.
        """
        request_schema = None
        if contract_dict.get("request") is not None:
            request_schema = create_model_from_schema(
                f"{contract_dict['consumer']}To{contract_dict['provider']}Request",
                contract_dict["request"]
            )
            
        response_schema = None
        if contract_dict.get("response") is not None:
            response_schema = create_model_from_schema(
                f"{contract_dict['provider']}To{contract_dict['consumer']}Response",
                contract_dict["response"]
            )
            
        return cls(
            consumer_name=contract_dict["consumer"],
            provider_name=contract_dict["provider"],
            endpoint=contract_dict["endpoint"],
            method=contract_dict.get("method", "GET"),
            request_schema=request_schema,
            response_schema=response_schema,
            description=contract_dict.get("description")
        )


def create_model_from_schema(
    model_name: str, 
    schema: Dict[str, Any]
) -> Type[BaseModel]:
    """
    Create a Pydantic model from a JSON schema.
    
    Args:
        model_name: Name of the model to create.
        schema: JSON schema.
        
    Returns:
        Pydantic model.
    """
    # TODO: Implement a more complete JSON schema to Pydantic model converter
    # This is a simplified version that handles only basic types
    fields = {}
    
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    
    for field_name, field_schema in properties.items():
        field_type = field_schema.get("type")
        field_default = field_schema.get("default", ...)
        
        python_type = Any
        if field_type == "string":
            python_type = str
        elif field_type == "number":
            python_type = float
        elif field_type == "integer":
            python_type = int
        elif field_type == "boolean":
            python_type = bool
        elif field_type == "array":
            # For simplicity, we use List[Any] for arrays
            python_type = List[Any]
        elif field_type == "object":
            # For simplicity, we use Dict[str, Any] for objects
            python_type = Dict[str, Any]
            
        # If the field is required, use ... as the default value
        # Otherwise, use None
        if field_name in required:
            # Required field with default value
            if field_default is not ...:
                fields[field_name] = (python_type, field_default)
            else:
                # Required field without default value
                fields[field_name] = (python_type, ...)
        else:
            # Optional field with default value
            if field_default is not ...:
                fields[field_name] = (python_type, field_default)
            else:
                # Optional field without default value
                fields[field_name] = (Optional[python_type], None)
                
    return create_model(model_name, **fields)


class ContractRegistry:
    """
    Registry for contract definitions.
    
    This class provides methods for registering, retrieving, and verifying
    contracts between services.
    """
    
    def __init__(self):
        """Initialize the contract registry."""
        self.contracts: Dict[str, ContractDefinition] = {}
        
    def register_contract(self, contract: ContractDefinition) -> None:
        """
        Register a contract.
        
        Args:
            contract: Contract definition.
        """
        key = f"{contract.consumer_name}:{contract.provider_name}:{contract.endpoint}:{contract.method}"
        self.contracts[key] = contract
        
    def get_contract(
        self,
        consumer_name: str,
        provider_name: str,
        endpoint: str,
        method: str = "GET"
    ) -> Optional[ContractDefinition]:
        """
        Get a contract by consumer, provider, endpoint, and method.
        
        Args:
            consumer_name: Name of the consumer service.
            provider_name: Name of the provider service.
            endpoint: API endpoint path.
            method: HTTP method (default: "GET").
            
        Returns:
            Contract definition, or None if not found.
        """
        key = f"{consumer_name}:{provider_name}:{endpoint}:{method.upper()}"
        return self.contracts.get(key)
        
    def get_contracts_for_consumer(
        self,
        consumer_name: str
    ) -> List[ContractDefinition]:
        """
        Get all contracts for a consumer.
        
        Args:
            consumer_name: Name of the consumer service.
            
        Returns:
            List of contract definitions.
        """
        return [
            contract for key, contract in self.contracts.items()
            if contract.consumer_name == consumer_name
        ]
        
    def get_contracts_for_provider(
        self,
        provider_name: str
    ) -> List[ContractDefinition]:
        """
        Get all contracts for a provider.
        
        Args:
            provider_name: Name of the provider service.
            
        Returns:
            List of contract definitions.
        """
        return [
            contract for key, contract in self.contracts.items()
            if contract.provider_name == provider_name
        ]
        
    def save_to_file(self, file_path: str) -> None:
        """
        Save the contract registry to a file.
        
        Args:
            file_path: Path to save the contract registry.
        """
        contracts_data = [
            contract.to_dict() for contract in self.contracts.values()
        ]
        
        with open(file_path, "w") as f:
            json.dump(contracts_data, f, indent=2)
            
    @classmethod
    def load_from_file(cls, file_path: str) -> "ContractRegistry":
        """
        Load a contract registry from a file.
        
        Args:
            file_path: Path to load the contract registry from.
            
        Returns:
            Contract registry.
        """
        registry = cls()
        
        if not os.path.exists(file_path):
            return registry
            
        with open(file_path, "r") as f:
            contracts_data = json.load(f)
            
        for contract_data in contracts_data:
            contract = ContractDefinition.from_dict(contract_data)
            registry.register_contract(contract)
            
        return registry


class ContractVerifier:
    """
    Verifier for contracts between services.
    
    This class provides methods for verifying that requests and responses
    match the contracts between services.
    """
    
    def __init__(self, registry: ContractRegistry):
        """
        Initialize the contract verifier.
        
        Args:
            registry: Contract registry.
        """
        self.registry = registry
        
    def verify_request(
        self,
        consumer_name: str,
        provider_name: str,
        endpoint: str,
        method: str,
        request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Verify a request against the contract.
        
        Args:
            consumer_name: Name of the consumer service.
            provider_name: Name of the provider service.
            endpoint: API endpoint path.
            method: HTTP method.
            request_data: Request data to verify.
            
        Returns:
            Validated request data.
            
        Raises:
            ValidationError: If the request does not match the contract.
            ValueError: If the contract is not found.
        """
        contract = self.registry.get_contract(
            consumer_name=consumer_name,
            provider_name=provider_name,
            endpoint=endpoint,
            method=method
        )
        
        if contract is None:
            raise ValueError(
                f"Contract not found for {consumer_name} -> {provider_name} "
                f"({method} {endpoint})"
            )
            
        return contract.validate_request(request_data)
        
    def verify_response(
        self,
        consumer_name: str,
        provider_name: str,
        endpoint: str,
        method: str,
        response_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Verify a response against the contract.
        
        Args:
            consumer_name: Name of the consumer service.
            provider_name: Name of the provider service.
            endpoint: API endpoint path.
            method: HTTP method.
            response_data: Response data to verify.
            
        Returns:
            Validated response data.
            
        Raises:
            ValidationError: If the response does not match the contract.
            ValueError: If the contract is not found.
        """
        contract = self.registry.get_contract(
            consumer_name=consumer_name,
            provider_name=provider_name,
            endpoint=endpoint,
            method=method
        )
        
        if contract is None:
            raise ValueError(
                f"Contract not found for {consumer_name} -> {provider_name} "
                f"({method} {endpoint})"
            )
            
        return contract.validate_response(response_data)


class ContractTestBuilder:
    """
    Builder for contract tests.
    
    This class provides methods for building contract tests for
    consumer and provider services.
    """
    
    def __init__(self, registry: ContractRegistry):
        """
        Initialize the contract test builder.
        
        Args:
            registry: Contract registry.
        """
        self.registry = registry
        
    def build_consumer_tests(
        self,
        consumer_name: str
    ) -> Dict[str, Callable]:
        """
        Build tests for a consumer service.
        
        Args:
            consumer_name: Name of the consumer service.
            
        Returns:
            Dictionary mapping test names to test functions.
        """
        contracts = self.registry.get_contracts_for_consumer(consumer_name)
        
        tests = {}
        for contract in contracts:
            test_name = f"test_{consumer_name}_contract_with_{contract.provider_name}_{contract.method}_{contract.endpoint.replace('/', '_')}"
            
            def test_function():
                # This is a placeholder that will be replaced by an actual test implementation
                pass
                
            test_function.__name__ = test_name
            test_function.__doc__ = f"Test contract between {consumer_name} and {contract.provider_name} for {contract.method} {contract.endpoint}"
            
            tests[test_name] = test_function
            
        return tests
        
    def build_provider_tests(
        self,
        provider_name: str
    ) -> Dict[str, Callable]:
        """
        Build tests for a provider service.
        
        Args:
            provider_name: Name of the provider service.
            
        Returns:
            Dictionary mapping test names to test functions.
        """
        contracts = self.registry.get_contracts_for_provider(provider_name)
        
        tests = {}
        for contract in contracts:
            test_name = f"test_{provider_name}_contract_with_{contract.consumer_name}_{contract.method}_{contract.endpoint.replace('/', '_')}"
            
            def test_function():
                # This is a placeholder that will be replaced by an actual test implementation
                pass
                
            test_function.__name__ = test_name
            test_function.__doc__ = f"Test contract between {contract.consumer_name} and {provider_name} for {contract.method} {contract.endpoint}"
            
            tests[test_name] = test_function
            
        return tests
        
    def generate_test_module(
        self,
        service_name: str,
        is_consumer: bool = True,
        output_file: Optional[str] = None
    ) -> str:
        """
        Generate a test module for a service.
        
        Args:
            service_name: Name of the service.
            is_consumer: Whether the service is a consumer (default: True).
            output_file: Optional path to save the generated module.
            
        Returns:
            Generated test module.
        """
        if is_consumer:
            tests = self.build_consumer_tests(service_name)
        else:
            tests = self.build_provider_tests(service_name)
            
        lines = [
            "# Generated contract tests for {}".format(service_name),
            "import pytest",
            "from shared.utils.src.testing.contract import ContractRegistry, ContractVerifier",
            "",
            "# Load contract registry",
            "CONTRACT_REGISTRY = ContractRegistry.load_from_file('contracts.json')",
            "CONTRACT_VERIFIER = ContractVerifier(CONTRACT_REGISTRY)",
            ""
        ]
        
        for test_name, test_function in tests.items():
            lines.append(f"def {test_name}():")
            lines.append(f'    """{test_function.__doc__}"""')
            lines.append("    # Implement the test here")
            lines.append("    pass")
            lines.append("")
            
        module_text = "\n".join(lines)
        
        if output_file is not None:
            with open(output_file, "w") as f:
                f.write(module_text)
                
        return module_text
