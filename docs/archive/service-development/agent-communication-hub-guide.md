# Agent Communication Hub Guide

> **Draft-of-Thought Documentation**: This comprehensive guide consolidates information about the Agent Communication Hub in the Berrys_AgentsV2 system, including its enhancement, monitoring, analytics, alerting, and visualization capabilities.

## Overview

The Agent Communication Hub is a critical component of the Berrys_AgentsV2 system that facilitates communication between agents. It has been enhanced with the following capabilities:

1. **Enhanced Routing**
   - Topic-based routing with wildcard support
   - Content-based routing
   - Rule-based routing with conditions and actions

2. **Priority Queue System**
   - Message prioritization based on message attributes
   - Priority inheritance for related messages
   - Fairness mechanisms to prevent starvation

3. **Advanced Communication Patterns**
   - Publish-subscribe messaging
   - Request-reply pattern with timeouts
   - Broadcast messaging
   - Agent groups and team communication

4. **Monitoring and Analytics**
   - Message flow tracking
   - Performance metrics collection
   - Analytics engine for pattern analysis
   - API endpoints for retrieving metrics

5. **Alerting System**
   - Alert configuration for metric thresholds
   - Alert history tracking
   - Notification channels (email, dashboard)
   - Alert acknowledgment

6. **Visualization Dashboard**
   - Message flow visualization (Sankey diagram)
   - Message status distribution
   - Top topics analysis
   - Agent activity monitoring
   - Topic activity over time

## Architecture

The Agent Communication Hub is built on a modular architecture with the following components:

### Core Components

1. **CommunicationHub**: The central component that ties together the routing and priority components.
2. **Routing Components**:
   - **TopicRouter**: Implements topic-based routing with wildcard support.
   - **ContentRouter**: Implements content-based routing.
   - **RuleBasedRouter**: Implements rule-based routing with conditions and actions.
3. **Priority Components**:
   - **PriorityQueue**: Implements a priority queue using Redis Sorted Sets.
   - **PriorityDeterminer**: Determines message priorities based on message attributes.
   - **PriorityDispatcher**: Dispatches messages to appropriate queues based on priority.
   - **FairnessManager**: Ensures fairness in message processing.
   - **PriorityInheritanceManager**: Implements priority inheritance for related messages.
4. **Monitoring Components**:
   - **MetricsCollector**: Collects metrics from the CommunicationHub and stores them in the database.
   - **AnalyticsEngine**: Analyzes message patterns and calculates metrics.
5. **Alerting Components**:
   - **AlertingService**: Monitors metrics and triggers alerts when thresholds are exceeded.
   - **NotificationManager**: Sends notifications to configured channels.
6. **Visualization Components**:
   - **MetricsDashboard**: Web interface for visualizing metrics.
   - **ChartRenderers**: Components for rendering different types of charts.

### Integration Components

1. **EnhancedCommunicationService**: Extends the basic CommunicationService with advanced routing, prioritization, monitoring, and alerting capabilities.
2. **Redis Integration**: Uses Redis for distributed priority queues and pub/sub messaging.
3. **Database Integration**: Uses PostgreSQL for storing metrics, alert configurations, and alert history.

## Core Components

### Enhanced Routing

The enhanced routing system provides three types of routing:

#### Topic-Based Routing

Topic-based routing allows agents to subscribe to topics and receive messages published to those topics. The implementation supports wildcards in topic patterns:

- `*`: Matches a single segment in a topic (e.g., `project.*.updates` matches `project.alpha.updates`).
- `#`: Matches multiple segments in a topic (e.g., `project.#` matches `project.alpha.updates.critical`).

```python
# Example topic subscription
await communication_hub.subscribe("agent_123", "project.alpha.updates")

# Example topic publishing
await communication_hub.publish_to_topic("project.alpha.updates", message)
```

#### Content-Based Routing

Content-based routing routes messages based on their content. Rules can be defined to match specific message attributes:

```python
# Example content-based routing rule
await communication_hub.add_content_rule(
    lambda message: message.get("payload", {}).get("task_type") == "research",
    "research_agent_id"
)
```

