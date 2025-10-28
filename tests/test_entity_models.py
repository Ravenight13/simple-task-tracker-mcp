"""
Tests for Entity Pydantic models.

Validates:
- Entity field validation
- EntityCreate and EntityUpdate models
- JSON metadata validation
- Tag normalization
- Helper methods
"""

import json
from datetime import datetime

import pytest
from pydantic import ValidationError

from task_mcp.models import Entity, EntityCreate, EntityUpdate, validate_json_metadata


class TestEntityValidation:
    """Test Entity model field validation."""

    def test_entity_type_validation_valid(self):
        """Valid entity types should be accepted."""
        entity_file = Entity(entity_type="file", name="test.py")
        assert entity_file.entity_type == "file"

        entity_other = Entity(entity_type="other", name="vendor")
        assert entity_other.entity_type == "other"

    def test_entity_type_validation_invalid(self):
        """Invalid entity types should raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Entity(entity_type="invalid", name="test")

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "entity_type must be one of" in errors[0]["msg"]

    def test_name_required(self):
        """Name field is required."""
        with pytest.raises(ValidationError) as exc_info:
            Entity(entity_type="file")  # type: ignore

        errors = exc_info.value.errors()
        assert any(e["type"] == "missing" and e["loc"] == ("name",) for e in errors)

    def test_name_min_length(self):
        """Name must be at least 1 character."""
        with pytest.raises(ValidationError) as exc_info:
            Entity(entity_type="file", name="")

        errors = exc_info.value.errors()
        assert any("at least 1 character" in str(e["msg"]) for e in errors)

    def test_name_max_length(self):
        """Name must not exceed 500 characters."""
        long_name = "a" * 501
        with pytest.raises(ValidationError) as exc_info:
            Entity(entity_type="file", name=long_name)

        errors = exc_info.value.errors()
        assert any("at most 500 character" in str(e["msg"]) for e in errors)

    def test_identifier_max_length(self):
        """Identifier must not exceed 1000 characters."""
        long_identifier = "a" * 1001
        with pytest.raises(ValidationError) as exc_info:
            Entity(entity_type="file", name="test", identifier=long_identifier)

        errors = exc_info.value.errors()
        assert any("at most 1000 character" in str(e["msg"]) for e in errors)

    def test_description_max_length(self):
        """Description cannot exceed 10,000 characters."""
        long_description = "a" * 10001
        with pytest.raises(ValidationError) as exc_info:
            Entity(entity_type="file", name="test", description=long_description)

        errors = exc_info.value.errors()
        assert any("10000" in str(e["msg"]) for e in errors)

    def test_description_valid_length(self):
        """Description up to 10,000 characters should be accepted."""
        valid_description = "a" * 10000
        entity = Entity(entity_type="file", name="test", description=valid_description)
        assert len(entity.description) == 10000  # type: ignore

    def test_tags_normalization(self):
        """Tags should be normalized to lowercase with single spaces."""
        entity = Entity(
            entity_type="file",
            name="test",
            tags="  Python   Django  REST  "
        )
        assert entity.tags == "python django rest"

    def test_metadata_json_validation_valid_dict(self):
        """Valid JSON metadata (dict) should be accepted."""
        metadata = {"language": "python", "line_count": 250}
        entity = Entity(
            entity_type="file",
            name="test.py",
            metadata=metadata  # type: ignore
        )
        assert entity.metadata == json.dumps(metadata)

    def test_metadata_json_validation_valid_string(self):
        """Valid JSON metadata (string) should be accepted."""
        metadata_str = '{"language": "python"}'
        entity = Entity(
            entity_type="file",
            name="test.py",
            metadata=metadata_str
        )
        assert entity.metadata == metadata_str

    def test_metadata_json_validation_invalid(self):
        """Invalid JSON metadata should raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Entity(
                entity_type="file",
                name="test.py",
                metadata="invalid json{"
            )

        errors = exc_info.value.errors()
        assert any("must be valid JSON" in str(e["msg"]) for e in errors)

    def test_metadata_none_allowed(self):
        """Metadata can be None."""
        entity = Entity(entity_type="file", name="test.py", metadata=None)
        assert entity.metadata is None

    def test_default_values(self):
        """Entity should have correct default values."""
        entity = Entity(entity_type="file", name="test.py")
        assert entity.id is None
        assert entity.identifier is None
        assert entity.description is None
        assert entity.metadata is None
        assert entity.tags is None
        assert entity.created_by is None
        assert entity.created_at is None
        assert entity.updated_at is None
        assert entity.deleted_at is None


