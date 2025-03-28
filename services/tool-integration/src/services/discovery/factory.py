"""
Discovery Strategy Factory module.

This module defines the factory for creating discovery strategies,
providing a centralized way to instantiate and configure strategies.
"""

import logging
from typing import Dict, Any, Optional, Type

from .strategy import (
    DiscoveryStrategy,
    MCPDiscoveryStrategy,
    APIDiscoveryStrategy,
    RepositoryDiscoveryStrategy,
    MCP_STRATEGY,
    API_STRATEGY,
    REPOSITORY_STRATEGY,
)
from shared.models.src.tool import ToolSource

logger = logging.getLogger(__name__)


class DiscoveryStrategyFactory:
    """Factory for creating and configuring discovery strategies."""
    
    def __init__(
        self,
        batch_size: int = 20,
        max_depth: int = 3,
        mcp_connection_timeout: int = 5,
        mcp_request_timeout: int = 30,
        api_keys: Optional[Dict[str, str]] = None,
        repository_urls: Optional[list[str]] = None,
    ):
        """
        Initialize the discovery strategy factory.
        
        Args:
            batch_size: Maximum number of tools to discover in one batch
            max_depth: Maximum depth for recursive discovery
            mcp_connection_timeout: Connection timeout for MCP servers in seconds
            mcp_request_timeout: Request timeout for MCP servers in seconds
            api_keys: Optional API keys for external APIs
            repository_urls: Optional repository URLs
        """
        self.batch_size = batch_size
        self.max_depth = max_depth
        self.mcp_connection_timeout = mcp_connection_timeout
        self.mcp_request_timeout = mcp_request_timeout
        self.api_keys = api_keys or {}
        self.repository_urls = repository_urls or []
        
        # Register strategies
        self._strategies: Dict[str, Type[DiscoveryStrategy]] = {
            MCP_STRATEGY: MCPDiscoveryStrategy,
            API_STRATEGY: APIDiscoveryStrategy,
            REPOSITORY_STRATEGY: RepositoryDiscoveryStrategy,
        }
        
        # Map sources to strategies
        self._source_strategy_map = {
            ToolSource.MCP: MCP_STRATEGY,
            ToolSource.EXTERNAL_API: API_STRATEGY,
            ToolSource.CODE_REPOSITORY: REPOSITORY_STRATEGY,
            ToolSource.REGISTRY: REPOSITORY_STRATEGY,
        }
        
        logger.info(f"Discovery strategy factory initialized with {len(self._strategies)} strategies")
    
    def create_strategy(self, strategy_name: str) -> DiscoveryStrategy:
        """
        Create a discovery strategy by name.
        
        Args:
            strategy_name: Strategy name
            
        Returns:
            DiscoveryStrategy: Discovery strategy instance
            
        Raises:
            ValueError: If strategy name is not found
        """
        logger.info(f"Creating discovery strategy: {strategy_name}")
        
        if strategy_name not in self._strategies:
            raise ValueError(f"Unknown discovery strategy: {strategy_name}")
        
        strategy_class = self._strategies[strategy_name]
        
        # Create strategy with appropriate configuration
        if strategy_name == MCP_STRATEGY:
            return strategy_class(
                batch_size=self.batch_size,
                max_depth=self.max_depth,
                mcp_connection_timeout=self.mcp_connection_timeout,
                mcp_request_timeout=self.mcp_request_timeout,
            )
        elif strategy_name == API_STRATEGY:
            return strategy_class(
                batch_size=self.batch_size,
                max_depth=self.max_depth,
                api_keys=self.api_keys,
            )
        elif strategy_name == REPOSITORY_STRATEGY:
            return strategy_class(
                batch_size=self.batch_size,
                max_depth=self.max_depth,
                repository_urls=self.repository_urls,
            )
        else:
            # Fallback to base configuration
            return strategy_class(
                batch_size=self.batch_size,
                max_depth=self.max_depth,
            )
    
    def get_strategy_for_source(self, source: str) -> DiscoveryStrategy:
        """
        Get a discovery strategy for a specific source.
        
        Args:
            source: Tool source
            
        Returns:
            DiscoveryStrategy: Discovery strategy instance
            
        Raises:
            ValueError: If source is not supported
        """
        logger.info(f"Getting discovery strategy for source: {source}")
        
        if source not in self._source_strategy_map:
            raise ValueError(f"Unsupported discovery source: {source}")
        
        strategy_name = self._source_strategy_map[source]
        return self.create_strategy(strategy_name)
    
    def register_strategy(self, name: str, strategy_class: Type[DiscoveryStrategy]) -> None:
        """
        Register a new discovery strategy.
        
        Args:
            name: Strategy name
            strategy_class: Strategy class
        """
        logger.info(f"Registering discovery strategy: {name}")
        
        self._strategies[name] = strategy_class