#### Rule-Based Routing

Rule-based routing provides a flexible way to define routing rules with conditions and actions:

```python
# Example rule-based routing rule
await communication_hub.add_rule({
    "name": "task_assignment_rule",
    "conditions": [
        {
            "type": "field",
            "field": "task_type",
            "operator": "eq",
            "value": "research"
        }
    ],
    "actions": [
        {
            "type": "route",
            "destination": "research_agent_id"
        }
    ],
    "is_terminal": True
})
```

### Priority Queue System

The priority queue system uses Redis Sorted Sets to implement priority queues. Messages are prioritized based on their attributes, and the system ensures fairness in message processing.

#### Priority Determination

Message priorities are determined based on the following factors:

1. Explicit priority in the message
2. Priority in message headers
3. Urgency flag in message headers
4. Priority inheritance from related messages

#### Fairness Mechanisms

The fairness manager ensures that lower-priority messages are not starved by higher-priority messages. It tracks the last processed time for each priority level and occasionally processes lower-priority messages to prevent starvation.

#### Priority Inheritance

The priority inheritance manager implements priority inheritance for related messages. Messages that are part of the same conversation or are replies to high-priority messages inherit the priority of the original message.

### Advanced Communication Patterns

#### Publish-Subscribe Messaging

The publish-subscribe pattern allows agents to publish messages to topics and subscribe to topics to receive messages:

```python
# Example topic subscription
await communication_service.subscribe(agent_id, "project.updates")

# Example topic publishing
await communication_service.publish_to_topic(agent_id, "project.updates", content)
```

#### Request-Reply Pattern

The request-reply pattern allows agents to send requests to other agents and wait for replies:

```python
# Example request-reply
reply = await communication_service.send_request(from_agent_id, to_agent_id, content, timeout=30.0)
```

#### Broadcast Messaging

The broadcast pattern allows agents to send messages to multiple agents at once:

```python
# Example broadcast
message_ids = await communication_service.broadcast(from_agent_id, to_agent_ids, content)
```

### Monitoring and Analytics

The monitoring and analytics system tracks message flow, collects performance metrics, and provides analytics capabilities.

#### Message Flow Tracking

The system tracks the following message lifecycle events:

1. **Message Creation**: When a message is created
2. **Message Routing**: When a message is routed
3. **Message Delivery**: When a message is delivered to the destination agent
4. **Message Processing**: When a message is processed by the destination agent
5. **Message Failure**: When a message fails to be processed

#### Performance Metrics Collection

The system collects the following performance metrics:

1. **Processing Time**: Time taken to process messages
2. **Queue Time**: Time messages spend in the queue
3. **Total Time**: Total time from creation to processing
4. **Message Count**: Number of messages by agent, topic, and status
5. **Error Rate**: Percentage of failed messages

#### Analytics Engine

The analytics engine analyzes message patterns and calculates metrics such as:

1. **Throughput**: Messages processed per second
2. **Latency**: Average processing time
3. **Queue Depth**: Number of messages in the queue
4. **Error Rate**: Percentage of failed messages
5. **Agent Activity**: Messages sent and received by each agent
6. **Topic Activity**: Messages published to each topic

### Alerting System

The alerting system monitors metrics and triggers alerts when thresholds are exceeded.

#### Alert Configuration

Alert configurations define the conditions under which alerts are triggered:

1. **Metric Type**: The type of metric to monitor (e.g., QUEUE_LENGTH, PROCESSING_TIME)
2. **Threshold**: The threshold value
3. **Comparison Operator**: The comparison operator (e.g., GT, LT, EQ)
4. **Severity**: The severity level (e.g., INFO, WARNING, ERROR, CRITICAL)
5. **Notification Channels**: The channels to send notifications to (e.g., email, dashboard)

#### Alert History

Alert history records triggered alerts:

1. **Alert Configuration**: Reference to the alert configuration
2. **Timestamp**: When the alert was triggered
3. **Value**: The value that triggered the alert
4. **Message**: The alert message
5. **Acknowledgment**: Whether the alert has been acknowledged