class TestEntityHelperMethods:
    """Test Entity helper methods."""

    def test_get_metadata_dict_with_valid_json(self):
        """get_metadata_dict should parse valid JSON metadata."""
        metadata = {"language": "python", "line_count": 250}
        entity = Entity(
            entity_type="file",
            name="test.py",
            metadata=json.dumps(metadata)
        )
        assert entity.get_metadata_dict() == metadata

    def test_get_metadata_dict_empty(self):
        """get_metadata_dict should return empty dict when metadata is None."""
        entity = Entity(entity_type="file", name="test.py", metadata=None)
        assert entity.get_metadata_dict() == {}

    def test_get_metadata_dict_invalid_json(self):
        """get_metadata_dict should return empty dict for invalid JSON."""
        # Note: With validate_assignment=True, we cannot set invalid JSON
        # So we'll use model_construct to bypass validation for testing
        entity = Entity.model_construct(
            entity_type="file",
            name="test.py",
            metadata="invalid"
        )
        assert entity.get_metadata_dict() == {}

    def test_get_metadata_dict_non_dict_json(self):
        """get_metadata_dict should return empty dict if JSON is not a dict."""
        entity = Entity(entity_type="file", name="test.py")
        entity.metadata = json.dumps(["array", "not", "dict"])
        assert entity.get_metadata_dict() == {}


class TestEntityCreate:
    """Test EntityCreate model."""

    def test_create_entity_minimal(self):
        """EntityCreate with minimal required fields should work."""
        entity_create = EntityCreate(entity_type="file", name="test.py")
        assert entity_create.entity_type == "file"
        assert entity_create.name == "test.py"
        assert entity_create.identifier is None
        assert entity_create.description is None
        assert entity_create.metadata is None
        assert entity_create.tags is None

    def test_create_entity_full(self):
        """EntityCreate with all fields should work."""
        metadata = {"language": "python"}
        entity_create = EntityCreate(
            entity_type="other",
            name="ABC Vendor",
            identifier="ABC-INS",
            description="Insurance vendor",
            metadata=metadata,  # type: ignore
            tags="vendor insurance",
            created_by="conv-123"
        )
        assert entity_create.entity_type == "other"
        assert entity_create.name == "ABC Vendor"
        assert entity_create.identifier == "ABC-INS"
        assert entity_create.description == "Insurance vendor"
        assert entity_create.metadata == json.dumps(metadata)
        assert entity_create.tags == "vendor insurance"
        assert entity_create.created_by == "conv-123"

    def test_create_entity_validates_entity_type(self):
        """EntityCreate should validate entity_type."""
        with pytest.raises(ValidationError) as exc_info:
            EntityCreate(entity_type="invalid", name="test")

        errors = exc_info.value.errors()
        assert any("entity_type must be one of" in str(e["msg"]) for e in errors)

    def test_create_entity_validates_description_length(self):
        """EntityCreate should validate description length."""
        long_description = "a" * 10001
        with pytest.raises(ValidationError) as exc_info:
            EntityCreate(
                entity_type="file",
                name="test",
                description=long_description
            )

        errors = exc_info.value.errors()
        assert any("10000" in str(e["msg"]) for e in errors)

    def test_create_entity_normalizes_tags(self):
        """EntityCreate should normalize tags."""
        entity_create = EntityCreate(
            entity_type="file",
            name="test",
            tags="  Python   Django  "
        )
        assert entity_create.tags == "python django"


class TestEntityUpdate:
    """Test EntityUpdate model."""

    def test_update_entity_all_none(self):
        """EntityUpdate with all None fields should be valid."""
        entity_update = EntityUpdate()
        assert entity_update.name is None
        assert entity_update.identifier is None
        assert entity_update.description is None
        assert entity_update.metadata is None
        assert entity_update.tags is None

    def test_update_entity_partial(self):
        """EntityUpdate with partial fields should work."""
        entity_update = EntityUpdate(
            name="Updated Name",
            tags="new tags"
        )
        assert entity_update.name == "Updated Name"
        assert entity_update.tags == "new tags"
        assert entity_update.identifier is None
        assert entity_update.description is None

    def test_update_entity_validates_description_length(self):
        """EntityUpdate should validate description length."""
        long_description = "a" * 10001
        with pytest.raises(ValidationError) as exc_info:
            EntityUpdate(description=long_description)

        errors = exc_info.value.errors()
        assert any("10000" in str(e["msg"]) for e in errors)

    def test_update_entity_normalizes_tags(self):
        """EntityUpdate should normalize tags."""
        entity_update = EntityUpdate(tags="  Python   Django  ")
        assert entity_update.tags == "python django"

    def test_update_entity_validates_metadata_json(self):
        """EntityUpdate should validate metadata JSON."""
        with pytest.raises(ValidationError) as exc_info:
            EntityUpdate(metadata="invalid json{")

        errors = exc_info.value.errors()
        assert any("must be valid JSON" in str(e["msg"]) for e in errors)


