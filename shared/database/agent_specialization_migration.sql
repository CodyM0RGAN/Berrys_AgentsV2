-- Migration script to add agent specialization tables

-- Create agent_specialization table if it doesn't exist
CREATE TABLE IF NOT EXISTS agent_specialization (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_type VARCHAR(50) NOT NULL UNIQUE,
    required_skills JSONB NOT NULL DEFAULT '[]'::jsonb,
    responsibilities JSONB NOT NULL DEFAULT '[]'::jsonb,
    knowledge_domains JSONB NOT NULL DEFAULT '[]'::jsonb,
    specialization_metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Create agent_collaboration_pattern table if it doesn't exist
CREATE TABLE IF NOT EXISTS agent_collaboration_pattern (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_specialization_id UUID NOT NULL REFERENCES agent_specialization(id) ON DELETE CASCADE,
    collaborator_type VARCHAR(50) NOT NULL,
    interaction_type VARCHAR(50) NOT NULL,
    description TEXT,
    pattern_metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Create index on agent_type for faster lookups if it doesn't exist
CREATE INDEX IF NOT EXISTS idx_agent_specialization_agent_type ON agent_specialization(agent_type);


-- Create index on agent_specialization_id for faster lookups if it doesn't exist
CREATE INDEX IF NOT EXISTS idx_agent_collaboration_pattern_agent_specialization_id ON agent_collaboration_pattern(agent_specialization_id);

-- Insert default agent specializations if they don't exist
-- Use WHERE NOT EXISTS to avoid duplicate entries

-- COORDINATOR
INSERT INTO agent_specialization (agent_type, required_skills, responsibilities, knowledge_domains)
SELECT 
    'COORDINATOR', 
    '["Project Management", "Task Coordination", "Resource Allocation"]', 
    '["Coordinate agent activities", "Manage project timeline", "Allocate resources"]', 
    '["Project Management", "Team Coordination"]'
WHERE 
    NOT EXISTS (
        SELECT 1 FROM agent_specialization 
        WHERE agent_type = 'COORDINATOR'
    );

-- ASSISTANT
INSERT INTO agent_specialization (agent_type, required_skills, responsibilities, knowledge_domains)
SELECT 
    'ASSISTANT', 
    '["Information Retrieval", "Task Support", "Documentation"]', 
    '["Provide information", "Support other agents", "Document progress"]', 
    '["Information Management", "Documentation"]'
WHERE 
    NOT EXISTS (
        SELECT 1 FROM agent_specialization 
        WHERE agent_type = 'ASSISTANT'
    );

-- RESEARCHER
INSERT INTO agent_specialization (agent_type, required_skills, responsibilities, knowledge_domains)
SELECT 
    'RESEARCHER', 
    '["Data Analysis", "Information Gathering", "Research Methodology"]', 
    '["Gather information", "Analyze data", "Provide insights"]', 
    '["Research Methods", "Data Analysis"]'
WHERE 
    NOT EXISTS (
        SELECT 1 FROM agent_specialization 
        WHERE agent_type = 'RESEARCHER'
    );

-- DEVELOPER
INSERT INTO agent_specialization (agent_type, required_skills, responsibilities, knowledge_domains)
SELECT 
    'DEVELOPER', 
    '["Programming", "Software Design", "Testing"]', 
    '["Implement features", "Fix bugs", "Write tests"]', 
    '["Software Development", "Programming Languages"]'
WHERE 
    NOT EXISTS (
        SELECT 1 FROM agent_specialization 
        WHERE agent_type = 'DEVELOPER'
    );

-- DESIGNER
INSERT INTO agent_specialization (agent_type, required_skills, responsibilities, knowledge_domains)
SELECT 
    'DESIGNER', 
    '["UI/UX Design", "Visual Design", "Prototyping"]', 
    '["Create designs", "Develop prototypes", "Improve user experience"]', 
    '["Design Principles", "User Experience"]'
WHERE 
    NOT EXISTS (
        SELECT 1 FROM agent_specialization 
        WHERE agent_type = 'DESIGNER'
    );

-- SPECIALIST
INSERT INTO agent_specialization (agent_type, required_skills, responsibilities, knowledge_domains)
SELECT 
    'SPECIALIST', 
    '["Domain Expertise", "Specialized Knowledge", "Problem Solving"]', 
    '["Provide domain expertise", "Solve complex problems", "Advise other agents"]', 
    '["Specialized Domain"]'
WHERE 
    NOT EXISTS (
        SELECT 1 FROM agent_specialization 
        WHERE agent_type = 'SPECIALIST'
    );

-- AUDITOR
INSERT INTO agent_specialization (agent_type, required_skills, responsibilities, knowledge_domains)
SELECT 
    'AUDITOR', 
    '["Quality Assurance", "Testing", "Compliance Checking"]', 
    '["Verify quality", "Ensure compliance", "Identify issues"]', 
    '["Quality Assurance", "Compliance"]'
WHERE 
    NOT EXISTS (
        SELECT 1 FROM agent_specialization 
        WHERE agent_type = 'AUDITOR'
    );

-- CUSTOM
INSERT INTO agent_specialization (agent_type, required_skills, responsibilities, knowledge_domains)
SELECT 
    'CUSTOM', 
    '["Adaptability", "Versatility", "Specialized Knowledge"]', 
    '["Perform custom tasks", "Adapt to project needs"]', 
    '["Project-Specific Domain"]'
WHERE 
    NOT EXISTS (
        SELECT 1 FROM agent_specialization 
        WHERE agent_type = 'CUSTOM'
    );

-- Insert default collaboration patterns for COORDINATOR if they don't exist
-- Use a WHERE NOT EXISTS clause to avoid duplicate entries
INSERT INTO agent_collaboration_pattern (agent_specialization_id, collaborator_type, interaction_type, description)
SELECT 
    id, 
    'DEVELOPER', 
    'ASSIGN_TASK', 
    'Assign development tasks'
FROM 
    agent_specialization AS spec
WHERE 
    spec.agent_type = 'COORDINATOR'
    AND NOT EXISTS (
        SELECT 1 FROM agent_collaboration_pattern 
        WHERE agent_specialization_id = spec.id 
        AND collaborator_type = 'DEVELOPER'
        AND interaction_type = 'ASSIGN_TASK'
    );

-- Only insert if no similar pattern exists
-- Use a WHERE NOT EXISTS clause to avoid duplicate entries
INSERT INTO agent_collaboration_pattern (agent_specialization_id, collaborator_type, interaction_type, description)
SELECT 
    id, 
    'DESIGNER', 
    'ASSIGN_TASK', 
    'Assign design tasks'
FROM 
    agent_specialization AS spec
WHERE 
    spec.agent_type = 'COORDINATOR'
    AND NOT EXISTS (
        SELECT 1 FROM agent_collaboration_pattern 
        WHERE agent_specialization_id = spec.id 
        AND collaborator_type = 'DESIGNER'
        AND interaction_type = 'ASSIGN_TASK'
    );

-- Insert default collaboration patterns for ASSISTANT if they don't exist
-- Use a WHERE NOT EXISTS clause to avoid duplicate entries
INSERT INTO agent_collaboration_pattern (agent_specialization_id, collaborator_type, interaction_type, description)
SELECT 
    id, 
    'COORDINATOR', 
    'PROVIDE_INFORMATION', 
    'Provide status updates'
FROM 
    agent_specialization AS spec
WHERE 
    spec.agent_type = 'ASSISTANT'
    AND NOT EXISTS (
        SELECT 1 FROM agent_collaboration_pattern 
        WHERE agent_specialization_id = spec.id 
        AND collaborator_type = 'COORDINATOR'
        AND interaction_type = 'PROVIDE_INFORMATION'
    );

-- Insert default collaboration patterns for RESEARCHER if they don't exist
-- Use a WHERE NOT EXISTS clause to avoid duplicate entries
INSERT INTO agent_collaboration_pattern (agent_specialization_id, collaborator_type, interaction_type, description)
SELECT 
    id, 
    'DEVELOPER', 
    'PROVIDE_INFORMATION', 
    'Provide research findings'
FROM 
    agent_specialization AS spec
WHERE 
    spec.agent_type = 'RESEARCHER'
    AND NOT EXISTS (
        SELECT 1 FROM agent_collaboration_pattern 
        WHERE agent_specialization_id = spec.id 
        AND collaborator_type = 'DEVELOPER'
        AND interaction_type = 'PROVIDE_INFORMATION'
    );

-- Insert default collaboration patterns for DEVELOPER if they don't exist
-- Use a WHERE NOT EXISTS clause to avoid duplicate entries
INSERT INTO agent_collaboration_pattern (agent_specialization_id, collaborator_type, interaction_type, description)
SELECT 
    id, 
    'DESIGNER', 
    'REQUEST_INFORMATION', 
    'Request design specifications'
FROM 
    agent_specialization AS spec
WHERE 
    spec.agent_type = 'DEVELOPER'
    AND NOT EXISTS (
        SELECT 1 FROM agent_collaboration_pattern 
        WHERE agent_specialization_id = spec.id 
        AND collaborator_type = 'DESIGNER'
        AND interaction_type = 'REQUEST_INFORMATION'
    );

-- Insert default collaboration patterns for DESIGNER if they don't exist
-- Use a WHERE NOT EXISTS clause to avoid duplicate entries
INSERT INTO agent_collaboration_pattern (agent_specialization_id, collaborator_type, interaction_type, description)
SELECT 
    id, 
    'DEVELOPER', 
    'PROVIDE_INFORMATION', 
    'Provide design specifications'
FROM 
    agent_specialization AS spec
WHERE 
    spec.agent_type = 'DESIGNER'
    AND NOT EXISTS (
        SELECT 1 FROM agent_collaboration_pattern 
        WHERE agent_specialization_id = spec.id 
        AND collaborator_type = 'DEVELOPER'
        AND interaction_type = 'PROVIDE_INFORMATION'
    );

-- Insert default collaboration patterns for SPECIALIST if they don't exist
-- Use a WHERE NOT EXISTS clause to avoid duplicate entries
INSERT INTO agent_collaboration_pattern (agent_specialization_id, collaborator_type, interaction_type, description)
SELECT 
    id, 
    'DEVELOPER', 
    'PROVIDE_INFORMATION', 
    'Provide domain expertise'
FROM 
    agent_specialization AS spec
WHERE 
    spec.agent_type = 'SPECIALIST'
    AND NOT EXISTS (
        SELECT 1 FROM agent_collaboration_pattern 
        WHERE agent_specialization_id = spec.id 
        AND collaborator_type = 'DEVELOPER'
        AND interaction_type = 'PROVIDE_INFORMATION'
    );

-- Insert default collaboration patterns for AUDITOR if they don't exist
-- Use a WHERE NOT EXISTS clause to avoid duplicate entries
INSERT INTO agent_collaboration_pattern (agent_specialization_id, collaborator_type, interaction_type, description)
SELECT 
    id, 
    'DEVELOPER', 
    'PROVIDE_FEEDBACK', 
    'Provide quality feedback'
FROM 
    agent_specialization AS spec
WHERE 
    spec.agent_type = 'AUDITOR'
    AND NOT EXISTS (
        SELECT 1 FROM agent_collaboration_pattern 
        WHERE agent_specialization_id = spec.id 
        AND collaborator_type = 'DEVELOPER'
        AND interaction_type = 'PROVIDE_FEEDBACK'
    );

-- Insert default collaboration patterns for CUSTOM if they don't exist
-- Use a WHERE NOT EXISTS clause to avoid duplicate entries
INSERT INTO agent_collaboration_pattern (agent_specialization_id, collaborator_type, interaction_type, description)
SELECT 
    id, 
    'COORDINATOR', 
    'RECEIVE_INSTRUCTIONS', 
    'Receive custom instructions'
FROM 
    agent_specialization AS spec
WHERE 
    spec.agent_type = 'CUSTOM'
    AND NOT EXISTS (
        SELECT 1 FROM agent_collaboration_pattern 
        WHERE agent_specialization_id = spec.id 
        AND collaborator_type = 'COORDINATOR'
        AND interaction_type = 'RECEIVE_INSTRUCTIONS'
    );
