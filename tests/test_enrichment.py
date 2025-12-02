"""
Unit tests for metadata enrichment in the IDP Metadata Collector Framework.
"""

import pytest
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, ArrayType

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from idp_metadata_collector_framework import (
    MetadataEnrichmentBuilder,
    DuplicateHandler,
)


class TestMetadataEnrichmentBuilder:
    """Tests for MetadataEnrichmentBuilder"""
    
    @pytest.fixture
    def base_df(self, spark):
        """Create base DataFrame for enrichment tests"""
        schema = StructType([
            StructField("full_table_name", StringType(), False),
            StructField("table_name", StringType(), False),
            StructField("id_columns", ArrayType(StringType()), True),
            StructField("source_schema", ArrayType(StringType()), True),
            StructField("ct_enabled", IntegerType(), True),
            StructField("source_id", StringType(), True),
        ])
        
        data = [
            ("dbo.CustomerOrders", "CustomerOrders", ["id"], ["id", "customerName", "orderDate"], 1, "source_1"),
            ("sales.ProductCatalog", "ProductCatalog", ["productId"], ["productId", "productName"], 0, "source_1"),
        ]
        
        return spark.createDataFrame(data, schema)
    
    def test_add_snake_case_columns(self, base_df):
        """Test snake_case conversion"""
        builder = MetadataEnrichmentBuilder(base_df)
        result = builder.add_snake_case_columns().build()
        
        # Check columns exist
        assert "idp_db_name" in result.columns
        assert "idp_id_columns" in result.columns
        assert "idp_schema" in result.columns
        
        # Check conversion
        row = result.filter(F.col("table_name") == "CustomerOrders").first()
        assert row["idp_db_name"] == "customer_orders"
    
    def test_add_inclusion_logic_empty_lists(self, base_df):
        """Test inclusion logic with empty include/exclude lists"""
        builder = MetadataEnrichmentBuilder(base_df)
        result = builder.add_inclusion_logic([], []).build()
        
        # All should be included when both lists empty
        rows = result.collect()
        for row in rows:
            assert row["is_included"] == 1
    
    def test_add_inclusion_logic_include_list(self, base_df):
        """Test inclusion logic with include list"""
        builder = MetadataEnrichmentBuilder(base_df)
        result = builder.add_inclusion_logic(["CustomerOrders"], []).build()
        
        customer_row = result.filter(F.col("table_name") == "CustomerOrders").first()
        product_row = result.filter(F.col("table_name") == "ProductCatalog").first()
        
        assert customer_row["is_included"] == 1
        assert product_row["is_included"] == 0
    
    def test_add_inclusion_logic_exclude_list(self, base_df):
        """Test inclusion logic with exclude list"""
        builder = MetadataEnrichmentBuilder(base_df)
        result = builder.add_inclusion_logic([], ["CustomerOrders"]).build()
        
        customer_row = result.filter(F.col("table_name") == "CustomerOrders").first()
        product_row = result.filter(F.col("table_name") == "ProductCatalog").first()
        
        assert customer_row["is_included"] == 0
        assert product_row["is_included"] == 1
    
    def test_add_inclusion_logic_both_lists(self, base_df):
        """Test inclusion logic with both include and exclude lists"""
        builder = MetadataEnrichmentBuilder(base_df)
        result = builder.add_inclusion_logic(
            ["CustomerOrders", "ProductCatalog"],
            ["ProductCatalog"]
        ).build()
        
        customer_row = result.filter(F.col("table_name") == "CustomerOrders").first()
        product_row = result.filter(F.col("table_name") == "ProductCatalog").first()
        
        # CustomerOrders in include, not in exclude -> included
        assert customer_row["is_included"] == 1
        # ProductCatalog in both -> excluded wins
        assert product_row["is_included"] == 0
    
    def test_add_append_only_logic(self, base_df):
        """Test append-only logic"""
        builder = MetadataEnrichmentBuilder(base_df)
        result = builder.add_append_only_logic(["CustomerOrders"]).build()
        
        customer_row = result.filter(F.col("table_name") == "CustomerOrders").first()
        product_row = result.filter(F.col("table_name") == "ProductCatalog").first()
        
        assert customer_row["is_append_only"] == 1
        assert product_row["is_append_only"] == 0
    
    def test_add_append_only_logic_empty(self, base_df):
        """Test append-only logic with empty list"""
        builder = MetadataEnrichmentBuilder(base_df)
        result = builder.add_append_only_logic([]).build()
        
        rows = result.collect()
        for row in rows:
            assert row["is_append_only"] == 0
    
    def test_add_run_properties(self, base_df):
        """Test run properties bitmap calculation"""
        # First add required columns
        df = base_df.withColumn("is_included", F.lit(1))
        df = df.withColumn("is_append_only", F.lit(0))
        
        builder = MetadataEnrichmentBuilder(df)
        result = builder.add_run_properties().build()
        
        # is_included=1, ct_enabled=1, is_append_only=0 -> 1*4 + 1*2 + 0 = 6
        row1 = result.filter(F.col("table_name") == "CustomerOrders").first()
        assert row1["table_run_properties"] == 6
        
        # is_included=1, ct_enabled=0, is_append_only=0 -> 1*4 + 0*2 + 0 = 4
        row2 = result.filter(F.col("table_name") == "ProductCatalog").first()
        assert row2["table_run_properties"] == 4
    
    def test_add_unique_id(self, base_df):
        """Test unique ID generation"""
        builder = MetadataEnrichmentBuilder(base_df)
        result = builder.add_unique_id().build()
        
        assert "id" in result.columns
        
        row = result.filter(F.col("table_name") == "CustomerOrders").first()
        assert row["id"] == "source_1_CustomerOrders"
    
    def test_full_enrichment_pipeline(self, base_df):
        """Test full enrichment pipeline"""
        builder = MetadataEnrichmentBuilder(base_df)
        result = (
            builder
            .add_snake_case_columns()
            .add_inclusion_logic([], [])
            .add_append_only_logic([])
            .add_run_properties()
            .add_unique_id()
            .build()
        )
        
        # Check all columns exist
        expected_columns = [
            "idp_db_name", "idp_id_columns", "idp_schema",
            "include_list", "exclude_list", "is_included",
            "is_append_only", "table_run_properties", "id"
        ]
        
        for col in expected_columns:
            assert col in result.columns
    
    def test_builder_immutability(self, base_df):
        """Test that builder operations don't modify original DataFrame"""
        original_columns = base_df.columns.copy()
        
        builder = MetadataEnrichmentBuilder(base_df)
        builder.add_snake_case_columns()
        
        # Original DataFrame columns should be unchanged
        # Note: The builder modifies its internal _df, but the original reference is preserved
        assert base_df.columns == original_columns