class TestJSONMetadataValidation:
    """Test validate_json_metadata helper function."""

    def test_validate_json_metadata_none(self):
        """None should return None."""
        assert validate_json_metadata(None) is None

    def test_validate_json_metadata_empty_string(self):
        """Empty string should return None."""
        assert validate_json_metadata("") is None

    def test_validate_json_metadata_valid_string(self):
        """Valid JSON string should be returned as-is."""
        json_str = '{"key": "value"}'
        assert validate_json_metadata(json_str) == json_str

    def test_validate_json_metadata_dict(self):
        """Dict should be converted to JSON string."""
        data = {"key": "value", "number": 123}
        result = validate_json_metadata(data)
        assert result == json.dumps(data)
        assert json.loads(result) == data

    def test_validate_json_metadata_list(self):
        """List should be converted to JSON string."""
        data = ["item1", "item2", "item3"]
        result = validate_json_metadata(data)
        assert result == json.dumps(data)
        assert json.loads(result) == data

    def test_validate_json_metadata_invalid_json(self):
        """Invalid JSON string should raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            validate_json_metadata("invalid json{")

        assert "must be valid JSON" in str(exc_info.value)

    def test_validate_json_metadata_complex_dict(self):
        """Complex nested dict should work."""
        data = {
            "vendor_code": "ABC",
            "phase": "active",
            "brands": ["Brand A", "Brand B"],
            "metadata": {
                "contact": "email@example.com",
                "extraction": {
                    "commission_col": "E",
                    "policy_col": "B"
                }
            }
        }
        result = validate_json_metadata(data)
        assert json.loads(result) == data


class TestEntityExamples:
    """Test Entity model with real-world examples."""

    def test_file_entity_example(self):
        """File entity example from documentation."""
        entity = Entity(
            entity_type="file",
            name="Login Controller",
            identifier="/src/auth/login.py",
            metadata='{"language": "python", "line_count": 250}',
            tags="auth backend"
        )
        assert entity.entity_type == "file"
        assert entity.name == "Login Controller"
        assert entity.identifier == "/src/auth/login.py"
        assert entity.tags == "auth backend"
        metadata_dict = entity.get_metadata_dict()
        assert metadata_dict["language"] == "python"
        assert metadata_dict["line_count"] == 250

    def test_vendor_entity_example(self):
        """Vendor entity example from documentation."""
        metadata = {
            "vendor_code": "ABC",
            "format": "xlsx",
            "phase": "active",
            "brands": ["Brand A", "Brand B", "Brand C"]
        }
        entity = Entity(
            entity_type="other",
            name="ABC Insurance Vendor",
            identifier="ABC-INS",
            metadata=metadata,  # type: ignore
            tags="vendor insurance commission"
        )
        assert entity.entity_type == "other"
        assert entity.name == "ABC Insurance Vendor"
        assert entity.identifier == "ABC-INS"
        assert entity.tags == "vendor insurance commission"
        metadata_dict = entity.get_metadata_dict()
        assert metadata_dict["vendor_code"] == "ABC"
        assert metadata_dict["format"] == "xlsx"
        assert metadata_dict["phase"] == "active"
        assert metadata_dict["brands"] == ["Brand A", "Brand B", "Brand C"]

    def test_entity_with_timestamps(self):
        """Entity with timestamp fields."""
        now = datetime.utcnow()
        entity = Entity(
            entity_type="file",
            name="test.py",
            created_by="conv-123",
            created_at=now,
            updated_at=now
        )
        assert entity.created_by == "conv-123"
        assert entity.created_at == now
        assert entity.updated_at == now
        assert entity.deleted_at is None
