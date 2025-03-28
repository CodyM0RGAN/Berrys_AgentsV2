"""
Routing module for agent communication hub.

This module implements various routing algorithms for agent communication:
- Topic-based routing: Routes messages based on topics with wildcard support
- Content-based routing: Routes messages based on message content
- Rule-based routing: Routes messages based on configurable rules
"""

import logging
import re
from typing import List, Dict, Any, Callable, Optional, Set, Tuple
from uuid import UUID

logger = logging.getLogger(__name__)


class TopicRouter:
    """Router for topic-based message routing."""
    
    def __init__(self):
        """Initialize the topic router."""
        self.subscriptions = {}  # topic -> set of subscriber_ids
    
    def subscribe(self, topic: str, subscriber_id: str) -> None:
        """
        Subscribe to a topic.
        
        Args:
            topic: Topic to subscribe to
            subscriber_id: ID of the subscriber
        """
        if topic not in self.subscriptions:
            self.subscriptions[topic] = set()
        self.subscriptions[topic].add(subscriber_id)
        logger.debug(f"Subscriber {subscriber_id} subscribed to topic {topic}")
    
    def unsubscribe(self, topic: str, subscriber_id: str) -> None:
        """
        Unsubscribe from a topic.
        
        Args:
            topic: Topic to unsubscribe from
            subscriber_id: ID of the subscriber
        """
        if topic in self.subscriptions:
            self.subscriptions[topic].discard(subscriber_id)
            if not self.subscriptions[topic]:
                del self.subscriptions[topic]
            logger.debug(f"Subscriber {subscriber_id} unsubscribed from topic {topic}")
    
    def get_subscribers(self, topic: str) -> List[str]:
        """
        Get subscribers for a topic.
        
        Args:
            topic: Topic to get subscribers for
            
        Returns:
            List of subscriber IDs
        """
        subscribers = set()
        
        # Exact match
        if topic in self.subscriptions:
            subscribers.update(self.subscriptions[topic])
        
        # Wildcard matches
        for subscription_topic, subscription_subscribers in self.subscriptions.items():
            if self._topic_matches(subscription_topic, topic):
                subscribers.update(subscription_subscribers)
        
        return list(subscribers)
    
    def _topic_matches(self, pattern: str, topic: str) -> bool:
        """
        Check if a topic matches a pattern.
        
        Args:
            pattern: Pattern to match against
            topic: Topic to check
            
        Returns:
            True if the topic matches the pattern, False otherwise
        """
        # Split the pattern and topic into segments
        pattern_segments = pattern.split('.')
        topic_segments = topic.split('.')
        
        # If the pattern has more segments than the topic, it can't match
        if len(pattern_segments) > len(topic_segments):
            return False
        
        # Check each segment
        for i, pattern_segment in enumerate(pattern_segments):
            # If this is the last segment and it's a wildcard, it matches the rest of the topic
            if i == len(pattern_segments) - 1 and pattern_segment == '*':
                return True
            
            # If this segment is a wildcard, it matches any single segment
            if pattern_segment == '*':
                continue
            
            # If this segment is a multi-level wildcard, it matches the rest of the topic
            if pattern_segment == '#':
                return True
            
            # If this segment doesn't match the corresponding topic segment, the pattern doesn't match
            if pattern_segment != topic_segments[i]:
                return False
        
        # If we've checked all pattern segments and they all match, the pattern matches
        return len(pattern_segments) == len(topic_segments)


class ContentRouter:
    """Router for content-based message routing."""
    
    def __init__(self):
        """Initialize the content router."""
        self.rules = []  # list of (condition, destination) tuples
    
    def add_rule(self, condition: Callable[[Dict[str, Any]], bool], destination: str) -> None:
        """
        Add a routing rule.
        
        Args:
            condition: Function that takes a message and returns True if the rule applies
            destination: Destination for messages that match the condition
        """
        self.rules.append((condition, destination))
        logger.debug(f"Added content-based routing rule to destination {destination}")
    
    def get_destinations(self, message: Dict[str, Any]) -> List[str]:
        """
        Get destinations for a message.
        
        Args:
            message: Message to route
            
        Returns:
            List of destination IDs
        """
        destinations = []
        
        for condition, destination in self.rules:
            if condition(message):
                destinations.append(destination)
                logger.debug(f"Message matched content-based rule for destination {destination}")
        
        return destinations