#### Notification Channels

The alerting system supports the following notification channels:

1. **Email**: Sends email notifications to configured recipients
2. **Dashboard**: Displays notifications in the web dashboard

### Visualization Dashboard

The visualization dashboard provides a visual interface for exploring and analyzing the collected metrics.

#### Message Flow Visualization

The message flow visualization provides a Sankey diagram showing the flow of messages between agents:

1. Node labels for agent names
2. Link thickness representing message volume
3. Tooltips showing message counts

#### Message Status Distribution

The message status distribution chart provides a pie chart showing the distribution of message statuses:

1. Color-coded segments for each status
2. Tooltips showing counts and percentages

#### Top Topics Analysis

The top topics chart provides a bar chart showing the most active topics:

1. Bars representing message count per topic
2. Sorted by message count

#### Agent Activity Monitoring

The agent activity chart provides a bar chart showing messages sent and received by each agent:

1. Grouped bars for sent and received messages
2. Color-coded by message direction

#### Topic Activity Over Time

The topic activity chart provides a line chart showing topic activity over time:

1. Multiple lines for different topics
2. Color-coded by topic

## Implementation Details

### Message Structure

Messages in the enhanced Agent Communication Hub have the following structure:

```json
{
  "message_id": "550e8400-e29b-41d4-a716-446655440000",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440001",
  "source_agent_id": "agent-123",
  "destination": {
    "type": "agent",  // "agent", "topic", "group"
    "id": "agent-456"
  },
  "reply_to": "agent-123",
  "priority": 2,  // 0-5, with 5 being highest
  "timestamp": "2025-03-26T19:45:00Z",
  "expiration": "2025-03-26T19:50:00Z",
  "headers": {
    "content_type": "application/json",
    "conversation_id": "conv-789",
    "custom_header": "value"
  },
  "payload": {
    // Message-specific content
  }
}
```

### Routing Configuration

Routing rules are defined using a declarative configuration format:

```json
{
  "rules": [
    {
      "name": "research-to-developer",
      "source": {
        "type": "agent_type",
        "value": "RESEARCHER"
      },
      "destination": {
        "type": "agent_type",
        "value": "DEVELOPER"
      },
      "condition": "payload.type == 'research_finding'",
      "action": {
        "route_to": "topic:research_findings",
        "transform": "transform_research_to_dev",
        "priority": 3
      }
    },
    {
      "name": "urgent-messages",
      "condition": "headers.urgent == true",
      "action": {
        "priority": 5,
        "route_to": "{{destination.id}}",
        "add_headers": {
          "processed_as": "urgent"
        }
      }
    }
  ],
  "transformations": {
    "transform_research_to_dev": {
      "script": "payload.details = summarize(payload.content); return payload;"
    }
  }
}
```

### Database Schema

The following tables were added to the database:

1. **message_metrics**
   - `id`: UUID primary key
   - `message_id`: UUID (reference to the original message)
   - `correlation_id`: UUID (for tracking related messages)
   - `source_agent_id`: UUID (reference to the source agent)
   - `destination_agent_id`: UUID (reference to the destination agent)
   - `topic`: String (for topic-based messages)
   - `priority`: Integer
   - `created_at`: Timestamp
   - `routed_at`: Timestamp
   - `delivered_at`: Timestamp
   - `processed_at`: Timestamp
   - `processing_time_ms`: Integer
   - `queue_time_ms`: Integer
   - `total_time_ms`: Integer
   - `status`: Enum (CREATED, ROUTED, DELIVERED, PROCESSED, FAILED)
   - `routing_path`: JSON (stores the routing decisions)
   - `metadata`: JSON (additional metadata)

2. **agent_metrics**
   - `id`: UUID primary key
   - `agent_id`: UUID (reference to the agent)
   - `timestamp`: Timestamp
   - `messages_sent`: Integer
   - `messages_received`: Integer
   - `average_processing_time_ms`: Float
   - `metadata`: JSON (additional metadata)

