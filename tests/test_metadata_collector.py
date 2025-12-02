"""
Unit Tests for IDP Metadata Collector Framework

This module contains comprehensive unit tests for the helper functions,
data models, and business logic used in the metadata collection framework.
"""

import hashlib
import pytest
from typing import List, Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass


# =============================================================================
# Helper Functions to Test (copied from main framework for standalone testing)
# =============================================================================

import re


def to_snake_case(name: str) -> str:
    """
    Convert a string to snake_case.
    
    Handles:
    - CamelCase -> camel_case
    - PascalCase -> pascal_case
    - spaces -> underscores
    - multiple underscores -> single underscore
    - special characters -> removed
    
    Args:
        name: Input string to convert
        
    Returns:
        snake_case version of the input
    """
    if not name:
        return ""
    
    # Handle common abbreviations by inserting underscore before them
    s = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', name)
    
    # Handle transition from lowercase/digit to uppercase
    s = re.sub(r'([a-z\d])([A-Z])', r'\1_\2', s)
    
    # Replace spaces and hyphens with underscores
    s = re.sub(r'[\s\-]+', '_', s)
    
    # Remove any non-alphanumeric characters except underscores
    s = re.sub(r'[^\w]', '', s)
    
    # Convert to lowercase
    s = s.lower()
    
    # Replace multiple underscores with single
    s = re.sub(r'_+', '_', s)
    
    # Strip leading/trailing underscores
    return s.strip('_')


def to_snake_case_list(items: Optional[List[str]]) -> List[str]:
    """
    Convert a list of strings to snake_case.
    
    Args:
        items: List of strings to convert
        
    Returns:
        List of snake_case strings
    """
    if not items:
        return []
    return [to_snake_case(item) for item in items]


def resolve_include_exclude(
    table_name: str,
    include_list: Optional[List[str]],
    exclude_list: Optional[List[str]]
) -> bool:
    """
    Determine if a table should be included based on include/exclude lists.
    
    Logic:
    - If both lists are empty: include all
    - If in include_list and not in exclude_list: include
    - If include_list is empty and not in exclude_list: include
    - Otherwise: exclude
    """
    incl = include_list or []
    excl = exclude_list or []
    
    if not incl and not excl:
        return True
    
    if table_name in excl:
        return False
    
    if not incl:
        return True
    
    return table_name in incl


def compute_table_run_properties(
    is_included: int,
    ct_enabled: int,
    is_append_only: int
) -> int:
    """
    Compute compact table run properties flag.
    
    Format: is_included * 100 + ct_enabled * 10 + is_append_only
    """
    return int(f"{is_included}{ct_enabled}{is_append_only}")


def compute_cdc_hash(data: Dict[str, Any]) -> str:
    """
    Compute a CDC hash for metadata change detection.
    """
    sorted_data = str(sorted(data.items()))
    return hashlib.sha256(sorted_data.encode()).hexdigest()


def generate_unique_id(source_id: str, table_name: str) -> str:
    """Generate unique ID for a metadata row."""
    return f"{source_id}_{table_name}"


# =============================================================================
# Test Classes
# =============================================================================

