-- Agent Template Engine Migration Script
-- This script creates the template_tag_mapping table for the Agent Template Engine.

-- Create template_tag_mapping table if it doesn't exist
CREATE TABLE IF NOT EXISTS template_tag_mapping (
    template_id character varying(50) NOT NULL REFERENCES agent_template(id) ON DELETE CASCADE,
    tag_id uuid NOT NULL REFERENCES template_tag(id) ON DELETE CASCADE,
    PRIMARY KEY (template_id, tag_id)
);

-- Create indexes for template_tag_mapping
CREATE INDEX IF NOT EXISTS idx_template_tag_mapping_template_id ON template_tag_mapping(template_id);
CREATE INDEX IF NOT EXISTS idx_template_tag_mapping_tag_id ON template_tag_mapping(tag_id);

-- Insert default template tags
INSERT INTO template_tag (name, description)
VALUES 
    ('Development', 'Templates for development tasks'),
    ('Design', 'Templates for design tasks'),
    ('Research', 'Templates for research tasks'),
    ('Analysis', 'Templates for analysis tasks'),
    ('Documentation', 'Templates for documentation tasks'),
    ('Testing', 'Templates for testing tasks'),
    ('DevOps', 'Templates for DevOps tasks'),
    ('Security', 'Templates for security tasks'),
    ('Data Science', 'Templates for data science tasks'),
    ('Machine Learning', 'Templates for machine learning tasks')
ON CONFLICT (name) DO NOTHING;

-- Add template tags to templates
INSERT INTO template_tag_mapping (
    template_id,
    tag_id
)
SELECT 
    agent_template.id,
    template_tag.id
FROM 
    agent_template,
    template_tag
WHERE 
    agent_template.agent_type = 'DEVELOPER'
    AND template_tag.name = 'Development'
    AND NOT EXISTS (
        SELECT 1 
        FROM template_tag_mapping 
        WHERE template_tag_mapping.template_id = agent_template.id
        AND template_tag_mapping.tag_id = template_tag.id
    );

INSERT INTO template_tag_mapping (
    template_id,
    tag_id
)
SELECT 
    agent_template.id,
    template_tag.id
FROM 
    agent_template,
    template_tag
WHERE 
    agent_template.agent_type = 'DESIGNER'
    AND template_tag.name = 'Design'
    AND NOT EXISTS (
        SELECT 1 
        FROM template_tag_mapping 
        WHERE template_tag_mapping.template_id = agent_template.id
        AND template_tag_mapping.tag_id = template_tag.id
    );

INSERT INTO template_tag_mapping (
    template_id,
    tag_id
)
SELECT 
    agent_template.id,
    template_tag.id
FROM 
    agent_template,
    template_tag
WHERE 
    agent_template.agent_type = 'RESEARCHER'
    AND template_tag.name = 'Research'
    AND NOT EXISTS (
        SELECT 1 
        FROM template_tag_mapping 
        WHERE template_tag_mapping.template_id = agent_template.id
        AND template_tag_mapping.tag_id = template_tag.id
    );