class Condition:
    """Condition for rule-based routing."""
    
    def __init__(self, condition_type: str, field: str, operator: str, value: Any):
        """
        Initialize the condition.
        
        Args:
            condition_type: Type of condition (field, header, source, destination)
            field: Field to check
            operator: Operator to use
            value: Value to compare against
        """
        self.condition_type = condition_type
        self.field = field
        self.operator = operator
        self.value = value
    
    @classmethod
    def from_dict(cls, condition_dict: Dict[str, Any]) -> 'Condition':
        """
        Create a condition from a dictionary.
        
        Args:
            condition_dict: Condition definition
            
        Returns:
            Condition object
        """
        return cls(
            condition_type=condition_dict.get('type'),
            field=condition_dict.get('field'),
            operator=condition_dict.get('operator'),
            value=condition_dict.get('value'),
        )
    
    def matches(self, message: Dict[str, Any]) -> bool:
        """
        Check if the condition matches a message.
        
        Args:
            message: Message to check
            
        Returns:
            True if the condition matches, False otherwise
        """
        if self.condition_type == 'field':
            return self._evaluate_field_condition(message)
        elif self.condition_type == 'header':
            return self._evaluate_header_condition(message)
        elif self.condition_type == 'source':
            return self._evaluate_source_condition(message)
        elif self.condition_type == 'destination':
            return self._evaluate_destination_condition(message)
        
        return False
    
    def _evaluate_field_condition(self, message: Dict[str, Any]) -> bool:
        """
        Evaluate a field condition.
        
        Args:
            message: Message to evaluate
            
        Returns:
            True if the condition is met, False otherwise
        """
        # Get the field value from the message
        field_value = message.get('payload', {}).get(self.field)
        
        # Evaluate the condition
        return self._evaluate_condition(field_value, self.operator, self.value)
    
    def _evaluate_header_condition(self, message: Dict[str, Any]) -> bool:
        """
        Evaluate a header condition.
        
        Args:
            message: Message to evaluate
            
        Returns:
            True if the condition is met, False otherwise
        """
        # Get the header value from the message
        header_value = message.get('headers', {}).get(self.field)
        
        # Evaluate the condition
        return self._evaluate_condition(header_value, self.operator, self.value)
    
    def _evaluate_source_condition(self, message: Dict[str, Any]) -> bool:
        """
        Evaluate a source condition.
        
        Args:
            message: Message to evaluate
            
        Returns:
            True if the condition is met, False otherwise
        """
        # Get the source agent ID from the message
        source_agent_id = message.get('source_agent_id')
        
        # Evaluate the condition
        return self._evaluate_condition(source_agent_id, self.operator, self.value)
    
    def _evaluate_destination_condition(self, message: Dict[str, Any]) -> bool:
        """
        Evaluate a destination condition.
        
        Args:
            message: Message to evaluate
            
        Returns:
            True if the condition is met, False otherwise
        """
        # Get the destination agent ID from the message
        destination = message.get('destination', {})
        destination_id = destination.get('id') if destination.get('type') == 'agent' else None
        
        # Evaluate the condition
        return self._evaluate_condition(destination_id, self.operator, self.value)
    
    def _evaluate_condition(self, value: Any, operator: str, target_value: Any) -> bool:
        """
        Evaluate a condition.
        
        Args:
            value: Value to evaluate
            operator: Operator to use
            target_value: Value to compare against
            
        Returns:
            True if the condition is met, False otherwise
        """
        if value is None:
            return False
        
        if operator == 'eq':
            return value == target_value
        elif operator == 'neq':
            return value != target_value
        elif operator == 'gt':
            return value > target_value
        elif operator == 'lt':
            return value < target_value
        elif operator == 'gte':
            return value >= target_value
        elif operator == 'lte':
            return value <= target_value
        elif operator == 'in':
            return value in target_value
        elif operator == 'contains':
            return target_value in value
        elif operator == 'matches':
            return bool(re.match(target_value, value))
        
        return False


