"""
Migration script to update query references to use singular table names.

This script updates references to plural table names in SQLAlchemy queries
to use singular table names instead.
"""

import os
import re
from pathlib import Path

def update_file(file_path, replacements):
    """
    Update a file with the given replacements.
    
    Args:
        file_path: Path to the file to update
        replacements: List of (pattern, replacement) tuples
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def main():
    """Update query references to use singular table names."""
    # Define the replacements
    replacements = [
        # agent_tools -> agent_tool
        (r'agent_tools\.append', 'agent_tool.append'),
        (r'agent_tools\.c\.', 'agent_tool.c.'),
        (r'secondary="agent_tools"', 'secondary="agent_tool"'),
        (r'secondary=agent_tools', 'secondary=agent_tool'),
        
        # models -> model
        (r'models\.list', 'model.list'),
        (r'models\.id', 'model.id'),
        (r'models\.c\.', 'model.c.'),
        (r'ForeignKey\("models\.', 'ForeignKey("model.'),
        (r'"models": list\(models\.values\(\)\)', '"models": list(model.values())'),
        
        # task_dependencies -> task_dependency
        (r'task_dependencies\.c\.', 'task_dependency.c.'),
        (r'secondary="task_dependencies"', 'secondary="task_dependency"'),
        (r'secondary=task_dependencies', 'secondary=task_dependency'),
        
        # provider_quotas -> provider_quota
        (r'provider_quotas\.c\.', 'provider_quota.c.'),
        
        # requests -> request
        (r'requests\.c\.', 'request.c.'),
        (r'ForeignKey\("requests\.', 'ForeignKey("request.'),
    ]
    
    # Define the directories to search
    directories = [
        'services/web-dashboard/app',
    ]
    
    # Update files
    for directory in directories:
        if not os.path.exists(directory):
            print(f"Directory {directory} does not exist, skipping")
            continue
        
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    update_file(file_path, replacements)
                    print(f"Updated {file_path}")

if __name__ == '__main__':
    main()
