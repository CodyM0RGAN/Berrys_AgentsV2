"""
Feature flag utility.

This module provides a utility for managing feature flags.
"""

import os
import logging

logger = logging.getLogger(__name__)

class FeatureFlags:
    """
    Feature flag utility.
    """

    def __init__(self, config_prefix="FEATURE_"):
        """
        Initialize the feature flags.
        """
        self.config_prefix = config_prefix
        self.flags = {}
        self.load_flags()

    def load_flags(self):
        """
        Load feature flags from environment variables.
        """
        for key, value in os.environ.items():
            if key.startswith(self.config_prefix):
                flag_name = key[len(self.config_prefix):].lower()
                try:
                    self.flags[flag_name] = bool(int(value))
                except ValueError:
                    logger.warning(f"Invalid feature flag value for {key}: {value}. Expected 0 or 1.")
                    self.flags[flag_name] = False

    def is_enabled(self, flag_name):
        """
        Check if a feature flag is enabled.
        """
        return self.flags.get(flag_name, False)

# Create a global feature flags instance
feature_flags = FeatureFlags()

def is_feature_enabled(flag_name):
    """
    Helper function to check if a feature is enabled.
    """
    return feature_flags.is_enabled(flag_name)