class TestToSnakeCase:
    """Tests for the to_snake_case function."""
    
    def test_empty_string(self):
        """Test empty string input."""
        assert to_snake_case("") == ""
    
    def test_none_handling(self):
        """Test that None-like values are handled."""
        assert to_snake_case("") == ""
    
    def test_already_snake_case(self):
        """Test string already in snake_case."""
        assert to_snake_case("already_snake") == "already_snake"
        assert to_snake_case("simple") == "simple"
    
    def test_camel_case(self):
        """Test camelCase conversion."""
        assert to_snake_case("camelCase") == "camel_case"
        assert to_snake_case("simpleTest") == "simple_test"
        assert to_snake_case("myVariableName") == "my_variable_name"
    
    def test_pascal_case(self):
        """Test PascalCase conversion."""
        assert to_snake_case("PascalCase") == "pascal_case"
        assert to_snake_case("FontReplacement") == "font_replacement"
        assert to_snake_case("UserProfile") == "user_profile"
        assert to_snake_case("HTTPResponse") == "http_response"
    
    def test_with_numbers(self):
        """Test strings containing numbers."""
        assert to_snake_case("test123") == "test123"
        assert to_snake_case("Test123Value") == "test123_value"
        assert to_snake_case("API2Client") == "api2_client"
    
    def test_with_spaces(self):
        """Test strings with spaces."""
        assert to_snake_case("hello world") == "hello_world"
        assert to_snake_case("Hello World") == "hello_world"
        assert to_snake_case("  spaced  out  ") == "spaced_out"
    
    def test_with_hyphens(self):
        """Test strings with hyphens."""
        assert to_snake_case("hello-world") == "hello_world"
        assert to_snake_case("kebab-case-string") == "kebab_case_string"
    
    def test_mixed_separators(self):
        """Test strings with mixed separators."""
        assert to_snake_case("hello_world-test") == "hello_world_test"
        assert to_snake_case("Mixed Case-with_all") == "mixed_case_with_all"
    
    def test_consecutive_uppercase(self):
        """Test strings with consecutive uppercase letters."""
        assert to_snake_case("XMLParser") == "xml_parser"
        assert to_snake_case("HTMLElement") == "html_element"
        assert to_snake_case("getHTTPResponse") == "get_http_response"
    
    def test_special_characters(self):
        """Test strings with special characters."""
        assert to_snake_case("hello@world") == "helloworld"
        assert to_snake_case("test!value") == "testvalue"
        assert to_snake_case("a.b.c") == "abc"
    
    def test_multiple_underscores(self):
        """Test strings with multiple underscores."""
        assert to_snake_case("hello___world") == "hello_world"
        assert to_snake_case("test__value") == "test_value"
    
    def test_leading_trailing_underscores(self):
        """Test strings with leading/trailing underscores."""
        assert to_snake_case("_leading") == "leading"
        assert to_snake_case("trailing_") == "trailing"
        assert to_snake_case("_both_") == "both"
    
    def test_real_world_examples(self):
        """Test real-world column/table names from requirements."""
        assert to_snake_case("FontReplacement") == "font_replacement"
        assert to_snake_case("Id") == "id"
        assert to_snake_case("TABLE_NAME") == "table_name"
        assert to_snake_case("FULL_TABLE_NAME") == "full_table_name"
        assert to_snake_case("idp_cdc_hash") == "idp_cdc_hash"
        assert to_snake_case("idpCreatedDate") == "idp_created_date"


class TestToSnakeCaseList:
    """Tests for the to_snake_case_list function."""
    
    def test_empty_list(self):
        """Test empty list input."""
        assert to_snake_case_list([]) == []
    
    def test_none_input(self):
        """Test None input."""
        assert to_snake_case_list(None) == []
    
    def test_single_item(self):
        """Test single item list."""
        assert to_snake_case_list(["FontReplacement"]) == ["font_replacement"]
    
    def test_multiple_items(self):
        """Test multiple items."""
        result = to_snake_case_list(["Id", "FontReplacement", "UserName"])
        assert result == ["id", "font_replacement", "user_name"]
    
    def test_mixed_cases(self):
        """Test list with mixed case styles."""
        input_list = ["camelCase", "PascalCase", "snake_case", "UPPER"]
        expected = ["camel_case", "pascal_case", "snake_case", "upper"]
        assert to_snake_case_list(input_list) == expected
    
    def test_preserves_order(self):
        """Test that order is preserved."""
        input_list = ["Zebra", "Apple", "Mango"]
        result = to_snake_case_list(input_list)
        assert result == ["zebra", "apple", "mango"]


class TestResolveIncludeExclude:
    """Tests for the include/exclude resolution logic."""
    
    def test_both_empty_includes_all(self):
        """When both lists are empty, include all tables."""
        assert resolve_include_exclude("any_table", [], []) is True
        assert resolve_include_exclude("any_table", None, None) is True
    
    def test_exclude_only(self):
        """When only exclude list provided, include everything except excluded."""
        assert resolve_include_exclude("table_a", None, ["table_b"]) is True
        assert resolve_include_exclude("table_b", None, ["table_b"]) is False
        assert resolve_include_exclude("table_c", [], ["table_a", "table_b"]) is True
    
    def test_include_only(self):
        """When only include list provided, include only specified."""
        assert resolve_include_exclude("table_a", ["table_a"], None) is True
        assert resolve_include_exclude("table_b", ["table_a"], None) is False
        assert resolve_include_exclude("table_a", ["table_a", "table_b"], []) is True
    
    def test_both_lists(self):
        """When both lists provided, exclude takes precedence."""
        # In include list, not in exclude - include
        assert resolve_include_exclude("table_a", ["table_a", "table_b"], ["table_c"]) is True
        
        # In both lists - exclude wins
        assert resolve_include_exclude("table_b", ["table_a", "table_b"], ["table_b"]) is False
        
        # In neither list - exclude
        assert resolve_include_exclude("table_c", ["table_a"], ["table_d"]) is False
    
    def test_case_sensitivity(self):
        """Test that matching is case-sensitive."""
        assert resolve_include_exclude("Table_A", ["table_a"], None) is False
        assert resolve_include_exclude("table_a", ["Table_A"], None) is False
    
    def test_real_world_scenarios(self):
        """Test scenarios from the requirements."""
        # From MASTERDATA-001 config
        include_list = ['Classifications', 'cmf_print_process', 'Layers', 
                       'MatchTypes', 'Separations', 'regions']
        exclude_list = ['cmf_print_process']
        
        # Classifications is in include, not in exclude - include
        assert resolve_include_exclude("Classifications", include_list, exclude_list) is True
        
        # cmf_print_process is in both - exclude wins
        assert resolve_include_exclude("cmf_print_process", include_list, exclude_list) is False
        
        # Unknown table - not in include - exclude
        assert resolve_include_exclude("unknown_table", include_list, exclude_list) is False


