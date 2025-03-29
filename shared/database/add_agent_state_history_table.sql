-- Migration script to add agent_state_history table

-- Create agent_state_history table
CREATE TABLE agent_state_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID REFERENCES agent(id) ON DELETE CASCADE,
    previous_status VARCHAR(20),
    new_status VARCHAR(20) NOT NULL,
    previous_state_detail VARCHAR(20),
    new_state_detail VARCHAR(20),
    reason TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index on agent_id
CREATE INDEX ix_agent_state_history_agent_id ON agent_state_history USING btree (agent_id);

-- Create index on timestamp
CREATE INDEX ix_agent_state_history_timestamp ON agent_state_history USING btree (timestamp);

-- Log the migration
INSERT INTO audit_log (id, entity_id, entity_type, action, previous_state, new_state, actor_id)
VALUES (
    gen_random_uuid(),
    gen_random_uuid(),
    'database_schema',
    'create_table',
    '{"tables": ["agent"]}',
    '{"tables": ["agent", "agent_state_history"]}',
    NULL
);
