# ABOUTME: Tests for JSON Schema to Pydantic model translation.
# ABOUTME: Verifies primitive types, arrays, nested objects, and required/optional handling.
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


class TestArrayTypes:
    """Tests for array type translations."""

    def test_array_of_strings(self):
        """Should translate array of strings to list[str] field."""
        schema = {
            "type": "object",
            "properties": {"tags": {"type": "array", "items": {"type": "string"}}},
        }
        Model = json_schema_to_pydantic(schema)
        instance = Model(tags=["a", "b", "c"])
        assert instance.tags == ["a", "b", "c"]

    def test_array_of_integers(self):
        """Should translate array of integers to list[int] field."""
        schema = {
            "type": "object",
            "properties": {"scores": {"type": "array", "items": {"type": "integer"}}},
        }
        Model = json_schema_to_pydantic(schema)
        instance = Model(scores=[1, 2, 3])
        assert instance.scores == [1, 2, 3]

    def test_array_of_numbers(self):
        """Should translate array of numbers to list[float] field."""
        schema = {
            "type": "object",
            "properties": {"prices": {"type": "array", "items": {"type": "number"}}},
        }
        Model = json_schema_to_pydantic(schema)
        instance = Model(prices=[1.5, 2.7, 3.9])
        assert instance.prices == [1.5, 2.7, 3.9]

    def test_array_of_booleans(self):
        """Should translate array of booleans to list[bool] field."""
        schema = {
            "type": "object",
            "properties": {"flags": {"type": "array", "items": {"type": "boolean"}}},
        }
        Model = json_schema_to_pydantic(schema)
        instance = Model(flags=[True, False, True])
        assert instance.flags == [True, False, True]

    def test_array_without_items(self):
        """Should default to list[Any] when items not specified."""
        schema = {
            "type": "object",
            "properties": {"data": {"type": "array"}},
        }
        Model = json_schema_to_pydantic(schema)
        instance = Model(data=[1, "two", True])
        assert len(instance.data) == 3
        assert instance.data[0] == 1
        assert instance.data[1] == "two"
        assert instance.data[2] is True

    def test_required_array_field(self):
        """Should enforce required array field."""
        schema = {
            "type": "object",
            "properties": {"items": {"type": "array", "items": {"type": "string"}}},
            "required": ["items"],
        }
        Model = json_schema_to_pydantic(schema)
        with pytest.raises(ValidationError):
            Model()

    def test_optional_array_field_defaults_to_none(self):
        """Should default optional array field to None."""
        schema = {
            "type": "object",
            "properties": {"tags": {"type": "array", "items": {"type": "string"}}},
        }
        Model = json_schema_to_pydantic(schema)
        instance = Model()
        assert instance.tags is None

    def test_validates_array_data_correctly(self):
        """Should validate array element types."""
        schema = {
            "type": "object",
            "properties": {"scores": {"type": "array", "items": {"type": "integer"}}},
            "required": ["scores"],
        }
        Model = json_schema_to_pydantic(schema)
        instance = Model(scores=[1, 2, 3])
        assert instance.scores == [1, 2, 3]

    def test_rejects_non_array_for_array_field(self):
        """Should reject non-array data for array field."""
        schema = {
            "type": "object",
            "properties": {"tags": {"type": "array", "items": {"type": "string"}}},
            "required": ["tags"],
        }
        Model = json_schema_to_pydantic(schema)
        with pytest.raises(ValidationError):
            Model(tags="not_an_array")


class TestNestedObjects:
    """Tests for nested object type translations."""

    def test_nested_object(self):
        """Should translate nested object property to nested Pydantic model."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "address": {
                    "type": "object",
                    "properties": {
                        "street": {"type": "string"},
                        "city": {"type": "string"},
                    },
                    "required": ["street"],
                },
            },
            "required": ["name"],
        }
        Model = json_schema_to_pydantic(schema)
        instance = Model(name="Test", address={"street": "123 Main", "city": "NYC"})
        assert instance.name == "Test"
        assert instance.address.street == "123 Main"
        assert instance.address.city == "NYC"

    def test_deeply_nested_objects(self):
        """Should handle deeply nested objects (2+ levels)."""
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "profile": {
                            "type": "object",
                            "properties": {
                                "bio": {"type": "string"},
                                "age": {"type": "integer"},
                            },
                        },
                    },
                },
            },
        }
        Model = json_schema_to_pydantic(schema)
        instance = Model(user={"name": "Alice", "profile": {"bio": "Engineer", "age": 30}})
        assert instance.user.name == "Alice"
        assert instance.user.profile.bio == "Engineer"
        assert instance.user.profile.age == 30

    def test_array_of_objects(self):
        """Should handle arrays of objects."""
        schema = {
            "type": "object",
            "properties": {
                "tags": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "value": {"type": "integer"},
                        },
                    },
                },
            },
        }
        Model = json_schema_to_pydantic(schema)
        instance = Model(tags=[{"name": "tag1", "value": 1}, {"name": "tag2", "value": 2}])
        assert len(instance.tags) == 2
        assert instance.tags[0].name == "tag1"
        assert instance.tags[0].value == 1
        assert instance.tags[1].name == "tag2"
        assert instance.tags[1].value == 2

    def test_required_nested_object_field(self):
        """Should enforce required nested object field."""
        schema = {
            "type": "object",
            "properties": {
                "address": {
                    "type": "object",
                    "properties": {"street": {"type": "string"}},
                },
            },
            "required": ["address"],
        }
        Model = json_schema_to_pydantic(schema)
        with pytest.raises(ValidationError):
            Model()

    def test_optional_nested_object_field_defaults_to_none(self):
        """Should default optional nested object field to None."""
        schema = {
            "type": "object",
            "properties": {
                "address": {
                    "type": "object",
                    "properties": {"street": {"type": "string"}},
                },
            },
        }
        Model = json_schema_to_pydantic(schema)
        instance = Model()
        assert instance.address is None

    def test_validates_nested_data_correctly(self):
        """Should validate nested object data correctly."""
        schema = {
            "type": "object",
            "properties": {
                "person": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "age": {"type": "integer"},
                    },
                    "required": ["name"],
                },
            },
            "required": ["person"],
        }
        Model = json_schema_to_pydantic(schema)
        instance = Model(person={"name": "Bob", "age": 25})
        assert instance.person.name == "Bob"
        assert instance.person.age == 25

    def test_rejects_invalid_nested_data(self):
        """Should reject invalid nested data."""
        schema = {
            "type": "object",
            "properties": {
                "person": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "age": {"type": "integer"},
                    },
                    "required": ["name"],
                },
            },
            "required": ["person"],
        }
        Model = json_schema_to_pydantic(schema)
        # Missing required field 'name' in nested object
        with pytest.raises(ValidationError):
            Model(person={"age": 25})