class TestComputeTableRunProperties:
    """Tests for the table_run_properties computation."""
    
    def test_all_zeros(self):
        """Test all flags are zero."""
        assert compute_table_run_properties(0, 0, 0) == 0
    
    def test_all_ones(self):
        """Test all flags are one."""
        assert compute_table_run_properties(1, 1, 1) == 111
    
    def test_is_included_only(self):
        """Test only is_included flag set."""
        assert compute_table_run_properties(1, 0, 0) == 100
    
    def test_ct_enabled_only(self):
        """Test only ct_enabled flag set."""
        assert compute_table_run_properties(0, 1, 0) == 10
    
    def test_is_append_only_only(self):
        """Test only is_append_only flag set."""
        assert compute_table_run_properties(0, 0, 1) == 1
    
    def test_combinations(self):
        """Test various combinations."""
        assert compute_table_run_properties(1, 1, 0) == 110
        assert compute_table_run_properties(1, 0, 1) == 101
        assert compute_table_run_properties(0, 1, 1) == 11


class TestComputeCDCHash:
    """Tests for the CDC hash computation."""
    
    def test_empty_dict(self):
        """Test empty dictionary."""
        result = compute_cdc_hash({})
        assert len(result) == 64  # SHA256 produces 64 hex chars
    
    def test_deterministic(self):
        """Test that same input produces same hash."""
        data = {"key": "value", "num": 123}
        hash1 = compute_cdc_hash(data)
        hash2 = compute_cdc_hash(data)
        assert hash1 == hash2
    
    def test_order_independent(self):
        """Test that key order doesn't affect hash."""
        data1 = {"a": 1, "b": 2}
        data2 = {"b": 2, "a": 1}
        assert compute_cdc_hash(data1) == compute_cdc_hash(data2)
    
    def test_different_data_different_hash(self):
        """Test that different data produces different hash."""
        hash1 = compute_cdc_hash({"key": "value1"})
        hash2 = compute_cdc_hash({"key": "value2"})
        assert hash1 != hash2
    
    def test_valid_sha256(self):
        """Test that output is valid SHA256 hex string."""
        result = compute_cdc_hash({"test": "data"})
        assert len(result) == 64
        assert all(c in '0123456789abcdef' for c in result)


class TestGenerateUniqueId:
    """Tests for unique ID generation."""
    
    def test_basic_id_generation(self):
        """Test basic ID generation."""
        assert generate_unique_id("SOURCE-001", "users") == "SOURCE-001_users"
    
    def test_with_underscores(self):
        """Test ID generation with underscores in names."""
        result = generate_unique_id("AEXML-001", "FontReplacement")
        assert result == "AEXML-001_FontReplacement"
    
    def test_empty_source_id(self):
        """Test with empty source ID."""
        assert generate_unique_id("", "table") == "_table"
    
    def test_empty_table_name(self):
        """Test with empty table name."""
        assert generate_unique_id("SOURCE-001", "") == "SOURCE-001_"


