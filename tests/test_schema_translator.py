# ABOUTME: Tests for JSON Schema to Pydantic model translation.
# ABOUTME: Verifies primitive type mapping, required/optional handling.
# ruff: noqa: N806

import pytest
from pydantic import ValidationError

from hikuweb.services.schema_translator import json_schema_to_pydantic


class TestPrimitiveTypes:
    """Tests for primitive type translations."""

    def test_string_type(self):
        """Should translate string type to str field."""
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        Model = json_schema_to_pydantic(schema)
        instance = Model(name="test")
        assert instance.name == "test"

    def test_integer_type(self):
        """Should translate integer type to int field."""
        schema = {"type": "object", "properties": {"age": {"type": "integer"}}}
        Model = json_schema_to_pydantic(schema)
        instance = Model(age=42)
        assert instance.age == 42

    def test_number_type(self):
        """Should translate number type to float field."""
        schema = {"type": "object", "properties": {"price": {"type": "number"}}}
        Model = json_schema_to_pydantic(schema)
        instance = Model(price=19.99)
        assert instance.price == 19.99

    def test_boolean_type(self):
        """Should translate boolean type to bool field."""
        schema = {"type": "object", "properties": {"active": {"type": "boolean"}}}
        Model = json_schema_to_pydantic(schema)
        instance = Model(active=True)
        assert instance.active is True

    def test_multiple_primitive_types(self):
        """Should handle multiple primitive types in one schema."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
                "score": {"type": "number"},
                "verified": {"type": "boolean"},
            },
        }
        Model = json_schema_to_pydantic(schema)
        instance = Model(name="Alice", age=30, score=95.5, verified=True)
        assert instance.name == "Alice"
        assert instance.age == 30
        assert instance.score == 95.5
        assert instance.verified is True


class TestRequiredFields:
    """Tests for required vs optional field handling."""

    def test_required_field_must_be_provided(self):
        """Should raise ValidationError when required field is missing."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        Model = json_schema_to_pydantic(schema)
        with pytest.raises(ValidationError):
            Model()

    def test_required_field_accepts_value(self):
        """Should accept value for required field."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        Model = json_schema_to_pydantic(schema)
        instance = Model(name="test")
        assert instance.name == "test"

    def test_optional_field_defaults_to_none(self):
        """Should default to None for optional field."""
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        Model = json_schema_to_pydantic(schema)
        instance = Model()
        assert instance.name is None

    def test_optional_field_accepts_value(self):
        """Should accept value for optional field."""
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        Model = json_schema_to_pydantic(schema)
        instance = Model(name="test")
        assert instance.name == "test"

    def test_mixed_required_and_optional(self):
        """Should handle mix of required and optional fields."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
                "email": {"type": "string"},
            },
            "required": ["name", "age"],
        }
        Model = json_schema_to_pydantic(schema)
        instance = Model(name="Alice", age=30)
        assert instance.name == "Alice"
        assert instance.age == 30
        assert instance.email is None


class TestDefaultValues:
    """Tests for default value handling from schema."""

    def test_default_string_value(self):
        """Should use default value from schema for string."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string", "default": "anonymous"}},
        }
        Model = json_schema_to_pydantic(schema)
        instance = Model()
        assert instance.name == "anonymous"

    def test_default_integer_value(self):
        """Should use default value from schema for integer."""
        schema = {
            "type": "object",
            "properties": {"age": {"type": "integer", "default": 0}},
        }
        Model = json_schema_to_pydantic(schema)
        instance = Model()
        assert instance.age == 0

    def test_default_number_value(self):
        """Should use default value from schema for number."""
        schema = {
            "type": "object",
            "properties": {"price": {"type": "number", "default": 9.99}},
        }
        Model = json_schema_to_pydantic(schema)
        instance = Model()
        assert instance.price == 9.99

    def test_default_boolean_value(self):
        """Should use default value from schema for boolean."""
        schema = {
            "type": "object",
            "properties": {"active": {"type": "boolean", "default": False}},
        }
        Model = json_schema_to_pydantic(schema)
        instance = Model()
        assert instance.active is False

    def test_override_default_value(self):
        """Should allow overriding default value."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string", "default": "anonymous"}},
        }
        Model = json_schema_to_pydantic(schema)
        instance = Model(name="Alice")
        assert instance.name == "Alice"


class TestValidation:
    """Tests for model validation."""

    def test_rejects_wrong_type_for_string(self):
        """Should reject non-string value for string field."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        Model = json_schema_to_pydantic(schema)
        with pytest.raises(ValidationError):
            Model(name=123)

    def test_rejects_wrong_type_for_integer(self):
        """Should reject non-integer value for integer field."""
        schema = {
            "type": "object",
            "properties": {"age": {"type": "integer"}},
            "required": ["age"],
        }
        Model = json_schema_to_pydantic(schema)
        with pytest.raises(ValidationError):
            Model(age="not_an_int")

    def test_rejects_wrong_type_for_number(self):
        """Should reject non-numeric value for number field."""
        schema = {
            "type": "object",
            "properties": {"price": {"type": "number"}},
            "required": ["price"],
        }
        Model = json_schema_to_pydantic(schema)
        with pytest.raises(ValidationError):
            Model(price="not_a_number")

    def test_rejects_wrong_type_for_boolean(self):
        """Should reject non-boolean value for boolean field."""
        schema = {
            "type": "object",
            "properties": {"active": {"type": "boolean"}},
            "required": ["active"],
        }
        Model = json_schema_to_pydantic(schema)
        with pytest.raises(ValidationError):
            Model(active="not_a_bool")

    def test_accepts_valid_data(self):
        """Should accept data that matches schema."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
                "score": {"type": "number"},
                "active": {"type": "boolean"},
            },
            "required": ["name", "age"],
        }
        Model = json_schema_to_pydantic(schema)
        instance = Model(name="Alice", age=30, score=95.5, active=True)
        assert instance.name == "Alice"
        assert instance.age == 30
        assert instance.score == 95.5
        assert instance.active is True


class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_schema(self):
        """Should create model with no fields for empty schema."""
        schema = {"type": "object", "properties": {}}
        Model = json_schema_to_pydantic(schema)
        instance = Model()
        assert instance is not None

    def test_schema_with_no_properties_key(self):
        """Should handle schema without properties key."""
        schema = {"type": "object"}
        Model = json_schema_to_pydantic(schema)
        instance = Model()
        assert instance is not None
