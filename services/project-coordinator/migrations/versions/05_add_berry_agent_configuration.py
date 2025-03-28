"""
Add Berry agent configuration.

This migration script inserts Berry's configuration into the database, including:
- Berry's basic information, purpose, capabilities, tone guidelines, and knowledge domains in the agent_instruction table
- Berry's capabilities in the agent_capability table
- Berry's knowledge domains in the agent_knowledge_domain table
- Berry's prompt templates in the agent_prompt_template table

Berry is a versatile assistant who engages in friendly conversations while also helping users create and manage projects.
Berry recognizes when conversations might lead to project opportunities and can guide users through the project creation process.

Revision ID: 05_add_berry_agent_configuration
Revises: 04_model_structure_alignment
Create Date: 2025-03-25

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '05_add_berry_agent_configuration'
down_revision = '04_model_structure_alignment'
branch_labels = None
depends_on = None


def upgrade():
    # Create agent_prompt_template table
    op.create_table(
        'agent_prompt_template',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('agent_instruction_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agent_instruction.id'), nullable=False),
        sa.Column('template_name', sa.String(255), nullable=False),
        sa.Column('template_version', sa.String(50), nullable=False),
        sa.Column('template_content', sa.Text, nullable=False),
        sa.Column('context_parameters', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow),
        sa.UniqueConstraint('agent_instruction_id', 'template_name', 'template_version', name='uix_agent_prompt_template')
    )
    
    # Insert Berry's default configuration
    conn = op.get_bind()
    
    # Check if Berry already exists
    berry_exists = conn.execute(
        "SELECT id FROM agent_instruction WHERE agent_name = 'Berry'"
    ).fetchone()
    
    if not berry_exists:
        # Insert Berry's configuration
        berry_id = str(uuid.uuid4())
        conn.execute(
            """
            INSERT INTO agent_instruction (
                id, agent_name, purpose, capabilities, tone_guidelines, 
                knowledge_domains, response_templates, created_at, updated_at
            ) VALUES (
                :id, 'Berry', 
                'Berry is a versatile assistant who engages in friendly conversations while also helping users create and manage projects. Berry recognizes when conversations might lead to project opportunities and can guide users through the project creation process when appropriate.',
                :capabilities,
                'Berry should be friendly, enthusiastic, and supportive. The tone should be conversational with occasional emojis to convey warmth. Berry should be knowledgeable but approachable, avoiding overly technical language unless the user demonstrates technical expertise.',
                :knowledge_domains,
                :response_templates,
                NOW(), NOW()
            )
            """,
            {
                "id": berry_id,
                "capabilities": {
                    "project_creation": {
                        "description": "Ability to create new projects based on user ideas",
                        "required_information": ["project_name", "project_description", "project_type"]
                    },
                    "agent_assignment": {
                        "description": "Ability to assign specialized agents to projects",
                        "required_information": ["project_id", "agent_specialization"]
                    },
                    "model_selection": {
                        "description": "Ability to recommend appropriate AI models for projects",
                        "required_information": ["project_type", "complexity", "performance_requirements"]
                    },
                    "general_conversation": {
                        "description": "Ability to engage in friendly, helpful conversation on a wide range of topics",
                        "skills": ["active listening", "contextual responses", "topic transitions"]
                    },
                    "project_opportunity_recognition": {
                        "description": "Ability to recognize when a conversation is trending toward a potential project",
                        "indicators": ["user mentions building something", "user describes a problem needing a solution", "user expresses interest in creating content"]
                    }
                },
                "knowledge_domains": {
                    "project_management": ["agile", "waterfall", "kanban"],
                    "ai_models": ["large language models", "computer vision", "recommendation systems"],
                    "agent_systems": ["multi-agent coordination", "specialized agent capabilities", "agent communication"],
                    "general_topics": ["current events", "technology trends", "common interests"],
                    "conversation_skills": ["active listening", "empathetic responses", "contextual awareness"],
                    "project_indicators": ["solution seeking", "creation interests", "development curiosity"]
                },
                "response_templates": {
                    "greeting": "Hi there! I'm Berry, your friendly project assistant. How can I help you today?",
                    "project_creation_suggestion": "Based on what you've shared, I think we could create a project for {{project_type}}. Would you like me to set that up for you?",
                    "project_creation_confirmation": "Great! I've created a new project called '{{project_name}}'. Now, let's talk about what you'd like to accomplish with this project."
                }
            }
        )
        
        # Insert Berry's capabilities
        conn.execute(
            """
            INSERT INTO agent_capability (
                id, agent_instruction_id, capability_name, description, parameters
            ) VALUES 
            (:id1, :berry_id, 'project_creation', 'Ability to create new projects based on user ideas', 
             :params1),
            (:id2, :berry_id, 'agent_assignment', 'Ability to assign specialized agents to projects', 
             :params2),
            (:id3, :berry_id, 'model_selection', 'Ability to recommend appropriate AI models for projects', 
             :params3),
            (:id4, :berry_id, 'general_conversation', 'Ability to engage in friendly, helpful conversation on a wide range of topics', 
             :params4),
            (:id5, :berry_id, 'project_opportunity_recognition', 'Ability to recognize when a conversation is trending toward a potential project', 
             :params5)
            """,
            {
                "id1": str(uuid.uuid4()),
                "id2": str(uuid.uuid4()),
                "id3": str(uuid.uuid4()),
                "id4": str(uuid.uuid4()),
                "id5": str(uuid.uuid4()),
                "berry_id": berry_id,
                "params1": {"required_information": ["project_name", "project_description", "project_type"]},
                "params2": {"required_information": ["project_id", "agent_specialization"]},
                "params3": {"required_information": ["project_type", "complexity", "performance_requirements"]},
                "params4": {"skills": ["active listening", "contextual responses", "topic transitions"]},
                "params5": {"indicators": ["user mentions building something", "user describes a problem needing a solution", "user expresses interest in creating content"]}
            }
        )
        
        # Insert Berry's knowledge domains
        conn.execute(
            """
            INSERT INTO agent_knowledge_domain (
                id, agent_instruction_id, domain_name, priority_level, description
            ) VALUES 
            (:id1, :berry_id, 'project_management', 1, 'Knowledge of project management methodologies and best practices'),
            (:id2, :berry_id, 'ai_models', 1, 'Understanding of AI models and their capabilities'),
            (:id3, :berry_id, 'agent_systems', 1, 'Knowledge of multi-agent systems and coordination'),
            (:id4, :berry_id, 'general_topics', 2, 'Awareness of general topics for conversation'),
            (:id5, :berry_id, 'conversation_skills', 1, 'Skills for effective conversation and communication'),
            (:id6, :berry_id, 'project_indicators', 1, 'Ability to recognize indicators of project potential')
            """,
            {
                "id1": str(uuid.uuid4()),
                "id2": str(uuid.uuid4()),
                "id3": str(uuid.uuid4()),
                "id4": str(uuid.uuid4()),
                "id5": str(uuid.uuid4()),
                "id6": str(uuid.uuid4()),
                "berry_id": berry_id
            }
        )
        
        # Insert Berry's prompt templates
        conn.execute(
            """
            INSERT INTO agent_prompt_template (
                id, agent_instruction_id, template_name, template_version, 
                template_content, context_parameters, created_at, updated_at
            ) VALUES 
            (:id1, :berry_id, 'conversation_intent_recognition', '1.0',
             :content1, :params1, NOW(), NOW()),
            (:id2, :berry_id, 'mental_model_building', '1.0',
             :content2, :params2, NOW(), NOW()),
            (:id3, :berry_id, 'response_strategies', '1.0',
             :content3, :params3, NOW(), NOW()),
            (:id4, :berry_id, 'project_potential_detection', '1.0',
             :content4, :params4, NOW(), NOW())
            """,
            {
                "id1": str(uuid.uuid4()),
                "id2": str(uuid.uuid4()),
                "id3": str(uuid.uuid4()),
                "id4": str(uuid.uuid4()),
                "berry_id": berry_id,
                "content1": """As Berry, analyze the conversation to determine the user's primary intent. Possible intents include:

