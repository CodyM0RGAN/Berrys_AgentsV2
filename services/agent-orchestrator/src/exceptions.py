from fastapi import status
from typing import Optional, Any, Dict, List
from uuid import UUID


class AuthenticationError(Exception):
    """
    Exception for authentication errors.
    """
    def __init__(
        self,
        message: str = "Authentication failed",
        code: str = "authentication_error",
        status_code: int = status.HTTP_401_UNAUTHORIZED,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ServiceError(Exception):
    """
    Base exception for service-specific errors.
    """
    def __init__(
        self,
        message: str,
        code: str = "service_error",
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class AgentNotFoundError(ServiceError):
    """
    Exception for agent not found errors.
    """
    def __init__(
        self,
        agent_id: UUID,
        message: Optional[str] = None,
        code: str = "agent_not_found",
        details: Optional[Dict[str, Any]] = None,
    ):
        message = message or f"Agent with ID {agent_id} not found"
        details = details or {"agent_id": str(agent_id)}
        super().__init__(message, code, status.HTTP_404_NOT_FOUND, details)


class ExecutionNotFoundError(ServiceError):
    """
    Exception for execution not found errors.
    """
    def __init__(
        self,
        execution_id: UUID,
        message: Optional[str] = None,
        code: str = "execution_not_found",
        details: Optional[Dict[str, Any]] = None,
    ):
        message = message or f"Execution with ID {execution_id} not found"
        details = details or {"execution_id": str(execution_id)}
        super().__init__(message, code, status.HTTP_404_NOT_FOUND, details)


class AgentConfigurationError(ServiceError):
    """
    Exception for agent configuration errors.
    """
    def __init__(
        self,
        message: str = "Agent configuration error",
        code: str = "agent_configuration_error",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code, status.HTTP_400_BAD_REQUEST, details)


class InvalidAgentStateError(ServiceError):
    """
    Exception for invalid agent state transition errors.
    """
    def __init__(
        self,
        current_state: str,
        target_state: str,
        message: Optional[str] = None,
        code: str = "invalid_agent_state",
        details: Optional[Dict[str, Any]] = None,
    ):
        message = message or f"Cannot transition from {current_state} to {target_state}"
        details = details or {"current_state": current_state, "target_state": target_state}
        super().__init__(message, code, status.HTTP_400_BAD_REQUEST, details)


class InvalidExecutionStateError(ServiceError):
    """
    Exception for invalid execution state transition errors.
    """
    def __init__(
        self,
        current_state: str,
        target_state: str,
        message: Optional[str] = None,
        code: str = "invalid_execution_state",
        details: Optional[Dict[str, Any]] = None,
    ):
        message = message or f"Cannot transition from {current_state} to {target_state}"
        details = details or {"current_state": current_state, "target_state": target_state}
        super().__init__(message, code, status.HTTP_400_BAD_REQUEST, details)


class AgentExecutionError(ServiceError):
    """
    Exception for agent execution errors.
    """
    def __init__(
        self,
        agent_id: UUID,
        message: str = "Agent execution error",
        code: str = "agent_execution_error",
        details: Optional[Dict[str, Any]] = None,
    ):
        details = details or {"agent_id": str(agent_id)}
        super().__init__(message, code, status.HTTP_500_INTERNAL_SERVER_ERROR, details)


class AgentCommunicationError(ServiceError):
    """
    Exception for agent communication errors.
    """
    def __init__(
        self,
        from_agent_id: UUID,
        to_agent_id: UUID,
        message: str = "Agent communication error",
        code: str = "agent_communication_error",
        details: Optional[Dict[str, Any]] = None,
    ):
        details = details or {
            "from_agent_id": str(from_agent_id),
            "to_agent_id": str(to_agent_id),
        }
        super().__init__(message, code, status.HTTP_500_INTERNAL_SERVER_ERROR, details)


class TemplateNotFoundError(ServiceError):
    """
    Exception for template not found errors.
    """
    def __init__(
        self,
        template_id: str,
        message: Optional[str] = None,
        code: str = "template_not_found",
        details: Optional[Dict[str, Any]] = None,
    ):
        message = message or f"Template with ID {template_id} not found"
        details = details or {"template_id": template_id}
        super().__init__(message, code, status.HTTP_404_NOT_FOUND, details)


class TemplateValidationError(ServiceError):
    """
    Exception for template validation errors.
    """
    def __init__(
        self,
        template_id: str,
        errors: List[str],
        message: Optional[str] = None,
        code: str = "template_validation_error",
        details: Optional[Dict[str, Any]] = None,
    ):
        message = message or f"Template validation failed: {', '.join(errors)}"
        details = details or {"template_id": template_id, "errors": errors}
        super().__init__(message, code, status.HTTP_400_BAD_REQUEST, details)


class AgentStateError(ServiceError):
    """
    Exception for agent state errors.
    """
    def __init__(
        self,
        agent_id: UUID,
        message: str = "Agent state error",
        code: str = "agent_state_error",
        details: Optional[Dict[str, Any]] = None,
    ):
        details = details or {"agent_id": str(agent_id)}
        super().__init__(message, code, status.HTTP_500_INTERNAL_SERVER_ERROR, details)


class ConcurrentModificationError(ServiceError):
    """
    Exception for concurrent modification errors.
    """
    def __init__(
        self,
        agent_id: UUID,
        message: Optional[str] = None,
        code: str = "concurrent_modification_error",
        details: Optional[Dict[str, Any]] = None,
    ):
        message = message or f"Agent with ID {agent_id} was modified concurrently"
        details = details or {"agent_id": str(agent_id)}
        super().__init__(message, code, status.HTTP_409_CONFLICT, details)


class ExternalServiceError(ServiceError):
    """
    Exception for errors from external services.
    """
    def __init__(
        self,
        service: str,
        message: str = "External service error",
        code: str = "external_service_error",
        status_code: int = status.HTTP_502_BAD_GATEWAY,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.service = service
        details = details or {"service": service}
        super().__init__(message, code, status_code, details)


class ModelOrchestrationError(ExternalServiceError):
    """
    Exception for errors from the Model Orchestration service.
    """
    def __init__(
        self,
        message: str = "Model Orchestration service error",
        code: str = "model_orchestration_error",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__("model-orchestration", message, code, status.HTTP_502_BAD_GATEWAY, details)


class HumanInteractionError(ServiceError):
    """
    Exception for human interaction errors.
    """
    def __init__(
        self,
        agent_id: UUID,
        message: str = "Human interaction error",
        code: str = "human_interaction_error",
        details: Optional[Dict[str, Any]] = None,
    ):
        details = details or {"agent_id": str(agent_id)}
        super().__init__(message, code, status.HTTP_500_INTERNAL_SERVER_ERROR, details)


class DatabaseError(ServiceError):
    """
    Exception for database errors.
    """
    def __init__(
        self,
        message: str = "Database error",
        code: str = "database_error",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code, status.HTTP_500_INTERNAL_SERVER_ERROR, details)


class SpecializationNotFoundError(ServiceError):
    """
    Exception for specialization not found errors.
    """
    def __init__(
        self,
        agent_type: str,
        message: Optional[str] = None,
        code: str = "specialization_not_found",
        details: Optional[Dict[str, Any]] = None,
    ):
        message = message or f"Specialization for agent type {agent_type} not found"
        details = details or {"agent_type": agent_type}
        super().__init__(message, code, status.HTTP_404_NOT_FOUND, details)


class InvalidRequestError(ServiceError):
    """
    Exception for invalid request errors.
    """
    def __init__(
        self,
        message: str = "Invalid request",
        code: str = "invalid_request",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code, status.HTTP_400_BAD_REQUEST, details)


class PatternNotFoundError(ServiceError):
    """
    Exception for collaboration pattern not found errors.
    """
    def __init__(
        self,
        pattern_id: UUID,
        message: Optional[str] = None,
        code: str = "pattern_not_found",
        details: Optional[Dict[str, Any]] = None,
    ):
        message = message or f"Collaboration pattern with ID {pattern_id} not found"
        details = details or {"pattern_id": str(pattern_id)}
        super().__init__(message, code, status.HTTP_404_NOT_FOUND, details)
