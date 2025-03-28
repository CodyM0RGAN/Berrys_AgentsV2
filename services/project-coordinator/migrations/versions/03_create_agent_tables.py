"""
Create agent-related tables for Berry and chat functionality.

This migration script creates the following tables:
- agent_instruction: Stores Berry's basic information, purpose, capabilities, tone guidelines, and knowledge domains
- agent_capability: Stores detailed information about Berry's capabilities
- agent_knowledge_domain: Stores detailed information about Berry's knowledge domains
- agent_prompt_template: Stores prompt templates for different conversation scenarios
- chat_session: Stores chat sessions
- chat_message: Stores chat messages

These tables are essential for the chat functionality and Berry's agent configuration.

Revision ID: 03_create_agent_tables
Revises: 02_standardize_table_names
Create Date: 2025-03-25 20:14:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid
from datetime import datetime

# revision identifiers, used by Alembic
revision = '03_create_agent_tables'
down_revision = '02_standardize_table_names'
branch_labels = None
depends_on = None


def upgrade():
    """Upgrade the database schema."""
    # Create agent_instruction table
    op.create_table(
        'agent_instruction',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('agent_name', sa.String(255), nullable=False, unique=True),
        sa.Column('purpose', sa.Text, nullable=False),
        sa.Column('capabilities', sa.JSON, nullable=False),
        sa.Column('tone_guidelines', sa.Text, nullable=False),
        sa.Column('knowledge_domains', sa.JSON, nullable=False),
        sa.Column('response_templates', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow),
        sa.Column('instruction_metadata', sa.JSON, nullable=True, default={}),
    )
    
    # Create agent_capability table
    op.create_table(
        'agent_capability',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('agent_instruction_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agent_instruction.id'), nullable=False),
        sa.Column('capability_name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('parameters', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow),
        sa.Column('capability_metadata', sa.JSON, nullable=True, default={}),
    )
    
    # Create agent_knowledge_domain table
    op.create_table(
        'agent_knowledge_domain',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('agent_instruction_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agent_instruction.id'), nullable=False),
        sa.Column('domain_name', sa.String(255), nullable=False),
        sa.Column('priority_level', sa.Integer, nullable=False, default=1),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow),
        sa.Column('domain_metadata', sa.JSON, nullable=True, default={}),
    )
    
    # Create chat_session table if it doesn't exist
    op.create_table(
        'chat_session',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('session_metadata', sa.JSON, nullable=True, default={}),
        sa.Column('created_at', sa.DateTime, nullable=False, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow),
    )
    
    # Create chat_message table if it doesn't exist
    op.create_table(
        'chat_message',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('session_id', sa.String(36), sa.ForeignKey('chat_session.id'), nullable=False),
        sa.Column('role', sa.String(10), nullable=False),  # 'user' or 'bot'
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('timestamp', sa.DateTime, nullable=False, default=datetime.utcnow),
        sa.Column('message_metadata', sa.JSON, nullable=True, default={}),
        sa.Column('created_at', sa.DateTime, nullable=False, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow),
    )


def downgrade():
    """Downgrade the database schema."""
    # Drop tables in reverse order
    op.drop_table('chat_message')
    op.drop_table('chat_session')
    op.drop_table('agent_knowledge_domain')
    op.drop_table('agent_capability')
    op.drop_table('agent_instruction')
