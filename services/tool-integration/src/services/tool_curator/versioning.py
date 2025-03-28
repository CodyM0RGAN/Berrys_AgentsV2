"""
Tool versioning system for the Tool Curator component.

This module provides functionality for managing tool versions, tracking updates,
and ensuring compatibility between different versions.
"""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID
from datetime import datetime

from .models import ToolVersion, ToolVersionStatus

logger = logging.getLogger(__name__)


class ToolVersioningService:
    """
    Service for managing tool versions and tracking updates.
    
    This class implements functionality for:
    - Parsing and validating semantic version numbers
    - Comparing versions for compatibility
    - Tracking version history
    - Managing version status (current, deprecated, etc.)
    """
    
    def __init__(self):
        """Initialize the tool versioning service."""
        logger.info("Initialized ToolVersioningService")
    
    async def parse_version(self, version_string: str) -> Tuple[int, int, int, Optional[str]]:
        """
        Parse a semantic version string into its components.
        
        Args:
            version_string: Semantic version string (e.g., "1.2.3" or "1.2.3-beta")
            
        Returns:
            Tuple[int, int, int, Optional[str]]: Major, minor, patch versions and optional suffix
            
        Raises:
            ValueError: If the version string is invalid
        """
        # Regular expression for semantic versioning
        pattern = r"^(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9.-]+))?$"
        match = re.match(pattern, version_string)
        
        if not match:
            raise ValueError(f"Invalid semantic version: {version_string}")
        
        major = int(match.group(1))
        minor = int(match.group(2))
        patch = int(match.group(3))
        suffix = match.group(4)
        
        return major, minor, patch, suffix
    
    async def compare_versions(self, version1: str, version2: str) -> int:
        """
        Compare two semantic versions.
        
        Args:
            version1: First version string
            version2: Second version string
            
        Returns:
            int: -1 if version1 < version2, 0 if equal, 1 if version1 > version2
            
        Raises:
            ValueError: If either version string is invalid
        """
        major1, minor1, patch1, suffix1 = await self.parse_version(version1)
        major2, minor2, patch2, suffix2 = await self.parse_version(version2)
        
        # Compare major versions
        if major1 < major2:
            return -1
        elif major1 > major2:
            return 1
        
        # Compare minor versions
        if minor1 < minor2:
            return -1
        elif minor1 > minor2:
            return 1
        
        # Compare patch versions
        if patch1 < patch2:
            return -1
        elif patch1 > patch2:
            return 1
        
        # If we get here, the versions are equal except possibly for suffixes
        
        # No suffixes means they're exactly equal
        if suffix1 is None and suffix2 is None:
            return 0
        
        # A version with no suffix is greater than one with a suffix
        if suffix1 is None:
            return 1
        if suffix2 is None:
            return -1
        
        # Compare suffixes lexicographically
        if suffix1 < suffix2:
            return -1
        elif suffix1 > suffix2:
            return 1
        else:
            return 0
    
    async def is_compatible(self, version1: str, version2: str) -> bool:
        """
        Check if two versions are compatible.
        
        In semantic versioning, versions with the same major version are typically
        considered compatible.
        
        Args:
            version1: First version string
            version2: Second version string
            
        Returns:
            bool: True if the versions are compatible, False otherwise
            
        Raises:
            ValueError: If either version string is invalid
        """
        major1, _, _, _ = await self.parse_version(version1)
        major2, _, _, _ = await self.parse_version(version2)
        
        return major1 == major2
    
    async def is_breaking_change(self, version1: str, version2: str) -> bool:
        """
        Check if upgrading from version1 to version2 would be a breaking change.
        
        In semantic versioning, a change in the major version indicates a breaking change.
        
        Args:
            version1: Current version string
            version2: New version string
            
        Returns:
            bool: True if upgrading would be a breaking change, False otherwise
            
        Raises:
            ValueError: If either version string is invalid
        """
        major1, _, _, _ = await self.parse_version(version1)
        major2, _, _, _ = await self.parse_version(version2)
        
        return major2 > major1
    
    async def create_version(
        self,
        tool_id: UUID,
        version_number: str,
        status: ToolVersionStatus = ToolVersionStatus.CURRENT,
        release_notes: Optional[str] = None,
        changes: Optional[List[str]] = None,
        compatibility: Optional[Dict[str, Any]] = None,
        created_by: Optional[str] = None,
    ) -> ToolVersion:
        """
        Create a new tool version.
        
        Args:
            tool_id: ID of the tool
            version_number: Version number (semantic versioning)
            status: Status of this version
            release_notes: Optional release notes
            changes: Optional list of changes
            compatibility: Optional compatibility information
            created_by: Optional creator identifier
            
        Returns:
            ToolVersion: Created version
            
        Raises:
            ValueError: If the version number is invalid
        """
        # Validate the version number
        await self.parse_version(version_number)
        
        # Create the version
        version = ToolVersion(
            tool_id=tool_id,
            version_number=version_number,
            status=status,
            release_notes=release_notes,
            changes=changes or [],
            compatibility=compatibility or {},
            created_by=created_by,
        )
        
        logger.info(f"Created version {version_number} for tool {tool_id}")
        return version
    
    async def update_version_status(
        self,
        version: ToolVersion,
        new_status: ToolVersionStatus,
    ) -> ToolVersion:
        """
        Update the status of a tool version.
        
        Args:
            version: Tool version to update
            new_status: New status
            
        Returns:
            ToolVersion: Updated version
        """
        # Create a copy of the version with the updated status
        updated_version = ToolVersion(
            tool_id=version.tool_id,
            version_number=version.version_number,
            status=new_status,
            release_notes=version.release_notes,
            changes=version.changes,
            compatibility=version.compatibility,
            created_at=version.created_at,
            created_by=version.created_by,
        )
        
        logger.info(
            f"Updated status of version {version.version_number} for tool {version.tool_id} "
            f"from {version.status} to {new_status}"
        )
        
        return updated_version
    
    async def generate_next_version(
        self,
        current_version: str,
        is_major_update: bool = False,
        is_minor_update: bool = True,
    ) -> str:
        """
        Generate the next version number based on the current version.
        
        Args:
            current_version: Current version string
            is_major_update: Whether this is a major update (breaking changes)
            is_minor_update: Whether this is a minor update (new features)
            
        Returns:
            str: Next version number
            
        Raises:
            ValueError: If the current version is invalid
        """
        major, minor, patch, suffix = await self.parse_version(current_version)
        
        if is_major_update:
            major += 1
            minor = 0
            patch = 0
        elif is_minor_update:
            minor += 1
            patch = 0
        else:
            patch += 1
        
        # Don't carry over suffixes to the next version
        return f"{major}.{minor}.{patch}"
    
    async def check_version_compatibility(
        self,
        tool_id: UUID,
        version1: str,
        version2: str,
    ) -> Dict[str, Any]:
        """
        Check compatibility between two versions of a tool.
        
        Args:
            tool_id: ID of the tool
            version1: First version string
            version2: Second version string
            
        Returns:
            Dict[str, Any]: Compatibility information
            
        Raises:
            ValueError: If either version string is invalid
        """
        # Parse versions
        major1, minor1, patch1, suffix1 = await self.parse_version(version1)
        major2, minor2, patch2, suffix2 = await self.parse_version(version2)
        
        # Check compatibility
        is_compatible = await self.is_compatible(version1, version2)
        is_breaking = await self.is_breaking_change(version1, version2)
        
        # Generate compatibility information
        compatibility_info = {
            "tool_id": str(tool_id),
            "version1": version1,
            "version2": version2,
            "is_compatible": is_compatible,
            "is_breaking_change": is_breaking,
            "details": {
                "major_change": major1 != major2,
                "minor_change": minor1 != minor2,
                "patch_change": patch1 != patch2,
                "suffix_change": suffix1 != suffix2,
            },
            "recommendation": "compatible" if is_compatible else "breaking_change",
        }
        
        logger.debug(
            f"Checked compatibility between versions {version1} and {version2} for tool {tool_id}: "
            f"{'compatible' if is_compatible else 'incompatible'}"
        )
        
        return compatibility_info