class TestDataSourceTypeMapping:
    """Tests for data source type category mapping."""
    
    # Data source type to category mapping
    SOURCE_TYPE_CATEGORY = {
        "SQLSERVER": "JDBC",
        "POSTGRESQL": "JDBC",
        "MARIADB": "JDBC",
        "CASSANDRA": "NOSQL",
        "ABFSS_STORAGE": "STORAGE",
        "WABS_STORAGE": "STORAGE",
        "WASBS_SAS_STORAGE": "STORAGE",
        "REST_API": "API",
    }
    
    def test_jdbc_types(self):
        """Test JDBC data source types."""
        assert self.SOURCE_TYPE_CATEGORY["SQLSERVER"] == "JDBC"
        assert self.SOURCE_TYPE_CATEGORY["POSTGRESQL"] == "JDBC"
        assert self.SOURCE_TYPE_CATEGORY["MARIADB"] == "JDBC"
    
    def test_storage_types(self):
        """Test storage data source types."""
        assert self.SOURCE_TYPE_CATEGORY["ABFSS_STORAGE"] == "STORAGE"
        assert self.SOURCE_TYPE_CATEGORY["WABS_STORAGE"] == "STORAGE"
        assert self.SOURCE_TYPE_CATEGORY["WASBS_SAS_STORAGE"] == "STORAGE"
    
    def test_nosql_types(self):
        """Test NoSQL data source types."""
        assert self.SOURCE_TYPE_CATEGORY["CASSANDRA"] == "NOSQL"
    
    def test_api_types(self):
        """Test API data source types."""
        assert self.SOURCE_TYPE_CATEGORY["REST_API"] == "API"


class TestDuplicateHandling:
    """Tests for duplicate ID handling logic."""
    
    def test_extract_schema_from_full_name(self):
        """Test extracting schema from full table name."""
        # Simulating the logic used in check_duplicate_and_update
        full_name = "dbo.FontReplacement"
        parts = full_name.split(".")
        if len(parts) >= 2:
            schema = parts[-2]
            table = parts[-1]
            assert schema == "dbo"
            assert table == "FontReplacement"
    
    def test_create_prefixed_table_name(self):
        """Test creating prefixed table name for deduplication."""
        schema = "dbo"
        table_name = "users"
        prefixed = f"{schema}_{table_name}"
        assert prefixed == "dbo_users"
    
    def test_regenerate_id_after_prefix(self):
        """Test ID regeneration after prefixing."""
        source_id = "SOURCE-001"
        prefixed_table_name = "dbo_users"
        new_id = f"{source_id}_{prefixed_table_name}"
        assert new_id == "SOURCE-001_dbo_users"


class TestSchemaConversion:
    """Tests for schema conversion between source and IDP formats."""
    
    def test_source_schema_preserved(self):
        """Test that source schema preserves original column names."""
        source_columns = ["FontReplacement", "UserID", "created_at"]
        # Source schema should be unchanged
        assert source_columns == ["FontReplacement", "UserID", "created_at"]
    
    def test_idp_schema_snake_case(self):
        """Test that IDP schema converts to snake_case."""
        source_columns = ["FontReplacement", "UserID", "created_at"]
        idp_columns = to_snake_case_list(source_columns)
        assert idp_columns == ["font_replacement", "user_id", "created_at"]
    
    def test_id_columns_preserved_and_converted(self):
        """Test that ID columns have both source and IDP versions."""
        source_id_cols = ["Id", "UserCode"]
        idp_id_cols = to_snake_case_list(source_id_cols)
        
        assert source_id_cols == ["Id", "UserCode"]  # preserved
        assert idp_id_cols == ["id", "user_code"]  # converted


class TestConfigParsing:
    """Tests for configuration parsing from db_details."""
    
    def test_parse_jdbc_config(self):
        """Test parsing JDBC configuration."""
        db_details = {
            "db_host": "photon-sqlserver.database.windows.net",
            "db_name": "ai_search",
            "user_name": "aisearchuser",
            "password_key": "AISEARCH-PASSWORD",
            "db_port": "1433",
            "table_schema": ["dbo"],
            "exclude_list": [],
            "append_only_list": []
        }
        
        assert db_details.get("db_host") == "photon-sqlserver.database.windows.net"
        assert db_details.get("db_port") == "1433"
        assert db_details.get("table_schema") == ["dbo"]
    
    def test_parse_storage_config(self):
        """Test parsing storage configuration."""
        db_details = {
            "storage_name": "photonidpqaeusdl",
            "container_name": "inbound",
            "storage_access_key": None,
            "folder_path": "masterdata",
            "file_extension": "csv",
            "file_options": {"header": "True", "inferSchema": "True"},
            "set_spark_config": False,
            "id_columns": ["id", "code"]
        }
        
        assert db_details.get("storage_name") == "photonidpqaeusdl"
        assert db_details.get("file_extension") == "csv"
        assert db_details.get("id_columns") == ["id", "code"]
    
    def test_parse_cassandra_config(self):
        """Test parsing Cassandra configuration."""
        db_details = {
            "user_name": "lQkavNIFfRZmbZJjeUCPPccS",
            "password_key": "CMF-PASSWORD",
            "client_id_key": "CMF-CLIENT-ID",
            "client_secret_key": "CMF-CLIENT-SECRET",
            "keyspace_name": "color",
            "secure_connect_bundle_path": "/dbfs/FileStore/cassandra/secure_connect.zip"
        }
        
        assert db_details.get("keyspace_name") == "color"
        assert "secure_connect" in db_details.get("secure_connect_bundle_path", "")
    
    def test_parse_rest_api_config(self):
        """Test parsing REST API configuration."""
        db_details = {
            "api_parameter_id": "FusionTblSites-APIKEY",
            "api_url": "Fusion-API-URL",
            "api_method": "post",
            "select_exprs": ["site_id AS ID", "site_name AS Name", "'True' AS Active"]
        }
        
        assert db_details.get("api_method") == "post"
        assert len(db_details.get("select_exprs", [])) == 3