3. **topic_metrics**
   - `id`: UUID primary key
   - `topic`: String
   - `timestamp`: Timestamp
   - `message_count`: Integer
   - `subscriber_count`: Integer
   - `metadata`: JSON (additional metadata)

4. **alert_configurations**
   - `id`: UUID primary key
   - `name`: String
   - `description`: String
   - `metric_type`: Enum (QUEUE_LENGTH, PROCESSING_TIME, etc.)
   - `threshold`: Float
   - `comparison`: Enum (GT, LT, EQ, etc.)
   - `severity`: Enum (INFO, WARNING, ERROR, CRITICAL)
   - `enabled`: Boolean
   - `notification_channels`: JSON (email, dashboard, etc.)
   - `metadata`: JSON (additional metadata)

5. **alert_history**
   - `id`: UUID primary key
   - `alert_configuration_id`: UUID (reference to alert_configuration)
   - `timestamp`: Timestamp
   - `value`: Float (the value that triggered the alert)
   - `message`: String
   - `acknowledged`: Boolean
   - `acknowledged_by`: UUID (reference to user)
   - `acknowledged_at`: Timestamp
   - `metadata`: JSON (additional metadata)

## API Endpoints

The enhanced communication system exposes the following API endpoints:

### Communication Endpoints

- `POST /api/enhanced-communication/send`: Send a communication from one agent to another.
- `GET /api/enhanced-communication/receive/{agent_id}`: Receive a message for an agent.
- `POST /api/enhanced-communication/subscribe`: Subscribe an agent to a topic.
- `POST /api/enhanced-communication/unsubscribe`: Unsubscribe an agent from a topic.
- `GET /api/enhanced-communication/subscriptions/{agent_id}`: Get an agent's subscriptions.
- `POST /api/enhanced-communication/publish`: Publish a message to a topic.
- `POST /api/enhanced-communication/broadcast`: Broadcast a message to multiple agents.
- `POST /api/enhanced-communication/request`: Send a request and wait for a reply.
- `POST /api/enhanced-communication/rules`: Add a routing rule.

### Metrics Endpoints

- `GET /api/metrics/messages`: Get message metrics with filtering options.
- `GET /api/metrics/agents`: Get agent metrics with filtering options.
- `GET /api/metrics/topics`: Get topic metrics with filtering options.
- `GET /api/metrics/performance`: Get performance metrics.

### Alert Endpoints

- `GET /api/alerts/configurations`: List alert configurations.
- `POST /api/alerts/configurations`: Create a new alert configuration.
- `GET /api/alerts/configurations/{id}`: Get an alert configuration.
- `PUT /api/alerts/configurations/{id}`: Update an alert configuration.
- `DELETE /api/alerts/configurations/{id}`: Delete an alert configuration.
- `GET /api/alerts/history`: List alert history.
- `GET /api/alerts/active`: List active (unacknowledged) alerts.
- `POST /api/alerts/acknowledge/{id}`: Acknowledge an alert.

## Usage Examples

### Basic Communication

```python
# Send a communication
response = await communication_service.send_communication(from_agent_id, communication_request)

# Receive a message
message = await communication_service.receive_message(agent_id)
```

### Topic-Based Messaging

```python
# Subscribe to a topic
await communication_service.subscribe(agent_id, "project.updates")

# Publish to a topic
message_id = await communication_service.publish_to_topic(agent_id, "project.updates", content)

# Get subscriptions
subscriptions = await communication_service.get_subscriptions(agent_id)

# Unsubscribe from a topic
await communication_service.unsubscribe(agent_id, "project.updates")
```

### Request-Reply Messaging

```python
# Send a request and wait for a reply
reply = await communication_service.send_request(from_agent_id, to_agent_id, content, timeout=30.0)
```

### Broadcast Messaging

```python
# Broadcast a message to multiple agents
message_ids = await communication_service.broadcast(from_agent_id, to_agent_ids, content)
```

### Rule-Based Routing

