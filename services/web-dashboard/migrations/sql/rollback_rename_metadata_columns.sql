-- Rollback script for metadata column renames

-- Web Dashboard Service
-- Revert project.project_metadata to project.metadata
ALTER TABLE project RENAME COLUMN project_metadata TO metadata;

-- Revert tool.tool_metadata to tool.metadata
ALTER TABLE tool RENAME COLUMN tool_metadata TO metadata;

-- Project Coordinator Service
-- Revert chat_sessions.session_metadata to chat_sessions.metadata
ALTER TABLE chat_sessions RENAME COLUMN session_metadata TO metadata;

-- Revert chat_messages.message_metadata to chat_messages.metadata
ALTER TABLE chat_messages RENAME COLUMN message_metadata TO metadata;
