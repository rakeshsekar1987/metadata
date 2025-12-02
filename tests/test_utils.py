"""
Unit tests for utility functions in the IDP Metadata Collector Framework.
"""

import pytest
from pyspark.sql import functions as F
from pyspark.sql.types import StringType, ArrayType

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from idp_metadata_collector_framework import (
    to_snake_case_expr,
    to_snake_case_array_expr,
    is_dataframe_empty,
    safe_get,
    compute_schema_hash,
)


class TestToSnakeCaseExpr:
    """Tests for to_snake_case_expr function"""
    
    def test_camel_case_conversion(self, spark):
        """Test converting camelCase to snake_case"""
        df = spark.createDataFrame([("camelCase",), ("PascalCase",), ("myVariableName",)], ["name"])
        result = df.withColumn("snake", to_snake_case_expr(F.col("name")))
        
        rows = result.collect()
        assert rows[0]["snake"] == "camel_case"
        assert rows[1]["snake"] == "pascal_case"
        assert rows[2]["snake"] == "my_variable_name"
    
    def test_already_snake_case(self, spark):
        """Test that already snake_case strings are unchanged"""
        df = spark.createDataFrame([("already_snake",), ("another_one",)], ["name"])
        result = df.withColumn("snake", to_snake_case_expr(F.col("name")))
        
        rows = result.collect()
        assert rows[0]["snake"] == "already_snake"
        assert rows[1]["snake"] == "another_one"
    
    def test_all_caps(self, spark):
        """Test ALL_CAPS conversion"""
        df = spark.createDataFrame([("ALLCAPS",), ("XMLParser",), ("HTTPClient",)], ["name"])
        result = df.withColumn("snake", to_snake_case_expr(F.col("name")))
        
        rows = result.collect()
        # ALL_CAPS becomes allcaps (no underscores added between consecutive caps)
        assert rows[0]["snake"] == "allcaps"
        # XMLParser -> xml_parser (consecutive caps followed by lower handled well)
        assert rows[1]["snake"] == "xml_parser"
        # HTTPClient -> http_client
        assert rows[2]["snake"] == "http_client"
    
    def test_single_word(self, spark):
        """Test single word strings"""
        df = spark.createDataFrame([("Table",), ("column",)], ["name"])
        result = df.withColumn("snake", to_snake_case_expr(F.col("name")))
        
        rows = result.collect()
        assert rows[0]["snake"] == "table"
        assert rows[1]["snake"] == "column"
    
    def test_empty_string(self, spark):
        """Test empty string handling"""
        df = spark.createDataFrame([("",)], ["name"])
        result = df.withColumn("snake", to_snake_case_expr(F.col("name")))
        
        rows = result.collect()
        assert rows[0]["snake"] == ""
    
    def test_null_handling(self, spark):
        """Test null value handling"""
        from pyspark.sql.types import StructType, StructField, StringType
        
        schema = StructType([StructField("name", StringType(), True)])
        df = spark.createDataFrame([(None,)], schema)
        result = df.withColumn("snake", to_snake_case_expr(F.col("name")))
        
        rows = result.collect()
        assert rows[0]["snake"] is None


class TestToSnakeCaseArrayExpr:
    """Tests for to_snake_case_array_expr function"""
    
    def test_array_conversion(self, spark):
        """Test converting array of strings to snake_case"""
        df = spark.createDataFrame(
            [(["camelCase", "PascalCase", "myVar"],)],
            ["names"]
        )
        result = df.withColumn("snake_names", to_snake_case_array_expr(F.col("names")))
        
        row = result.first()
        assert row["snake_names"] == ["camel_case", "pascal_case", "my_var"]
    
    def test_empty_array(self, spark):
        """Test empty array handling"""
        from pyspark.sql.types import StructType, StructField, ArrayType, StringType
        
        schema = StructType([StructField("names", ArrayType(StringType()), True)])
        df = spark.createDataFrame([([],)], schema)
        result = df.withColumn("snake_names", to_snake_case_array_expr(F.col("names")))
        
        row = result.first()
        assert row["snake_names"] == []
    
    def test_null_array(self, spark):
        """Test null array handling"""
        from pyspark.sql.types import StructType, StructField, ArrayType, StringType
        
        schema = StructType([StructField("names", ArrayType(StringType()), True)])
        df = spark.createDataFrame([(None,)], schema)
        result = df.withColumn("snake_names", to_snake_case_array_expr(F.col("names")))
        
        row = result.first()
        assert row["snake_names"] is None