```python
# Add a routing rule
await communication_service.add_rule({
    "name": "task_assignment_rule",
    "conditions": [
        {
            "type": "field",
            "field": "task_type",
            "operator": "eq",
            "value": "research"
        }
    ],
    "actions": [
        {
            "type": "route",
            "destination": "research_agent_id"
        }
    ],
    "is_terminal": True
})
```

### Retrieving Metrics

```python
# Get message metrics
message_metrics = await metrics_collector.get_message_metrics(
    source_agent_id="agent-123",
    start_time=datetime(2025, 3, 26),
    end_time=datetime(2025, 3, 27)
)

# Get agent metrics
agent_metrics = await metrics_collector.get_agent_metrics(
    agent_id="agent-123",
    start_time=datetime(2025, 3, 26),
    end_time=datetime(2025, 3, 27)
)

# Get topic metrics
topic_metrics = await metrics_collector.get_topic_metrics(
    topic="project.updates",
    start_time=datetime(2025, 3, 26),
    end_time=datetime(2025, 3, 27)
)

# Get performance metrics
performance_metrics = await metrics_collector.get_performance_metrics(
    start_time=datetime(2025, 3, 26),
    end_time=datetime(2025, 3, 27)
)
```

### Managing Alerts

```python
# Create an alert configuration
alert_config = {
    "name": "High Queue Length Alert",
    "description": "Alert when queue length exceeds threshold",
    "metric_type": "QUEUE_LENGTH",
    "threshold": 100,
    "comparison": "GT",
    "severity": "WARNING",
    "enabled": True,
    "notification_channels": {
        "email": ["admin@example.com"],
        "dashboard": True
    }
}
alert_id = await alerting_service.create_alert_configuration(alert_config)

# Get active alerts
active_alerts = await alerting_service.get_active_alerts()

# Acknowledge an alert
await alerting_service.acknowledge_alert(alert_id, user_id)
```

### Using the Visualization Dashboard

The visualization dashboard provides a visual interface for exploring and analyzing the collected metrics:

1. **Viewing Message Flow**
   - Select a time range (e.g., Last 24 Hours)
   - Optionally filter by agent or topic
   - Click "Apply Filters"
   - The Sankey diagram will show the flow of messages between agents

2. **Analyzing Message Status Distribution**
   - Select a time range (e.g., Last 24 Hours)
   - Optionally filter by agent or topic
   - Click "Apply Filters"
   - The pie chart will show the distribution of message statuses

3. **Monitoring Agent Activity**
   - Select a time range (e.g., Last 24 Hours)
   - Optionally filter by agent or topic
   - Click "Apply Filters"
   - The bar chart will show the number of messages sent and received by each agent

4. **Tracking Topic Activity Over Time**
   - Select a time range (e.g., Last 24 Hours)
   - Optionally filter by agent or topic
   - Click "Apply Filters"
   - The line chart will show the activity of each topic over time

## Future Enhancements

The following enhancements are planned for future iterations:

1. **Message Transformation**: Add support for message transformation during routing.
2. **Message Filtering**: Add support for message filtering during routing.
3. **Message Aggregation**: Add support for message aggregation from multiple sources.
4. **Message Correlation**: Enhance message correlation for complex workflows.
5. **Message Persistence**: Add support for message persistence for reliable messaging.
6. **Message Replay**: Add support for message replay for error recovery.
7. **Message Security**: Enhance message security with encryption and authentication.
8. **Message Versioning**: Add support for message versioning for backward compatibility.
9. **Message Schema Validation**: Add support for message schema validation.
10. **Real-time Updates**: Implement WebSocket connection for real-time updates.
11. **Advanced Filtering**: Add filtering by message status, priority, and correlation ID.
12. **Message Detail View**: Add ability to view details of individual messages.
13. **Export Functionality**: Add ability to export metrics data as CSV and charts as images.

## Related Documentation

- [Agent Orchestrator Standardization Implementation](agent-orchestrator-standardization-implementation.md)
- [Cross-Service Communication Improvements](cross-service-communication-improvements.md)
- [Error Handling Best Practices](error-handling-best-practices.md)
- [Service Integration Workflow Guide](service-integration-workflow-guide.md)
