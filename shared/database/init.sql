-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- Users table
CREATE TABLE "user" (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(100) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    role VARCHAR(20) NOT NULL DEFAULT 'USER',
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    permissions JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Projects table
CREATE TABLE project (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    owner_id UUID REFERENCES "user"(id),
    status VARCHAR(20) NOT NULL DEFAULT 'DRAFT',
    project_metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Agents table
CREATE TABLE agent (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES project(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL,
    configuration JSONB NOT NULL,
    prompt_template TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'CREATED',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tasks table
CREATE TABLE task (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES project(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES agent(id),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    priority INTEGER NOT NULL DEFAULT 3,
    start_date TIMESTAMP WITH TIME ZONE,
    due_date TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    result JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Task dependencies
CREATE TABLE task_dependencies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dependent_task_id UUID REFERENCES task(id) ON DELETE CASCADE,
    dependency_task_id UUID REFERENCES task(id) ON DELETE CASCADE,
    dependency_type VARCHAR(20) NOT NULL DEFAULT 'FINISH_TO_START',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(dependent_task_id, dependency_task_id)
);

-- Tools table
CREATE TABLE tool (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    capability VARCHAR(100) NOT NULL,
    source VARCHAR(50) NOT NULL,
    documentation_url TEXT,
    schema JSONB,
    integration_type VARCHAR(50),
    status VARCHAR(20) NOT NULL DEFAULT 'DISCOVERED',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Agent tools junction table
CREATE TABLE agent_tools (
    agent_id UUID REFERENCES agent(id) ON DELETE CASCADE,
    tool_id UUID REFERENCES tool(id) ON DELETE CASCADE,
    configuration JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (agent_id, tool_id)
);

-- Communications table
CREATE TABLE communication (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    from_agent_id UUID REFERENCES agent(id),
    to_agent_id UUID REFERENCES agent(id),
    content JSONB NOT NULL,
    type VARCHAR(50) NOT NULL,
    communication_metadata JSONB,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Audit logs table
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_id UUID NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL,
    previous_state JSONB,
    new_state JSONB,
    actor_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Performance metrics table
CREATE TABLE performance_metric (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_id UUID NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DOUBLE PRECISION NOT NULL,
    context JSONB,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Model usage table
CREATE TABLE model_usage (
    id VARCHAR(100) PRIMARY KEY,
    model_id VARCHAR(100) NOT NULL,
    project_id UUID REFERENCES project(id),
    agent_id UUID REFERENCES agent(id),
    task_id UUID REFERENCES task(id),
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    cost DECIMAL(10, 6),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Optimization suggestions table
CREATE TABLE optimization_suggestion (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    evidence JSONB NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    impact_score DOUBLE PRECISION NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Human interactions table
CREATE TABLE human_interaction (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_id UUID NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    interaction_type VARCHAR(50) NOT NULL,
    type VARCHAR(50) NOT NULL,
    content JSONB NOT NULL,
    response JSONB,
    user_id UUID REFERENCES "user"(id),
    status VARCHAR(20) NOT NULL,
    priority INTEGER NOT NULL,
    response_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Models table
CREATE TYPE modelprovider AS ENUM ('OPENAI', 'ANTHROPIC', 'OLLAMA', 'CUSTOM');
CREATE TYPE modelstatus AS ENUM ('ACTIVE', 'INACTIVE', 'DEPRECATED');
CREATE TYPE requesttype AS ENUM ('CHAT', 'COMPLETION', 'EMBEDDING', 'IMAGE_GENERATION', 'AUDIO_TRANSCRIPTION', 'AUDIO_TRANSLATION');

CREATE TABLE models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id VARCHAR(100) UNIQUE NOT NULL,
    provider modelprovider NOT NULL,
    display_name VARCHAR(100),
    description TEXT,
    capabilities VARCHAR[] NOT NULL,
    status modelstatus NOT NULL,
    max_tokens INTEGER,
    token_limit INTEGER,
    cost_per_token DOUBLE PRECISION,
    configuration JSONB,
    model_metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Model performance metrics
CREATE TABLE model_performance_metric (
    id VARCHAR(100) PRIMARY KEY,
    model_id VARCHAR(100) NOT NULL,
    task_type VARCHAR(50) NOT NULL,
    success BOOLEAN NOT NULL,
    latency_ms INTEGER NOT NULL,
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Budget management
CREATE TABLE model_budget (
    id VARCHAR(100) PRIMARY KEY,
    project_id UUID REFERENCES project(id),
    monthly_limit DOUBLE PRECISION NOT NULL,
    current_usage DOUBLE PRECISION NOT NULL DEFAULT 0,
    last_reset TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    alert_percentage INTEGER NOT NULL DEFAULT 80,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- AI Models
CREATE TABLE ai_model (
    id VARCHAR(100) PRIMARY KEY,
    provider VARCHAR(50) NOT NULL,
    version VARCHAR(50) NOT NULL,
    capabilities JSONB NOT NULL,
    context_window INTEGER NOT NULL,
    cost_per_1k_input DOUBLE PRECISION,
    cost_per_1k_output DOUBLE PRECISION,
    is_local BOOLEAN NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Requests
CREATE TABLE requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    request_id VARCHAR(100) UNIQUE NOT NULL,
    request_type requesttype NOT NULL,
    model_id VARCHAR(100) NOT NULL,
    provider modelprovider NOT NULL,
    user_id VARCHAR(100),
    project_id VARCHAR(100),
    task_id VARCHAR(100),
    request_data JSONB NOT NULL,
    response_data JSONB,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    latency_ms DOUBLE PRECISION,
    cost DOUBLE PRECISION,
    success BOOLEAN NOT NULL,
    error_message VARCHAR,
    error_code VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Provider Quotas
CREATE TABLE provider_quotas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider modelprovider NOT NULL,
    daily_token_limit INTEGER,
    monthly_token_limit INTEGER,
    daily_cost_limit DOUBLE PRECISION,
    monthly_cost_limit DOUBLE PRECISION,
    daily_tokens_used INTEGER NOT NULL DEFAULT 0,
    monthly_tokens_used INTEGER NOT NULL DEFAULT 0,
    daily_cost_used DOUBLE PRECISION NOT NULL DEFAULT 0,
    monthly_cost_used DOUBLE PRECISION NOT NULL DEFAULT 0,
    daily_reset_at TIMESTAMP WITH TIME ZONE,
    monthly_reset_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Model Performance
CREATE TABLE model_performance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id VARCHAR(100) NOT NULL,
    task_type VARCHAR(50) NOT NULL,
    quality_score DOUBLE PRECISION NOT NULL,
    success_rate DOUBLE PRECISION NOT NULL,
    sample_count INTEGER NOT NULL,
    metrics JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(model_id, task_type)
);

-- Model Performance History
CREATE TABLE model_performance_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id VARCHAR(100) NOT NULL,
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    period_type VARCHAR(20) NOT NULL,
    task_type VARCHAR(50) NOT NULL,
    quality_score DOUBLE PRECISION NOT NULL,
    success_rate DOUBLE PRECISION NOT NULL,
    sample_count INTEGER NOT NULL,
    metrics JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(model_id, task_type, period_start, period_type)
);

-- Model Feedback
CREATE TABLE model_feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    request_id VARCHAR(100) NOT NULL,
    model_id VARCHAR(100) NOT NULL,
    task_type VARCHAR(50),
    quality_rating DOUBLE PRECISION,
    success BOOLEAN NOT NULL,
    feedback_text TEXT,
    has_corrections BOOLEAN NOT NULL,
    original_content TEXT,
    corrected_content TEXT,
    user_id VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Optimization Implementation
CREATE TABLE optimization_implementation (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    suggestion_id UUID NOT NULL REFERENCES optimization_suggestion(id) ON DELETE CASCADE,
    implementation_details JSONB NOT NULL,
    implemented_by UUID REFERENCES "user"(id) ON DELETE SET NULL,
    result_metrics JSONB,
    success BOOLEAN NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Human Interaction Types
CREATE TABLE approval_request (
    id UUID PRIMARY KEY,
    approved BOOLEAN,
    comment VARCHAR
);

CREATE TABLE clarification_request (
    id UUID PRIMARY KEY,
    answer VARCHAR
);

CREATE TABLE feedback_request (
    id UUID PRIMARY KEY,
    feedback JSONB
);

CREATE TABLE notification (
    id UUID PRIMARY KEY,
    level VARCHAR(20) NOT NULL,
    requires_acknowledgement BOOLEAN NOT NULL,
    acknowledged BOOLEAN NOT NULL
);

-- Create indexes
CREATE INDEX ix_model_feedback_model_id ON model_feedback USING btree (model_id);
CREATE INDEX ix_model_feedback_request_id ON model_feedback USING btree (request_id);
CREATE INDEX ix_model_feedback_task_type ON model_feedback USING btree (task_type);
CREATE INDEX ix_model_feedback_user_id ON model_feedback USING btree (user_id);
CREATE INDEX ix_model_performance_model_id ON model_performance USING btree (model_id);
CREATE INDEX ix_model_performance_task_type ON model_performance USING btree (task_type);
CREATE INDEX ix_model_performance_history_model_id ON model_performance_history USING btree (model_id);
CREATE INDEX ix_model_performance_history_period_start ON model_performance_history USING btree (period_start);
CREATE INDEX ix_model_performance_history_task_type ON model_performance_history USING btree (task_type);

-- Project state transitions table
CREATE TABLE project_state (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES project(id) ON DELETE CASCADE,
    state VARCHAR(20) NOT NULL,
    transitioned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    reason TEXT,
    transitioned_by UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create default admin user
INSERT INTO "user" (username, email, password_hash, is_active, is_admin, role, status)
VALUES ('admin', 'admin@example.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', TRUE, TRUE, 'ADMIN', 'ACTIVE');
