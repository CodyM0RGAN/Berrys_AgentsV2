from fastapi import status
from typing import Optional, Any, Dict


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


class ModelServiceError(Exception):
    """
    Base exception for model service errors.
    """
    def __init__(
        self,
        message: str,
        code: str = "model_service_error",
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ModelNotFoundError(ModelServiceError):
    """
    Exception for model not found errors.
    """
    def __init__(
        self,
        model_id: str,
        message: Optional[str] = None,
        code: str = "model_not_found",
        details: Optional[Dict[str, Any]] = None,
    ):
        message = message or f"Model '{model_id}' not found"
        details = details or {"model_id": model_id}
        super().__init__(message, code, status.HTTP_404_NOT_FOUND, details)


class ProviderError(ModelServiceError):
    """
    Exception for provider-specific errors.
    """
    def __init__(
        self,
        message: str,
        provider: str,
        code: str = "provider_error",
        status_code: int = status.HTTP_502_BAD_GATEWAY,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.provider = provider
        details = details or {"provider": provider}
        super().__init__(message, code, status_code, details)


class ProviderNotAvailableError(ProviderError):
    """
    Exception for provider not available errors.
    """
    def __init__(
        self,
        provider: str,
        message: Optional[str] = None,
        code: str = "provider_not_available",
        details: Optional[Dict[str, Any]] = None,
    ):
        message = message or f"Provider '{provider}' is not available"
        super().__init__(message, provider, code, status.HTTP_503_SERVICE_UNAVAILABLE, details)


class ProviderAuthenticationError(ProviderError):
    """
    Exception for provider authentication errors.
    """
    def __init__(
        self,
        provider: str,
        message: Optional[str] = None,
        code: str = "provider_authentication_error",
        details: Optional[Dict[str, Any]] = None,
    ):
        message = message or f"Authentication failed for provider '{provider}'"
        super().__init__(message, provider, code, status.HTTP_401_UNAUTHORIZED, details)


class RateLimitError(ProviderError):
    """
    Exception for rate limit errors.
    """
    def __init__(
        self,
        provider: str,
        message: Optional[str] = None,
        code: str = "rate_limit_exceeded",
        details: Optional[Dict[str, Any]] = None,
    ):
        message = message or f"Rate limit exceeded for provider '{provider}'"
        super().__init__(message, provider, code, status.HTTP_429_TOO_MANY_REQUESTS, details)


class TokenLimitError(ModelServiceError):
    """
    Exception for token limit errors.
    """
    def __init__(
        self,
        token_count: int,
        token_limit: int,
        message: Optional[str] = None,
        code: str = "token_limit_exceeded",
        details: Optional[Dict[str, Any]] = None,
    ):
        message = message or f"Token limit exceeded: {token_count} > {token_limit}"
        details = details or {"token_count": token_count, "token_limit": token_limit}
        super().__init__(message, code, status.HTTP_400_BAD_REQUEST, details)


class InvalidRequestError(ModelServiceError):
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


class ContentFilterError(ModelServiceError):
    """
    Exception for content filter errors.
    """
    def __init__(
        self,
        message: str = "Content filtered",
        code: str = "content_filtered",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code, status.HTTP_400_BAD_REQUEST, details)


class RequestTimeoutError(ModelServiceError):
    """
    Exception for request timeout errors.
    """
    def __init__(
        self,
        provider: str,
        message: Optional[str] = None,
        code: str = "request_timeout",
        details: Optional[Dict[str, Any]] = None,
    ):
        message = message or f"Request to provider '{provider}' timed out"
        details = details or {"provider": provider}
        super().__init__(message, code, status.HTTP_504_GATEWAY_TIMEOUT, details)