class TestIsDataFrameEmpty:
    """Tests for is_dataframe_empty function"""
    
    def test_empty_dataframe(self, spark):
        """Test that empty DataFrame returns True"""
        df = spark.createDataFrame([], "name: string")
        assert is_dataframe_empty(df) is True
    
    def test_non_empty_dataframe(self, spark):
        """Test that non-empty DataFrame returns False"""
        df = spark.createDataFrame([("test",)], ["name"])
        assert is_dataframe_empty(df) is False
    
    def test_single_row_dataframe(self, spark):
        """Test DataFrame with single row returns False"""
        df = spark.createDataFrame([("single",)], ["name"])
        assert is_dataframe_empty(df) is False
    
    def test_large_dataframe(self, spark):
        """Test that large DataFrame check is efficient"""
        import time
        
        # Create a DataFrame with many rows
        data = [(f"row_{i}",) for i in range(10000)]
        df = spark.createDataFrame(data, ["name"])
        
        start = time.time()
        result = is_dataframe_empty(df)
        elapsed = time.time() - start
        
        assert result is False
        # Should complete in under 1 second (head(1) is O(1))
        assert elapsed < 1.0


class TestSafeGet:
    """Tests for safe_get function"""
    
    def test_existing_key(self):
        """Test getting existing key"""
        d = {"key1": "value1", "key2": 42}
        assert safe_get(d, "key1") == "value1"
        assert safe_get(d, "key2") == 42
    
    def test_missing_key_with_default(self):
        """Test getting missing key with default"""
        d = {"key1": "value1"}
        assert safe_get(d, "missing", "default") == "default"
        assert safe_get(d, "missing", 0) == 0
    
    def test_missing_key_without_default(self):
        """Test getting missing key without default returns None"""
        d = {"key1": "value1"}
        assert safe_get(d, "missing") is None
    
    def test_none_dict(self):
        """Test with None dictionary"""
        assert safe_get(None, "key") is None
        assert safe_get(None, "key", "default") == "default"
    
    def test_nested_values(self):
        """Test getting nested dictionary value"""
        d = {"nested": {"inner": "value"}}
        result = safe_get(d, "nested")
        assert result == {"inner": "value"}


class TestComputeSchemaHash:
    """Tests for compute_schema_hash function"""
    
    def test_same_inputs_same_hash(self):
        """Test that same inputs produce same hash"""
        schema = '{"type":"struct","fields":[]}'
        count = 100
        
        hash1 = compute_schema_hash(schema, count)
        hash2 = compute_schema_hash(schema, count)
        
        assert hash1 == hash2
    
    def test_different_schema_different_hash(self):
        """Test that different schemas produce different hashes"""
        schema1 = '{"type":"struct","fields":[{"name":"col1"}]}'
        schema2 = '{"type":"struct","fields":[{"name":"col2"}]}'
        
        hash1 = compute_schema_hash(schema1, 100)
        hash2 = compute_schema_hash(schema2, 100)
        
        assert hash1 != hash2
    
    def test_different_count_different_hash(self):
        """Test that different counts produce different hashes"""
        schema = '{"type":"struct","fields":[]}'
        
        hash1 = compute_schema_hash(schema, 100)
        hash2 = compute_schema_hash(schema, 200)
        
        assert hash1 != hash2
    
    def test_hash_length(self):
        """Test that hash is exactly 32 characters"""
        schema = '{"type":"struct","fields":[]}'
        hash_value = compute_schema_hash(schema, 100)
        
        assert len(hash_value) == 32
    
    def test_hash_is_hexadecimal(self):
        """Test that hash contains only hex characters"""
        schema = '{"type":"struct","fields":[]}'
        hash_value = compute_schema_hash(schema, 100)
        
        # All characters should be valid hex
        assert all(c in '0123456789abcdef' for c in hash_value)