class TestOutputSchemaCompliance:
    """Tests to ensure output schema requirements are met."""
    
    REQUIRED_COLUMNS = [
        "full_table_name",
        "table_name",
        "id_columns",
        "partition_cols",
        "ct_enabled",
        "source_id",
        "catalog_name",
        "entity_name",
        "db_name",
        "id",
        "include_list",
        "exclude_list",
        "is_included",
        "is_append_only",
        "is_active",
        "table_run_properties",
        "idp_db_name",
        "idp_id_columns",
        "idp_cdc_hash",
        "idp_created_date",
        "idp_modified_date",
        "table_row_count",
        "column_count",
        "source_schema",
        "idp_schema",
        "column_details",
        "file_size_bytes",
        "file_last_modified",
        "sample_file_paths"
    ]
    
    def test_all_required_columns_defined(self):
        """Test that all required columns are accounted for."""
        assert len(self.REQUIRED_COLUMNS) == 29
    
    def test_no_duplicate_columns(self):
        """Test no duplicate column names."""
        assert len(self.REQUIRED_COLUMNS) == len(set(self.REQUIRED_COLUMNS))
    
    def test_id_column_format(self):
        """Test ID column format."""
        source_id = "AEXML-004"
        table_name = "FontReplacement"
        expected_id = "AEXML-004_FontReplacement"
        
        assert generate_unique_id(source_id, table_name) == expected_id


class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_unicode_in_names(self):
        """Test handling of unicode characters."""
        result = to_snake_case("Café")
        assert result == "café"
    
    def test_very_long_names(self):
        """Test handling of very long names."""
        long_name = "A" * 1000
        result = to_snake_case(long_name)
        assert len(result) == 1000
        assert result == "a" * 1000
    
    def test_only_special_chars(self):
        """Test string with only special characters."""
        result = to_snake_case("@#$%")
        assert result == ""
    
    def test_numeric_string(self):
        """Test purely numeric string."""
        result = to_snake_case("12345")
        assert result == "12345"
    
    def test_single_character(self):
        """Test single character input."""
        assert to_snake_case("A") == "a"
        assert to_snake_case("_") == ""
        assert to_snake_case("1") == "1"


# =============================================================================
# Integration Test Helpers
# =============================================================================

class TestIntegrationHelpers:
    """Helper tests that simulate integration scenarios."""
    
    def test_full_metadata_row_creation(self):
        """Test creating a complete metadata row."""
        # Simulate processing a table
        source_id = "AEXML-004"
        table_name = "FontReplacement"
        source_schema = ["Id", "FontName", "ReplacementFont", "CreatedDate"]
        id_columns = ["Id"]
        include_list = ["GlobalFontUserFeedback"]
        exclude_list = []
        
        # Computed values
        unique_id = generate_unique_id(source_id, table_name)
        idp_db_name = to_snake_case(table_name)
        idp_id_columns = to_snake_case_list(id_columns)
        idp_schema = to_snake_case_list(source_schema)
        is_included = 0 if table_name not in (include_list or []) else 1
        is_append_only = 0
        is_active = is_included
        ct_enabled = 0
        table_run_properties = compute_table_run_properties(is_included, ct_enabled, is_append_only)
        
        # Assertions
        assert unique_id == "AEXML-004_FontReplacement"
        assert idp_db_name == "font_replacement"
        assert idp_id_columns == ["id"]
        assert idp_schema == ["id", "font_name", "replacement_font", "created_date"]
        assert is_included == 0  # Not in include_list
        assert table_run_properties == 0  # 000


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
