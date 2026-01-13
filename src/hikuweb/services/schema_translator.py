# ABOUTME: Translates JSON Schema definitions to Pydantic models.
# ABOUTME: Supports primitive types, arrays, and nested objects with recursion.

from typing import Any

from pydantic import create_model

TYPE_MAP = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
}

VALID_TYPES = {"string", "integer", "number", "boolean", "object", "array"}


class SchemaValidationError(ValueError):
    """Raised when JSON Schema contains invalid or unsupported types."""


def validate_schema(schema: dict, path: str = "root") -> None:
    """Validate JSON Schema for unsupported types.

    Args:
        schema: JSON Schema object definition to validate.
        path: Current path in schema (for error messages).

    Raises:
        SchemaValidationError: If schema contains unsupported types.
    """
    schema_type = schema.get("type")

    if schema_type and schema_type not in VALID_TYPES:
        raise SchemaValidationError(
            f"Unsupported type '{schema_type}' at {path}. "
            f"Supported types: {', '.join(sorted(VALID_TYPES))}"
        )

    # Validate nested properties for object types
    if schema_type == "object":
        properties = schema.get("properties", {})
        for prop_name, prop_schema in properties.items():
            validate_schema(prop_schema, f"{path}.{prop_name}")

    # Validate array items
    if schema_type == "array":
        items = schema.get("items", {})
        if items:
            validate_schema(items, f"{path}[]")


def _map_primitive_type(prop: dict) -> Any:
    """Map JSON Schema type to Python type.

    Args:
        prop: Property definition from JSON Schema.

    Returns:
        Python type corresponding to the JSON Schema type.
    """
    prop_type = prop.get("type")
    if prop_type is None:
        return Any
    return TYPE_MAP.get(prop_type, Any)


def _get_field_type(prop: dict, model_name: str, field_name: str) -> Any:
    """Get field type including array and nested object support.

    Args:
        prop: Property definition from JSON Schema.
        model_name: Parent model name for generating nested model names.
        field_name: Field name for generating nested model names.

    Returns:
        Python type for the field (primitive, list[T], or nested model).
    """
    prop_type = prop.get("type")

    if prop_type == "object":
        # Recursively create nested Pydantic model
        nested_model_name = f"{model_name}_{field_name}"
        return json_schema_to_pydantic(prop, nested_model_name)

    if prop_type == "array":
        items = prop.get("items", {})
        items_type = items.get("type")

        if items_type == "object":
            # Array of objects - recursively create model for array items
            nested_model_name = f"{model_name}_{field_name}_item"
            inner_type = json_schema_to_pydantic(items, nested_model_name)
        else:
            # Array of primitives
            inner_type = _map_primitive_type(items)

        return list[inner_type]

    return _map_primitive_type(prop)


def json_schema_to_pydantic(schema: dict, model_name: str = "DynamicModel") -> type:
    """Convert JSON Schema to Pydantic model.

    Args:
        schema: JSON Schema object definition.
        model_name: Name for the generated Pydantic model.

    Returns:
        Dynamically created Pydantic model class.

    Raises:
        SchemaValidationError: If schema contains unsupported types.

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
    # Validate schema before processing
    validate_schema(schema)

    properties = schema.get("properties", {})
    required = set(schema.get("required", []))

    field_definitions = {}
    for name, prop in properties.items():
        field_type = _get_field_type(prop, model_name, name)

        if name in required:
            # Required field: no default value (use ... Ellipsis)
            field_definitions[name] = (field_type, ...)
        else:
            # Optional field: use default from schema or None
            default = prop.get("default", None)
            field_definitions[name] = (field_type | None, default)

    return create_model(model_name, **field_definitions)
