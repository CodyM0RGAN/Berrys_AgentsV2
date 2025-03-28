"""
Model Orchestrator client for interacting with the Model Orchestration service.

This module provides a client for making API calls to the Model Orchestration service.
"""
import logging
import json
from typing import Dict, List, Optional, Any, Union
import httpx

from ...exceptions import DependencyError

logger = logging.getLogger(__name__)

class ModelOrchestratorClient:
    """Client for interacting with the Model Orchestration service."""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None, timeout: int = 30):
        """
        Initialize the Model Orchestrator client.
        
        Args:
            base_url: Base URL of the Model Orchestration service
            api_key: API key for authentication (if required)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.session = httpx.AsyncClient(timeout=timeout)
        
        # Set up headers
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        if api_key:
            self.headers['Authorization'] = f'Bearer {api_key}'
    
    async def generate_response(
        self, 
        message: str, 
        context: Dict[str, Any]
    ) -> str:
        """
        Generate a response using the Model Orchestration service.
        
        Args:
            message: User message
            context: Context information for the model
            
        Returns:
            Generated response
            
        Raises:
            DependencyError: If there's an error communicating with the Model Orchestration service
        """
        try:
            url = f"{self.base_url}/generate"
            
            payload = {
                'message': message,
                'context': context
            }
            
            response = await self.session.post(
                url,
                headers=self.headers,
                json=payload
            )
            
            if response.status_code != 200:
                error_detail = response.text
                try:
                    error_json = response.json()
                    if 'detail' in error_json:
                        error_detail = error_json['detail']
                except:
                    pass
                
                logger.error(f"Error from Model Orchestration service: {error_detail}")
                raise DependencyError(
                    message=f"Error from Model Orchestration service: {error_detail}",
                    status_code=response.status_code
                )
            
            result = response.json()
            return result.get('response', '')
        
        except httpx.RequestError as e:
            logger.error(f"Error connecting to Model Orchestration service: {str(e)}")
            raise DependencyError(
                message=f"Error connecting to Model Orchestration service: {str(e)}",
                status_code=503
            )
        
        except Exception as e:
            logger.error(f"Unexpected error in Model Orchestration client: {str(e)}")
            raise DependencyError(
                message=f"Unexpected error in Model Orchestration client: {str(e)}",
                status_code=500
            )
    
    async def analyze_message(
        self, 
        message: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze a message to extract structured information.
        
        Args:
            message: User message
            context: Context information for the model
            
        Returns:
            Extracted information
            
        Raises:
            DependencyError: If there's an error communicating with the Model Orchestration service
        """
        try:
            url = f"{self.base_url}/analyze"
            
            payload = {
                'message': message,
                'context': context
            }
            
            response = await self.session.post(
                url,
                headers=self.headers,
                json=payload
            )
            
            if response.status_code != 200:
                error_detail = response.text
                try:
                    error_json = response.json()
                    if 'detail' in error_json:
                        error_detail = error_json['detail']
                except:
                    pass
                
                logger.error(f"Error from Model Orchestration service: {error_detail}")
                raise DependencyError(
                    message=f"Error from Model Orchestration service: {error_detail}",
                    status_code=response.status_code
                )
            
            return response.json()
        
        except httpx.RequestError as e:
            logger.error(f"Error connecting to Model Orchestration service: {str(e)}")
            raise DependencyError(
                message=f"Error connecting to Model Orchestration service: {str(e)}",
                status_code=503
            )
        
        except Exception as e:
            logger.error(f"Unexpected error in Model Orchestration client: {str(e)}")
            raise DependencyError(
                message=f"Unexpected error in Model Orchestration client: {str(e)}",
                status_code=500
            )
    
    async def close(self):
        """Close the HTTP session."""
        await self.session.aclose()
