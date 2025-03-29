import logging
import json
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

logger = logging.getLogger(__name__)


class JSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder for handling special types.
    """
    
    def default(self, obj: Any) -> Any:
        """
        Convert special types to JSON-serializable types.
        
        Args:
            obj: Object to convert
            
        Returns:
            JSON-serializable object
        """
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, UUID):
            return str(obj)
        return super().default(obj)


def json_dumps(obj: Any) -> str:
    """
    Convert object to JSON string with custom encoder.
    
    Args:
        obj: Object to convert
        
    Returns:
        str: JSON string
    """
    return json.dumps(obj, cls=JSONEncoder)


def json_loads(s: str) -> Any:
    """
    Parse JSON string to object.
    
    Args:
        s: JSON string
        
    Returns:
        Any: Parsed object
    """
    return json.loads(s)


def format_error_response(
    message: str,
    code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Format error response.
    
    Args:
        message: Error message
        code: Error code
        details: Error details
        
    Returns:
        Dict[str, Any]: Formatted error response
    """
    response = {
        "detail": message,
    }
    
    if code:
        response["code"] = code
    
    if details:
        response["details"] = details
    
    return response


def paginate_results(
    items: List[Any],
    total: int,
    page: int,
    page_size: int,
) -> Dict[str, Any]:
    """
    Format paginated results.
    
    Args:
        items: List of items
        total: Total number of items
        page: Current page number
        page_size: Page size
        
    Returns:
        Dict[str, Any]: Formatted paginated results
    """
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    
    return {
        "items": items,
        "pagination": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        },
    }


def filter_none_values(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Filter out None values from dictionary.
    
    Args:
        data: Dictionary to filter
        
    Returns:
        Dict[str, Any]: Filtered dictionary
    """
    return {k: v for k, v in data.items() if v is not None}


def merge_dicts(
    base: Dict[str, Any],
    update: Dict[str, Any],
    overwrite: bool = True,
) -> Dict[str, Any]:
    """
    Merge two dictionaries.
    
    Args:
        base: Base dictionary
        update: Dictionary with updates
        overwrite: Whether to overwrite existing values
        
    Returns:
        Dict[str, Any]: Merged dictionary
    """
    result = base.copy()
    
    for key, value in update.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # Recursively merge nested dictionaries
            result[key] = merge_dicts(result[key], value, overwrite)
        elif key not in result or overwrite:
            # Add new key or overwrite existing value
            result[key] = value
    
    return result


def safe_get(
    data: Dict[str, Any],
    path: str,
    default: Any = None,
) -> Any:
    """
    Safely get value from nested dictionary using dot notation.
    
    Args:
        data: Dictionary to get value from
        path: Path to value using dot notation (e.g., "user.address.city")
        default: Default value if path not found
        
    Returns:
        Any: Value at path or default
    """
    keys = path.split(".")
    result = data
    
    for key in keys:
        if isinstance(result, dict) and key in result:
            result = result[key]
        else:
            return default
    
    return result
