-- Rename metadata columns to avoid SQLAlchemy reserved name conflicts

-- Web Dashboard Service
-- Rename project.metadata to project.project_metadata
ALTER TABLE project RENAME COLUMN metadata TO project_metadata;

-- Rename tool.metadata to tool.tool_metadata
ALTER TABLE tool RENAME COLUMN metadata TO tool_metadata;

-- Project Coordinator Service
-- Rename chat_sessions.metadata to chat_sessions.session_metadata
ALTER TABLE chat_sessions RENAME COLUMN metadata TO session_metadata;

-- Rename chat_messages.metadata to chat_messages.message_metadata
ALTER TABLE chat_messages RENAME COLUMN metadata TO message_metadata;
