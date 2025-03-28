-- Migration script to add collaboration pattern tables

-- Create collaboration_pattern table if it doesn't exist
CREATE TABLE IF NOT EXISTS collaboration_pattern (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_agent_type VARCHAR(50) NOT NULL,
    target_agent_type VARCHAR(50) NOT NULL,
    interaction_type VARCHAR(100) NOT NULL,
    description TEXT,
    priority INTEGER NOT NULL DEFAULT 1,
    metadata JSONB,
    source_agent_id UUID,
    target_agent_id UUID,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_collaboration_pattern_source_agent_type ON collaboration_pattern(source_agent_type);
CREATE INDEX IF NOT EXISTS idx_collaboration_pattern_target_agent_type ON collaboration_pattern(target_agent_type);
CREATE INDEX IF NOT EXISTS idx_collaboration_pattern_interaction_type ON collaboration_pattern(interaction_type);
CREATE INDEX IF NOT EXISTS idx_collaboration_pattern_source_agent_id ON collaboration_pattern(source_agent_id);
CREATE INDEX IF NOT EXISTS idx_collaboration_pattern_target_agent_id ON collaboration_pattern(target_agent_id);

-- Insert default collaboration patterns if they don't exist
-- COORDINATOR -> DEVELOPER
INSERT INTO collaboration_pattern (source_agent_type, target_agent_type, interaction_type, description, priority)
SELECT 
    'COORDINATOR', 
    'DEVELOPER', 
    'ASSIGN_TASK', 
    'Assign development tasks',
    3
WHERE 
    NOT EXISTS (
        SELECT 1 FROM collaboration_pattern 
        WHERE source_agent_type = 'COORDINATOR' 
        AND target_agent_type = 'DEVELOPER'
        AND interaction_type = 'ASSIGN_TASK'
    );

-- COORDINATOR -> DESIGNER
INSERT INTO collaboration_pattern (source_agent_type, target_agent_type, interaction_type, description, priority)
SELECT 
    'COORDINATOR', 
    'DESIGNER', 
    'ASSIGN_TASK', 
    'Assign design tasks',
    3
WHERE 
    NOT EXISTS (
        SELECT 1 FROM collaboration_pattern 
        WHERE source_agent_type = 'COORDINATOR' 
        AND target_agent_type = 'DESIGNER'
        AND interaction_type = 'ASSIGN_TASK'
    );

-- COORDINATOR -> RESEARCHER
INSERT INTO collaboration_pattern (source_agent_type, target_agent_type, interaction_type, description, priority)
SELECT 
    'COORDINATOR', 
    'RESEARCHER', 
    'ASSIGN_TASK', 
    'Assign research tasks',
    3
WHERE 
    NOT EXISTS (
        SELECT 1 FROM collaboration_pattern 
        WHERE source_agent_type = 'COORDINATOR' 
        AND target_agent_type = 'RESEARCHER'
        AND interaction_type = 'ASSIGN_TASK'
    );

-- DEVELOPER -> DESIGNER
INSERT INTO collaboration_pattern (source_agent_type, target_agent_type, interaction_type, description, priority)
SELECT 
    'DEVELOPER', 
    'DESIGNER', 
    'REQUEST_INFORMATION', 
    'Request design specifications',
    2
WHERE 
    NOT EXISTS (
        SELECT 1 FROM collaboration_pattern 
        WHERE source_agent_type = 'DEVELOPER' 
        AND target_agent_type = 'DESIGNER'
        AND interaction_type = 'REQUEST_INFORMATION'
    );

-- DESIGNER -> DEVELOPER
INSERT INTO collaboration_pattern (source_agent_type, target_agent_type, interaction_type, description, priority)
SELECT 
    'DESIGNER', 
    'DEVELOPER', 
    'PROVIDE_INFORMATION', 
    'Provide design specifications',
    2
WHERE 
    NOT EXISTS (
        SELECT 1 FROM collaboration_pattern 
        WHERE source_agent_type = 'DESIGNER' 
        AND target_agent_type = 'DEVELOPER'
        AND interaction_type = 'PROVIDE_INFORMATION'
    );

-- RESEARCHER -> DEVELOPER
INSERT INTO collaboration_pattern (source_agent_type, target_agent_type, interaction_type, description, priority)
SELECT 
    'RESEARCHER', 
    'DEVELOPER', 
    'PROVIDE_INFORMATION', 
    'Provide research findings',
    2
WHERE 
    NOT EXISTS (
        SELECT 1 FROM collaboration_pattern 
        WHERE source_agent_type = 'RESEARCHER' 
        AND target_agent_type = 'DEVELOPER'
        AND interaction_type = 'PROVIDE_INFORMATION'
    );

-- DEVELOPER -> COORDINATOR
INSERT INTO collaboration_pattern (source_agent_type, target_agent_type, interaction_type, description, priority)
SELECT 
    'DEVELOPER', 
    'COORDINATOR', 
    'PROVIDE_STATUS_UPDATE', 
    'Provide development status update',
    2
WHERE 
    NOT EXISTS (
        SELECT 1 FROM collaboration_pattern 
        WHERE source_agent_type = 'DEVELOPER' 
        AND target_agent_type = 'COORDINATOR'
        AND interaction_type = 'PROVIDE_STATUS_UPDATE'
    );

-- DESIGNER -> COORDINATOR
INSERT INTO collaboration_pattern (source_agent_type, target_agent_type, interaction_type, description, priority)
SELECT 
    'DESIGNER', 
    'COORDINATOR', 
    'PROVIDE_STATUS_UPDATE', 
    'Provide design status update',
    2
WHERE 
    NOT EXISTS (
        SELECT 1 FROM collaboration_pattern 
        WHERE source_agent_type = 'DESIGNER' 
        AND target_agent_type = 'COORDINATOR'
        AND interaction_type = 'PROVIDE_STATUS_UPDATE'
    );

-- RESEARCHER -> COORDINATOR
INSERT INTO collaboration_pattern (source_agent_type, target_agent_type, interaction_type, description, priority)
SELECT 
    'RESEARCHER', 
    'COORDINATOR', 
    'PROVIDE_STATUS_UPDATE', 
    'Provide research status update',
    2
WHERE 
    NOT EXISTS (
        SELECT 1 FROM collaboration_pattern 
        WHERE source_agent_type = 'RESEARCHER' 
        AND target_agent_type = 'COORDINATOR'
        AND interaction_type = 'PROVIDE_STATUS_UPDATE'
    );

-- DEVELOPER -> AUDITOR
INSERT INTO collaboration_pattern (source_agent_type, target_agent_type, interaction_type, description, priority)
SELECT 
    'DEVELOPER', 
    'AUDITOR', 
    'REQUEST_REVIEW', 
    'Request code review',
    2
WHERE 
    NOT EXISTS (
        SELECT 1 FROM collaboration_pattern 
        WHERE source_agent_type = 'DEVELOPER' 
        AND target_agent_type = 'AUDITOR'
        AND interaction_type = 'REQUEST_REVIEW'
    );

-- AUDITOR -> DEVELOPER
INSERT INTO collaboration_pattern (source_agent_type, target_agent_type, interaction_type, description, priority)
SELECT 
    'AUDITOR', 
    'DEVELOPER', 
    'PROVIDE_FEEDBACK', 
    'Provide code review feedback',
    2
WHERE 
    NOT EXISTS (
        SELECT 1 FROM collaboration_pattern 
        WHERE source_agent_type = 'AUDITOR' 
        AND target_agent_type = 'DEVELOPER'
        AND interaction_type = 'PROVIDE_FEEDBACK'
    );

-- DESIGNER -> AUDITOR
INSERT INTO collaboration_pattern (source_agent_type, target_agent_type, interaction_type, description, priority)
SELECT 
    'DESIGNER', 
    'AUDITOR', 
    'REQUEST_REVIEW', 
    'Request design review',
    2
WHERE 
    NOT EXISTS (
        SELECT 1 FROM collaboration_pattern 
        WHERE source_agent_type = 'DESIGNER' 
        AND target_agent_type = 'AUDITOR'
        AND interaction_type = 'REQUEST_REVIEW'
    );

-- AUDITOR -> DESIGNER
INSERT INTO collaboration_pattern (source_agent_type, target_agent_type, interaction_type, description, priority)
SELECT 
    'AUDITOR', 
    'DESIGNER', 
    'PROVIDE_FEEDBACK', 
    'Provide design review feedback',
    2
WHERE 
    NOT EXISTS (
        SELECT 1 FROM collaboration_pattern 
        WHERE source_agent_type = 'AUDITOR' 
        AND target_agent_type = 'DESIGNER'
        AND interaction_type = 'PROVIDE_FEEDBACK'
    );

-- SPECIALIST -> DEVELOPER
INSERT INTO collaboration_pattern (source_agent_type, target_agent_type, interaction_type, description, priority)
SELECT 
    'SPECIALIST', 
    'DEVELOPER', 
    'PROVIDE_DOMAIN_KNOWLEDGE', 
    'Provide domain expertise',
    2
WHERE 
    NOT EXISTS (
        SELECT 1 FROM collaboration_pattern 
        WHERE source_agent_type = 'SPECIALIST' 
        AND target_agent_type = 'DEVELOPER'
        AND interaction_type = 'PROVIDE_DOMAIN_KNOWLEDGE'
    );

-- SPECIALIST -> DESIGNER
INSERT INTO collaboration_pattern (source_agent_type, target_agent_type, interaction_type, description, priority)
SELECT 
    'SPECIALIST', 
    'DESIGNER', 
    'PROVIDE_DOMAIN_KNOWLEDGE', 
    'Provide domain expertise for design',
    2
WHERE 
    NOT EXISTS (
        SELECT 1 FROM collaboration_pattern 
        WHERE source_agent_type = 'SPECIALIST' 
        AND target_agent_type = 'DESIGNER'
        AND interaction_type = 'PROVIDE_DOMAIN_KNOWLEDGE'
    );

-- DEVELOPER -> SPECIALIST
INSERT INTO collaboration_pattern (source_agent_type, target_agent_type, interaction_type, description, priority)
SELECT 
    'DEVELOPER', 
    'SPECIALIST', 
    'REQUEST_DOMAIN_KNOWLEDGE', 
    'Request domain expertise',
    2
WHERE 
    NOT EXISTS (
        SELECT 1 FROM collaboration_pattern 
        WHERE source_agent_type = 'DEVELOPER' 
        AND target_agent_type = 'SPECIALIST'
        AND interaction_type = 'REQUEST_DOMAIN_KNOWLEDGE'
    );

-- DESIGNER -> SPECIALIST
INSERT INTO collaboration_pattern (source_agent_type, target_agent_type, interaction_type, description, priority)
SELECT 
    'DESIGNER', 
    'SPECIALIST', 
    'REQUEST_DOMAIN_KNOWLEDGE', 
    'Request domain expertise for design',
    2
WHERE 
    NOT EXISTS (
        SELECT 1 FROM collaboration_pattern 
        WHERE source_agent_type = 'DESIGNER' 
        AND target_agent_type = 'SPECIALIST'
        AND interaction_type = 'REQUEST_DOMAIN_KNOWLEDGE'
    );

-- ASSISTANT -> COORDINATOR
INSERT INTO collaboration_pattern (source_agent_type, target_agent_type, interaction_type, description, priority)
SELECT 
    'ASSISTANT', 
    'COORDINATOR', 
    'PROVIDE_INFORMATION', 
    'Provide status updates',
    1
WHERE 
    NOT EXISTS (
        SELECT 1 FROM collaboration_pattern 
        WHERE source_agent_type = 'ASSISTANT' 
        AND target_agent_type = 'COORDINATOR'
        AND interaction_type = 'PROVIDE_INFORMATION'
    );

-- COORDINATOR -> ASSISTANT
INSERT INTO collaboration_pattern (source_agent_type, target_agent_type, interaction_type, description, priority)
SELECT 
    'COORDINATOR', 
    'ASSISTANT', 
    'REQUEST_INFORMATION', 
    'Request status updates',
    1
WHERE 
    NOT EXISTS (
        SELECT 1 FROM collaboration_pattern 
        WHERE source_agent_type = 'COORDINATOR' 
        AND target_agent_type = 'ASSISTANT'
        AND interaction_type = 'REQUEST_INFORMATION'
    );

-- CUSTOM -> COORDINATOR
INSERT INTO collaboration_pattern (source_agent_type, target_agent_type, interaction_type, description, priority)
SELECT 
    'CUSTOM', 
    'COORDINATOR', 
    'RECEIVE_INSTRUCTIONS', 
    'Receive custom instructions',
    2
WHERE 
    NOT EXISTS (
        SELECT 1 FROM collaboration_pattern 
        WHERE source_agent_type = 'CUSTOM' 
        AND target_agent_type = 'COORDINATOR'
        AND interaction_type = 'RECEIVE_INSTRUCTIONS'
    );

-- COORDINATOR -> CUSTOM
INSERT INTO collaboration_pattern (source_agent_type, target_agent_type, interaction_type, description, priority)
SELECT 
    'COORDINATOR', 
    'CUSTOM', 
    'PROVIDE_INSTRUCTIONS', 
    'Provide custom instructions',
    2
WHERE 
    NOT EXISTS (
        SELECT 1 FROM collaboration_pattern 
        WHERE source_agent_type = 'COORDINATOR' 
        AND target_agent_type = 'CUSTOM'
        AND interaction_type = 'PROVIDE_INSTRUCTIONS'
    );