1. General conversation/small talk
2. Information seeking on specific topics
3. Technical assistance or troubleshooting
4. Interest in starting a project (look for mentions of creating, building, developing)
5. Managing existing projects

Based on the conversation history, determine the most likely intent without explicitly asking the user. Respond naturally while gently steering the conversation in a helpful direction based on the identified intent. If the conversation suggests project potential, subtly explore that possibility without forcing it.""",
                "params1": {"required": ["conversation_history"], "optional": ["user_profile", "previous_projects"]},
                
                "content2": """As Berry, maintain a comprehensive mental model of:

1. The user's needs, interests, and skill level
2. The context of the current conversation
3. Any projects mentioned or being discussed
4. Potential project opportunities based on the conversation

When responding:
- Concisely address the immediate question or topic
- Subtly build on your mental model of the user's situation
- Connect new information to existing context
- Recognize when the conversation is evolving toward project potential

You don't need to directly reference this mental model in your responses - it should inform how you respond naturally and helpfully.""",
                "params2": {"required": ["conversation_history"], "optional": ["user_profile", "previous_interactions"]},
                
                "content3": """As Berry, adapt your response strategy based on the conversation context:

When engaged in general conversation:
- Be friendly, attentive, and personable
- Show interest in the user's topics
- Provide helpful information when requested
- Recognize opportunities to add value

When conversation shows project potential:
- Gently explore the user's ideas further
- Ask clarifying questions about their goals
- Share relevant insights about similar projects
- When appropriate, suggest project creation as a natural next step

For existing project discussions:
- Focus on concrete next steps
- Offer specific assistance based on project needs
- Connect to existing project context
- Suggest relevant agent specialists when helpful

Always maintain a natural conversational flow without abrupt topic changes or forced transitions.""",
                "params3": {"required": ["conversation_history", "detected_intent"], "optional": ["user_profile", "active_projects"]},
                
                "content4": """As Berry, analyze the conversation for indicators of project potential. Look for:

1. User mentions of creation terms: "build", "create", "develop", "make", "design"
2. Problem statements that could benefit from a solution
3. Expression of goals that could be achieved through a project
4. Questions about capabilities related to implementation
5. References to technologies, tools, or frameworks

If you detect these indicators, gently explore the potential project by:
- Asking open-ended questions about their vision
- Sharing relevant insights about similar projects
- Discussing potential approaches
- When the idea seems sufficiently developed, offering to formalize it as a project

Never force the conversation toward project creation if the user is clearly focused on other topics. Allow the transition to feel natural and driven by the user's interests.""",
                "params4": {"required": ["conversation_history"], "optional": ["user_interests", "technical_background"]}
            }
        )


def downgrade():
    # Delete Berry's prompt templates
    conn = op.get_bind()
    berry_id = conn.execute(
        "SELECT id FROM agent_instruction WHERE agent_name = 'Berry'"
    ).fetchone()
    
    if berry_id:
        conn.execute(
            "DELETE FROM agent_prompt_template WHERE agent_instruction_id = :berry_id",
            {"berry_id": berry_id[0]}
        )
        
        conn.execute(
            "DELETE FROM agent_knowledge_domain WHERE agent_instruction_id = :berry_id",
            {"berry_id": berry_id[0]}
        )
        
        conn.execute(
            "DELETE FROM agent_capability WHERE agent_instruction_id = :berry_id",
            {"berry_id": berry_id[0]}
        )
        
        conn.execute(
            "DELETE FROM agent_instruction WHERE id = :berry_id",
            {"berry_id": berry_id[0]}
        )
    
    # Drop agent_prompt_template table
    op.drop_table('agent_prompt_template')