class Action:
    """Action for rule-based routing."""
    
    def __init__(self, action_type: str, **kwargs):
        """
        Initialize the action.
        
        Args:
            action_type: Type of action (route, transform, log, drop)
            **kwargs: Additional action parameters
        """
        self.action_type = action_type
        self.params = kwargs
    
    @classmethod
    def from_dict(cls, action_dict: Dict[str, Any]) -> 'Action':
        """
        Create an action from a dictionary.
        
        Args:
            action_dict: Action definition
            
        Returns:
            Action object
        """
        action_type = action_dict.pop('type')
        return cls(action_type, **action_dict)
    
    def execute(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the action on a message.
        
        Args:
            message: Message to act on
            
        Returns:
            Modified message
        """
        if self.action_type == 'route':
            return self._execute_route_action(message)
        elif self.action_type == 'transform':
            return self._execute_transform_action(message)
        elif self.action_type == 'log':
            return self._execute_log_action(message)
        elif self.action_type == 'drop':
            return self._execute_drop_action(message)
        
        return message
    
    def _execute_route_action(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a route action.
        
        Args:
            message: Message to route
            
        Returns:
            Modified message
        """
        destination = self.params.get('destination')
        if destination:
            message['destination'] = {
                'type': 'agent',
                'id': destination
            }
        
        return message
    
    def _execute_transform_action(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a transform action.
        
        Args:
            message: Message to transform
            
        Returns:
            Modified message
        """
        transformation = self.params.get('transformation')
        if transformation:
            # Apply transformation
            # This is a placeholder for actual transformation logic
            pass
        
        return message
    
    def _execute_log_action(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a log action.
        
        Args:
            message: Message to log
            
        Returns:
            Unmodified message
        """
        log_level = self.params.get('level', 'info')
        log_message = self.params.get('message', 'Message routed')
        
        if log_level == 'debug':
            logger.debug(f"{log_message}: {message}")
        elif log_level == 'info':
            logger.info(f"{log_message}: {message}")
        elif log_level == 'warning':
            logger.warning(f"{log_message}: {message}")
        elif log_level == 'error':
            logger.error(f"{log_message}: {message}")
        
        return message
    
    def _execute_drop_action(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a drop action.
        
        Args:
            message: Message to drop
            
        Returns:
            None to indicate the message should be dropped
        """
        return None


class RouteAction(Action):
    """Route action for rule-based routing."""
    
    def __init__(self, destination: str):
        """
        Initialize the route action.
        
        Args:
            destination: Destination for the message
        """
        super().__init__('route', destination=destination)
    
    def get_destinations(self, message: Dict[str, Any]) -> List[str]:
        """
        Get destinations for a message.
        
        Args:
            message: Message to route
            
        Returns:
            List of destination IDs
        """
        return [self.params.get('destination')]


class Rule:
    """Rule for rule-based routing."""
    
    def __init__(self, name: str, conditions: List[Condition], actions: List[Action], is_terminal: bool = False):
        """
        Initialize the rule.
        
        Args:
            name: Rule name
            conditions: List of conditions that must be met for the rule to apply
            actions: List of actions to take when the rule applies
            is_terminal: Whether this rule is terminal (stops rule processing)
        """
        self.name = name
        self.conditions = conditions
        self.actions = actions
        self.is_terminal = is_terminal
    
    @classmethod
    def from_dict(cls, rule_dict: Dict[str, Any]) -> 'Rule':
        """
        Create a rule from a dictionary.
        
        Args:
            rule_dict: Rule definition
            
        Returns:
            Rule object
        """
        name = rule_dict.get('name', 'unnamed')
        conditions = [Condition.from_dict(c) for c in rule_dict.get('conditions', [])]
        actions = [Action.from_dict(a) for a in rule_dict.get('actions', [])]
        is_terminal = rule_dict.get('is_terminal', False)
        
        return cls(name, conditions, actions, is_terminal)
    
    def matches(self, message: Dict[str, Any]) -> bool:
        """
        Check if the rule matches a message.
        
        Args:
            message: Message to check
            
        Returns:
            True if the rule matches, False otherwise
        """
        return all(condition.matches(message) for condition in self.conditions)
    
    def get_destinations(self, message: Dict[str, Any]) -> List[str]:
        """
        Get destinations for a message.
        
        Args:
            message: Message to route
            
        Returns:
            List of destination IDs
        """
        destinations = []
        
        for action in self.actions:
            if isinstance(action, RouteAction):
                destinations.extend(action.get_destinations(message))
        
        return destinations
    
    def apply(self, message: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
        """
        Apply the rule to a message.
        
        Args:
            message: Message to apply the rule to
            
        Returns:
            Tuple of (modified message, whether to stop processing)
        """
        if not self.matches(message):
            return message, False
        
        modified_message = message
        for action in self.actions:
            result = action.execute(modified_message)
            if result is None:
                # Message was dropped
                return None, True
            modified_message = result
        
        return modified_message, self.is_terminal


class RuleBasedRouter:
    """Router for rule-based message routing."""
    
    def __init__(self):
        """Initialize the rule-based router."""
        self.rules = []  # list of Rule objects
    
    def add_rule(self, rule: Rule) -> None:
        """
        Add a routing rule.
        
        Args:
            rule: Rule to add
        """
        self.rules.append(rule)
        logger.debug(f"Added rule-based routing rule: {rule.name}")
    
    def add_rule_from_dict(self, rule_dict: Dict[str, Any]) -> None:
        """
        Add a routing rule from a dictionary.
        
        Args:
            rule_dict: Rule definition
        """
        rule = Rule.from_dict(rule_dict)
        self.add_rule(rule)
    
    def get_destinations(self, message: Dict[str, Any]) -> List[str]:
        """
        Get destinations for a message.
        
        Args:
            message: Message to route
            
        Returns:
            List of destination IDs
        """
        destinations = []
        
        for rule in self.rules:
            if rule.matches(message):
                destinations.extend(rule.get_destinations(message))
                
                # If the rule is marked as terminal, stop processing rules
                if rule.is_terminal:
                    break
        
        return destinations
    
    def route_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Route a message according to the rules.
        
        Args:
            message: Message to route
            
        Returns:
            Modified message or None if the message was dropped
        """
        modified_message = message
        
        for rule in self.rules:
            result, stop = rule.apply(modified_message)
            if result is None:
                # Message was dropped
                return None
            
            modified_message = result
            
            if stop:
                break
        
        return modified_message
