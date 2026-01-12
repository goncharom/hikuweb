# ABOUTME: Translates JSON Schema definitions to Pydantic models.
# ABOUTME: Supports primitive types with required/optional field handling.

from typing import Any

from pydantic import create_model

TYPE_MAP = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
}


def _map_primitive_type(prop: dict) -> type:
    """Map JSON Schema type to Python type.

    Args:
        prop: Property definition from JSON Schema.

    Returns:
        Python type corresponding to the JSON Schema type.
    """
    return TYPE_MAP.get(prop.get("type"), Any)


def json_schema_to_pydantic(schema: dict, model_name: str = "DynamicModel") -> type:
    """Convert JSON Schema to Pydantic model.

    Args:
        schema: JSON Schema object definition.
        model_name: Name for the generated Pydantic model.

    Returns:
        Dynamically created Pydantic model class.

    Example:
        >>> schema = {
        ...     "type": "object",
        ...     "properties": {
        ...         "name": {"type": "string"},
        ...         "age": {"type": "integer"}
        ...     },
        ...     "required": ["name"]
        ... }
        >>> Model = json_schema_to_pydantic(schema)
        >>> instance = Model(name="Alice", age=30)
    """
    properties = schema.get("properties", {})
    required = set(schema.get("required", []))

    field_definitions = {}
    for name, prop in properties.items():
        field_type = _map_primitive_type(prop)

        if name in required:
            # Required field: no default value (use ... Ellipsis)
            field_definitions[name] = (field_type, ...)
        else:
            # Optional field: use default from schema or None
            default = prop.get("default", None)
            field_definitions[name] = (field_type | None, default)

    return create_model(model_name, **field_definitions)
