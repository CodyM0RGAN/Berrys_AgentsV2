"""
Tool Discovery Service module.

This module defines the discovery service for finding and registering tools,
providing a unified interface for discovering tools from various sources.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID

from ..repository import ToolRepository
from .factory import DiscoveryStrategyFactory
from .strategy import DiscoveryStrategy
from ...exceptions import ToolDiscoveryError

logger = logging.getLogger(__name__)


class DiscoveryService:
    """Service for discovering tools from various sources."""
    
    def __init__(
        self,
        repository: ToolRepository,
        event_bus: Any,
        discovery_factory: DiscoveryStrategyFactory,
        cache_ttl: int = 3600,
    ):
        """
        Initialize the discovery service.
        
        Args:
            repository: Tool repository
            event_bus: Event bus for publishing events
            discovery_factory: Discovery strategy factory
            cache_ttl: Cache time to live in seconds
        """
        self.repository = repository
        self.event_bus = event_bus
        self.discovery_factory = discovery_factory
        self.cache_ttl = cache_ttl
        
        # Discovery cache
        self._discovery_cache: Dict[str, Tuple[List[Dict[str, Any]], float]] = {}
        
        logger.info("Discovery service initialized")
    
    async def discover_tools(
        self,
        requirements: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Discover tools based on requirements.
        
        Args:
            requirements: Tool requirements
            context: Optional discovery context
            
        Returns:
            List[Dict[str, Any]]: Discovered tools
            
        Raises:
            ToolDiscoveryError: If discovery fails
        """
        logger.info(f"Discovering tools with requirements: {requirements}")
        
        # Extract requirements
        capability = requirements.get("capability")
        source = requirements.get("source")
        integration_type = requirements.get("integration_type")
        min_score = requirements.get("min_score", 0.5)
        
        # Check cache if applicable
        cache_key = self._generate_cache_key(capability, source, integration_type, min_score)
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            logger.info(f"Using cached discovery result for {cache_key}")
            return cached_result
        
        try:
            # Discover from specific source if provided
            if source:
                strategy = self.discovery_factory.get_strategy_for_source(source)
                discovered_tools = await strategy.discover(
                    capability=capability,
                    integration_type=integration_type,
                    min_score=min_score,
                    context=context,
                )
            else:
                # Discover from all sources
                discovered_tools = await self._discover_from_all_sources(
                    capability=capability,
                    integration_type=integration_type,
                    min_score=min_score,
                    context=context,
                )
            
            # Cache result
            self._add_to_cache(cache_key, discovered_tools)
            
            # Publish discovery event
            await self._publish_discovery_event(discovered_tools)
            
            return discovered_tools
        except Exception as e:
            logger.error(f"Error discovering tools: {str(e)}")
            raise ToolDiscoveryError(f"Tool discovery failed: {str(e)}")
    
    async def _discover_from_all_sources(
        self,
        capability: Optional[str] = None,
        integration_type: Optional[str] = None,
        min_score: float = 0.5,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Discover tools from all available sources.
        
        Args:
            capability: Optional capability filter
            integration_type: Optional integration type filter
            min_score: Minimum match score
            context: Optional discovery context
            
        Returns:
            List[Dict[str, Any]]: Discovered tools
        """
        logger.info(f"Discovering tools from all sources (capability={capability})")
        
        # Create strategies for all sources
        strategies = [
            self.discovery_factory.create_strategy("mcp"),
            self.discovery_factory.create_strategy("api"),
            self.discovery_factory.create_strategy("repository"),
        ]
        
        # Discover from all sources in parallel
        tasks = [
            strategy.discover(
                capability=capability,
                integration_type=integration_type,
                min_score=min_score,
                context=context,
            )
            for strategy in strategies
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results, filtering out exceptions
        discovered_tools = []
        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"Error in discovery: {str(result)}")
            else:
                discovered_tools.extend(result)
        
        # Sort by match score (descending)
        discovered_tools.sort(key=lambda t: t.get("match_score", 0.0), reverse=True)
        
        return discovered_tools
    
    def get_strategy_for_source(self, source: str) -> DiscoveryStrategy:
        """
        Get a discovery strategy for a specific source.
        
        Args:
            source: Tool source
            
        Returns:
            DiscoveryStrategy: Discovery strategy
            
        Raises:
            ValueError: If source is not supported
        """
        return self.discovery_factory.get_strategy_for_source(source)
    
    def _generate_cache_key(
        self,
        capability: Optional[str],
        source: Optional[str],
        integration_type: Optional[str],
        min_score: float,
    ) -> str:
        """Generate a cache key for the given parameters."""
        return f"{capability}:{source}:{integration_type}:{min_score}"
    
    def _get_from_cache(self, key: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get discovery result from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Optional[List[Dict[str, Any]]]: Cached result if found and not expired
        """
        if key in self._discovery_cache:
            result, timestamp = self._discovery_cache[key]
            if asyncio.get_event_loop().time() - timestamp < self.cache_ttl:
                return result
            else:
                # Expired
                del self._discovery_cache[key]
        return None
    
    def _add_to_cache(self, key: str, result: List[Dict[str, Any]]) -> None:
        """
        Add discovery result to cache.
        
        Args:
            key: Cache key
            result: Discovery result
        """
        self._discovery_cache[key] = (result, asyncio.get_event_loop().time())
    
    async def _publish_discovery_event(self, discovered_tools: List[Dict[str, Any]]) -> None:
        """
        Publish discovery event.
        
        Args:
            discovered_tools: Discovered tools
        """
        if self.event_bus:
            await self.event_bus.publish(
                "tools_discovered",
                {
                    "count": len(discovered_tools),
                    "tool_summaries": [
                        {
                            "name": t.get("name"),
                            "capability": t.get("capability"),
                            "source": t.get("source"),
                            "match_score": t.get("match_score", 0.0),
                        }
                        for t in discovered_tools
                    ],
                }
            )
