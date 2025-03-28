"""
Artifact Store for Project Coordinator service.

This module provides functionality for storing and retrieving project artifacts.
"""
import logging
import os
import shutil
from typing import List, Dict, Any, Optional, BinaryIO
from uuid import UUID
from datetime import datetime
import hashlib
import mimetypes
import aiofiles
from pathlib import Path
from fastapi import UploadFile, HTTPException

from ...repositories.project import ProjectRepository
from ...exceptions import ArtifactStorageError, ProjectNotFoundError, ProjectLimitExceededError
from ...models.api import ArtifactType, ArtifactCreateRequest
from ...config import Settings


class ArtifactStore:
    """
    Artifact Store service.
    
    This service manages project artifact storage and retrieval.
    
    Attributes:
        project_repo: Project repository
        settings: Application settings
        logger: Logger instance
        base_storage_path: Base path for artifact storage
    """
    
    def __init__(
        self,
        project_repo: ProjectRepository,
        settings: Settings,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the Artifact Store.
        
        Args:
            project_repo: Project repository
            settings: Application settings
            logger: Logger instance (optional)
        """
        self.project_repo = project_repo
        self.settings = settings
        self.logger = logger or logging.getLogger("artifact_store")
        self.base_storage_path = Path(settings.artifact_storage_path)
        
        # Create base storage directory if it doesn't exist
        self.base_storage_path.mkdir(parents=True, exist_ok=True)
    
    async def store_artifact(
        self, 
        project_id: UUID, 
        artifact_data: ArtifactCreateRequest,
        file: UploadFile
    ) -> Dict[str, Any]:
        """
        Store an artifact for a project.
        
        Args:
            project_id: Project ID
            artifact_data: Artifact metadata
            file: Uploaded file
            
        Returns:
            Created artifact
            
        Raises:
            ProjectNotFoundError: If project not found
            ArtifactStorageError: If artifact storage fails
            ProjectLimitExceededError: If artifact limit is exceeded
        """
        self.logger.info(f"Storing artifact {artifact_data.name} for project {project_id}")
        
        # Ensure project exists
        project = self.project_repo.get_project_or_404(project_id)
        
        # Check artifact limit
        existing_artifacts = self.project_repo.get_project_artifacts(project_id)
        if len(existing_artifacts) >= self.settings.max_artifacts_per_project:
            raise ProjectLimitExceededError(
                message=f"Maximum number of artifacts ({self.settings.max_artifacts_per_project}) reached for project {project_id}",
                limit_type="artifacts",
                current_value=len(existing_artifacts),
                max_value=self.settings.max_artifacts_per_project
            )
        
        try:
            # Create storage path for project if it doesn't exist
            project_storage_path = self.base_storage_path / str(project_id)
            project_storage_path.mkdir(parents=True, exist_ok=True)
            
            # Generate file hash for deduplication
            file_content = await file.read()
            file_hash = hashlib.sha256(file_content).hexdigest()
            
            # Reset file position for writing
            await file.seek(0)
            
            # Determine file extension from content type
            content_type = file.content_type
            extension = self._get_extension_from_content_type(content_type)
            if not extension and file.filename:
                extension = os.path.splitext(file.filename)[1]
            
            # Generate storage filename
            filename = f"{file_hash}{extension}"
            storage_path = project_storage_path / filename
            
            # Save file to storage
            async with aiofiles.open(storage_path, "wb") as f:
                await f.write(file_content)
            
            # Get file size
            size_bytes = os.path.getsize(storage_path)
            
            # Store artifact metadata in database
            artifact = self.project_repo.add_artifact(
                project_id=project_id,
                name=artifact_data.name,
                artifact_type=artifact_data.type.value,
                storage_path=str(storage_path),
                size_bytes=size_bytes,
                description=artifact_data.description,
                metadata=artifact_data.metadata
            )
            
            return {
                "id": artifact.id,
                "project_id": artifact.project_id,
                "name": artifact.name,
                "type": artifact.type,
                "description": artifact.description,
                "created_at": artifact.created_at,
                "updated_at": artifact.updated_at,
                "size_bytes": artifact.size_bytes,
                "metadata": artifact.artifact_metadata or {}
            }
            
        except ArtifactStorageError:
            raise
        except Exception as e:
            self.logger.exception(f"Error storing artifact: {str(e)}")
            raise ArtifactStorageError(
                message=f"Failed to store artifact: {str(e)}"
            )
    
    def get_artifacts(
        self, 
        project_id: UUID,
        artifact_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get artifacts for a project.
        
        Args:
            project_id: Project ID
            artifact_type: Optional filter by artifact type
            
        Returns:
            List of artifacts
            
        Raises:
            ProjectNotFoundError: If project not found
        """
        self.logger.info(f"Getting artifacts for project: {project_id}")
        
        # Ensure project exists
        self.project_repo.get_project_or_404(project_id)
        
        # Get artifacts from database
        artifacts = self.project_repo.get_project_artifacts(
            project_id=project_id,
            artifact_type=artifact_type
        )
        
        return [
            {
                "id": artifact.id,
                "project_id": artifact.project_id,
                "name": artifact.name,
                "type": artifact.type,
                "description": artifact.description,
                "created_at": artifact.created_at,
                "updated_at": artifact.updated_at,
                "size_bytes": artifact.size_bytes,
                "metadata": artifact.artifact_metadata or {}
            }
            for artifact in artifacts
        ]
    
    def get_artifact(
        self, 
        project_id: UUID, 
        artifact_id: UUID
    ) -> Dict[str, Any]:
        """
        Get artifact details.
        
        Args:
            project_id: Project ID
            artifact_id: Artifact ID
            
        Returns:
            Artifact details
            
        Raises:
            ProjectNotFoundError: If project not found
            ArtifactStorageError: If artifact not found
        """
        self.logger.info(f"Getting artifact {artifact_id} from project {project_id}")
        
        # Ensure project exists
        self.project_repo.get_project_or_404(project_id)
        
        # Get artifact from database
        artifact = self.project_repo.get_artifact(artifact_id)
        
        if not artifact or artifact.project_id != project_id:
            raise ArtifactStorageError(
                message=f"Artifact {artifact_id} not found in project {project_id}",
                artifact_id=str(artifact_id)
            )
        
        return {
            "id": artifact.id,
            "project_id": artifact.project_id,
            "name": artifact.name,
            "type": artifact.type,
            "description": artifact.description,
            "created_at": artifact.created_at,
            "updated_at": artifact.updated_at,
            "size_bytes": artifact.size_bytes,
            "metadata": artifact.artifact_metadata or {}
        }
    
    async def get_artifact_content(
        self, 
        project_id: UUID, 
        artifact_id: UUID
    ) -> tuple[str, BinaryIO]:
        """
        Get artifact content.
        
        Args:
            project_id: Project ID
            artifact_id: Artifact ID
            
        Returns:
            Tuple of (content_type, file_handle)
            
        Raises:
            ProjectNotFoundError: If project not found
            ArtifactStorageError: If artifact not found or cannot be read
        """
        self.logger.info(f"Getting artifact content for {artifact_id} from project {project_id}")
        
        # Get artifact details
        artifact = self.get_artifact(project_id, artifact_id)
        
        # Check if file exists
        storage_path = artifact.get("storage_path")
        if not storage_path or not os.path.exists(storage_path):
            raise ArtifactStorageError(
                message=f"Artifact file not found: {storage_path}",
                artifact_id=str(artifact_id)
            )
        
        try:
            # Determine content type
            content_type, _ = mimetypes.guess_type(storage_path)
            content_type = content_type or "application/octet-stream"
            
            # Open file
            file_handle = open(storage_path, "rb")
            
            return content_type, file_handle
            
        except Exception as e:
            self.logger.exception(f"Error reading artifact file: {str(e)}")
            raise ArtifactStorageError(
                message=f"Failed to read artifact file: {str(e)}",
                artifact_id=str(artifact_id)
            )
    
    def delete_artifact(
        self, 
        project_id: UUID, 
        artifact_id: UUID
    ) -> Dict[str, Any]:
        """
        Delete an artifact.
        
        Args:
            project_id: Project ID
            artifact_id: Artifact ID
            
        Returns:
            Deleted artifact details
            
        Raises:
            ProjectNotFoundError: If project not found
            ArtifactStorageError: If artifact not found or cannot be deleted
        """
        self.logger.info(f"Deleting artifact {artifact_id} from project {project_id}")
        
        # Get artifact details
        artifact = self.get_artifact(project_id, artifact_id)
        
        # Check if file exists
        storage_path = artifact.get("storage_path")
        
        try:
            # Delete file from storage if it exists
            if storage_path and os.path.exists(storage_path):
                os.remove(storage_path)
            
            # Delete from database
            self.project_repo.delete_artifact(artifact_id)
            
            return {
                "id": artifact_id,
                "project_id": project_id,
                "deleted": True
            }
            
        except Exception as e:
            self.logger.exception(f"Error deleting artifact: {str(e)}")
            raise ArtifactStorageError(
                message=f"Failed to delete artifact: {str(e)}",
                artifact_id=str(artifact_id)
            )
    
    def _get_extension_from_content_type(self, content_type: str) -> str:
        """
        Get file extension from content type.
        
        Args:
            content_type: Content type
            
        Returns:
            File extension including dot (e.g., ".pdf")
        """
        if not content_type:
            return ""
        
        extension = mimetypes.guess_extension(content_type)
        return extension or ""