class TestDuplicateHandler:
    """Tests for DuplicateHandler"""
    
    @pytest.fixture
    def handler(self, mock_logger):
        """Create duplicate handler for testing"""
        return DuplicateHandler(mock_logger)
    
    def test_no_duplicates(self, handler, spark):
        """Test handling DataFrame with no duplicates"""
        schema = StructType([
            StructField("id", StringType(), False),
            StructField("table_name", StringType(), False),
            StructField("full_table_name", StringType(), False),
            StructField("source_id", StringType(), False),
        ])
        
        data = [
            ("source1_table1", "table1", "dbo.table1", "source1"),
            ("source1_table2", "table2", "dbo.table2", "source1"),
            ("source2_table3", "table3", "sales.table3", "source2"),
        ]
        
        df = spark.createDataFrame(data, schema)
        result = handler.resolve_duplicates(df)
        
        assert result.count() == 3
    
    def test_with_duplicates(self, handler, spark):
        """Test handling DataFrame with duplicate IDs"""
        schema = StructType([
            StructField("id", StringType(), False),
            StructField("table_name", StringType(), False),
            StructField("full_table_name", StringType(), False),
            StructField("source_id", StringType(), False),
        ])
        
        data = [
            ("source1_table1", "table1", "dbo.table1", "source1"),
            ("source1_table1", "table1", "sales.table1", "source1"),  # Duplicate ID
            ("source1_table2", "table2", "dbo.table2", "source1"),
        ]
        
        df = spark.createDataFrame(data, schema)
        result = handler.resolve_duplicates(df)
        
        # Should resolve duplicates by adding schema prefix
        ids = [row["id"] for row in result.select("id").distinct().collect()]
        assert len(ids) == 3  # All unique now
    
    def test_empty_dataframe(self, handler, spark):
        """Test handling empty DataFrame"""
        schema = StructType([
            StructField("id", StringType(), False),
            StructField("table_name", StringType(), False),
            StructField("full_table_name", StringType(), False),
            StructField("source_id", StringType(), False),
        ])
        
        df = spark.createDataFrame([], schema)
        result = handler.resolve_duplicates(df)
        
        assert result.count() == 0
    
    def test_multiple_duplicates(self, handler, spark):
        """Test handling multiple duplicate groups"""
        schema = StructType([
            StructField("id", StringType(), False),
            StructField("table_name", StringType(), False),
            StructField("full_table_name", StringType(), False),
            StructField("source_id", StringType(), False),
        ])
        
        data = [
            ("source1_users", "users", "dbo.users", "source1"),
            ("source1_users", "users", "auth.users", "source1"),  # Duplicate
            ("source1_orders", "orders", "sales.orders", "source1"),
            ("source1_orders", "orders", "archive.orders", "source1"),  # Duplicate
            ("source1_products", "products", "catalog.products", "source1"),  # No duplicate
        ]
        
        df = spark.createDataFrame(data, schema)
        result = handler.resolve_duplicates(df)
        
        ids = [row["id"] for row in result.select("id").distinct().collect()]
        assert len(ids) == 5  # All unique now


class TestEnrichmentIntegration:
    """Integration tests for enrichment pipeline"""
    
    def test_enrichment_with_metadata_collection(self, spark, sample_metadata_df):
        """Test enrichment applied to collected metadata"""
        # Add source_id for enrichment
        df = sample_metadata_df.withColumn("source_id", F.lit("test_source"))
        
        builder = MetadataEnrichmentBuilder(df)
        result = (
            builder
            .add_snake_case_columns()
            .add_inclusion_logic(["customers", "orders"], ["orders"])
            .add_append_only_logic(["products"])
            .add_run_properties()
            .add_unique_id()
            .build()
        )
        
        # Verify customers (included)
        customers = result.filter(F.col("table_name") == "customers").first()
        assert customers["is_included"] == 1
        assert customers["idp_db_name"] == "customers"
        
        # Verify orders (excluded)
        orders = result.filter(F.col("table_name") == "orders").first()
        assert orders["is_included"] == 0
        
        # Verify products (append-only)
        products = result.filter(F.col("table_name") == "products").first()
        assert products["is_append_only"] == 1
