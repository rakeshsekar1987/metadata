"""
Unit tests for MetadataCollectionOrchestrator in the IDP Metadata Collector Framework.
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
import time
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, ArrayType

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from idp_metadata_collector_framework import (
    MetadataCollectionOrchestrator,
    CollectorConfig,
    SQLConnectionDetails,
    StorageConnectionDetails,
    CollectionResult,
    DataSourceType,
    is_dataframe_empty,
    parse_connections,
)


class TestMetadataCollectionOrchestrator:
    """Tests for MetadataCollectionOrchestrator"""
    
    @pytest.fixture
    def mock_df_reader(self, spark):
        """Create mock DataFrame reader"""
        reader = MagicMock()
        reader.read_table.return_value = spark.createDataFrame([], "col: string")
        reader.table_exists.return_value = True
        return reader
    
    @pytest.fixture
    def mock_df_writer(self):
        """Create mock DataFrame writer"""
        writer = MagicMock()
        writer.write_table.return_value = None
        writer.merge_table.return_value = None
        return writer
    
    @pytest.fixture
    def orchestrator(
        self, spark, mock_secret_provider, mock_df_reader, mock_df_writer,
        mock_dbutils, mock_http_client, default_config
    ):
        """Create orchestrator for testing"""
        return MetadataCollectionOrchestrator(
            spark=spark,
            secret_provider=mock_secret_provider,
            df_reader=mock_df_reader,
            df_writer=mock_df_writer,
            dbutils=mock_dbutils,
            http_client=mock_http_client,
            config=default_config
        )
    
    def test_orchestrator_creation(self, orchestrator):
        """Test orchestrator is created correctly"""
        assert orchestrator is not None
        assert orchestrator.results == []
        assert orchestrator.collector_factory is not None
        assert orchestrator.duplicate_handler is not None
    
    def test_create_empty_metadata_df(self, orchestrator):
        """Test creating empty metadata DataFrame"""
        df = orchestrator._create_empty_metadata_df()
        
        assert df.count() == 0
        
        # Check key columns exist
        expected_columns = [
            "full_table_name", "table_name", "id_columns",
            "source_id", "catalog_name", "is_included",
            "idp_cdc_hash", "idp_created_date"
        ]
        
        for col in expected_columns:
            assert col in df.columns
    
    def test_create_summary_df(self, orchestrator):
        """Test creating summary DataFrame"""
        # Add some results
        orchestrator.results = [
            CollectionResult("source1", "Success", row_count=100, duration_seconds=5.0),
            CollectionResult("source2", "Failure", error_message="Connection failed", duration_seconds=30.0),
        ]
        
        summary = orchestrator._create_summary_df()
        
        assert summary.count() == 2
        
        # Check columns
        assert "source_id" in summary.columns
        assert "status" in summary.columns
        assert "error_message" in summary.columns
        assert "row_count" in summary.columns
        assert "duration_seconds" in summary.columns
    
    def test_combine_dataframes_single(self, orchestrator, sample_metadata_df):
        """Test combining single DataFrame"""
        result = orchestrator._combine_dataframes([sample_metadata_df])
        
        assert result.count() == sample_metadata_df.count()
    
    def test_combine_dataframes_multiple(self, orchestrator, spark):
        """Test combining multiple DataFrames"""
        schema = StructType([
            StructField("id", StringType(), False),
            StructField("name", StringType(), False),
        ])
        
        df1 = spark.createDataFrame([("1", "a"), ("2", "b")], schema)
        df2 = spark.createDataFrame([("3", "c"), ("4", "d")], schema)
        
        result = orchestrator._combine_dataframes([df1, df2])
        
        assert result.count() == 4
    
    def test_combine_dataframes_with_missing_columns(self, orchestrator, spark):
        """Test combining DataFrames with different schemas"""
        df1 = spark.createDataFrame([("1", "a")], ["id", "name"])
        df2 = spark.createDataFrame([("2", "b", 100)], ["id", "name", "count"])
        
        result = orchestrator._combine_dataframes([df1, df2])
        
        assert result.count() == 2
        assert "count" in result.columns
    
    def test_enrich_metadata(self, orchestrator, sample_metadata_df):
        """Test metadata enrichment"""
        # Add required column
        df = sample_metadata_df.withColumn("source_id", F.lit("test_source"))
        df = df.withColumn("source_schema", F.array(F.lit("col1"), F.lit("col2")))
        
        conn = SQLConnectionDetails(
            source_id="test_source",
            catalog_name="TEST_CATALOG",
            table_name=None,
            metadata_enabled=True,
            is_active=True,
            db_details={
                "include_list": [],
                "exclude_list": [],
                "append_only_list": []
            }
        )
        
        result = orchestrator._enrich_metadata(df, conn)
        
        # Check enrichment columns
        assert "idp_db_name" in result.columns
        assert "is_included" in result.columns
        assert "is_active" in result.columns
        assert "id" in result.columns


class TestOrchestratorRetryLogic:
    """Tests for retry logic in orchestrator"""
    
    @pytest.fixture
    def fast_config(self):
        """Create config with fast retry settings for testing"""
        return CollectorConfig(
            MAX_RETRIES=3,
            RETRY_BASE_DELAY=0.01,  # Very short for testing
            RETRY_MAX_DELAY=0.1
        )
    
    def test_retry_on_failure(
        self, spark, mock_secret_provider, mock_dbutils, mock_http_client, fast_config
    ):
        """Test that retries happen on failure"""
        mock_df_reader = MagicMock()
        mock_df_writer = MagicMock()
        
        orchestrator = MetadataCollectionOrchestrator(
            spark=spark,
            secret_provider=mock_secret_provider,
            df_reader=mock_df_reader,
            df_writer=mock_df_writer,
            dbutils=mock_dbutils,
            http_client=mock_http_client,
            config=fast_config
        )
        
        # Create a connection that will fail
        conn = SQLConnectionDetails(
            source_id="failing_source",
            catalog_name="CATALOG",
            table_name=None,
            metadata_enabled=True,
            is_active=True,
            db_details={"data_source_type": "SQLSERVER"},
            db_host="nonexistent",
            db_name="testdb",
            user_name="user",
            password_key="key",
            table_schema=["dbo"]
        )
        
        # This will fail but should retry
        result = orchestrator._process_single_connection(conn)
        
        assert result.status == "Failure"
        assert result.retry_count == fast_config.MAX_RETRIES


class TestParseConnections:
    """Tests for parse_connections function"""
    
    def test_parse_sql_connection(self, config_df):
        """Test parsing SQL connection from config"""
        connections = parse_connections(config_df)
        
        # Should have 2 active connections (source_3 is inactive)
        assert len(connections) == 2
        
        # Find SQL connection
        sql_conn = next((c for c in connections if c.source_id == "source_1"), None)
        assert sql_conn is not None
        assert isinstance(sql_conn, SQLConnectionDetails)
        assert sql_conn.db_host == "localhost"
    
    def test_parse_storage_connection(self, config_df):
        """Test parsing storage connection from config"""
        connections = parse_connections(config_df)
        
        # Find storage connection
        storage_conn = next((c for c in connections if c.source_id == "source_2"), None)
        assert storage_conn is not None
        assert isinstance(storage_conn, StorageConnectionDetails)
        assert storage_conn.storage_name == "mystorageaccount"
    
    def test_parse_filters_inactive(self, config_df):
        """Test that inactive sources are filtered"""
        connections = parse_connections(config_df)
        
        # source_3 is inactive, should not be included
        source_ids = [c.source_id for c in connections]
        assert "source_3" not in source_ids
    
    def test_parse_empty_config(self, spark):
        """Test parsing empty config DataFrame"""
        import json
        
        schema = StructType([
            StructField("id", StringType(), False),
            StructField("catalog_name", StringType(), False),
            StructField("table_name", StringType(), True),
            StructField("metadata_enabled", IntegerType(), True),
            StructField("is_active", IntegerType(), True),
            StructField("db_details", StringType(), False)
        ])
        
        empty_df = spark.createDataFrame([], schema)
        connections = parse_connections(empty_df)
        
        assert len(connections) == 0


class TestWriteResults:
    """Tests for write_results method"""
    
    @pytest.fixture
    def orchestrator(
        self, spark, mock_secret_provider, mock_dbutils, mock_http_client, default_config
    ):
        """Create orchestrator with mock writer"""
        mock_df_reader = MagicMock()
        mock_df_writer = MagicMock()
        
        return MetadataCollectionOrchestrator(
            spark=spark,
            secret_provider=mock_secret_provider,
            df_reader=mock_df_reader,
            df_writer=mock_df_writer,
            dbutils=mock_dbutils,
            http_client=mock_http_client,
            config=default_config
        )
    
    def test_write_full_load(self, orchestrator, sample_metadata_df):
        """Test writing with full load mode"""
        # Add required columns
        df = sample_metadata_df.withColumn("source_id", F.lit("test"))
        df = df.withColumn("id", F.lit("test_id"))
        
        orchestrator.write_results(df, "test_table", full_load=True)
        
        orchestrator.df_writer.write_table.assert_called_once()
        call_args = orchestrator.df_writer.write_table.call_args
        assert call_args[1]["mode"] == "overwrite"
    
    def test_write_incremental(self, orchestrator, sample_metadata_df):
        """Test writing with incremental mode"""
        # Add required columns
        df = sample_metadata_df.withColumn("source_id", F.lit("test"))
        df = df.withColumn("id", F.lit("test_id"))
        
        orchestrator.write_results(df, "test_table", full_load=False)
        
        orchestrator.df_writer.merge_table.assert_called_once()
    
    def test_write_empty_df_skipped(self, orchestrator, spark):
        """Test that empty DataFrame write is skipped"""
        schema = StructType([StructField("col", StringType(), True)])
        empty_df = spark.createDataFrame([], schema)
        
        orchestrator.write_results(empty_df, "test_table", full_load=True)
        
        # Neither write nor merge should be called
        orchestrator.df_writer.write_table.assert_not_called()
        orchestrator.df_writer.merge_table.assert_not_called()


class TestCollectAll:
    """Tests for collect_all method"""
    
    def test_collect_all_empty_connections(
        self, spark, mock_secret_provider, mock_dbutils, mock_http_client, default_config
    ):
        """Test collect_all with no connections"""
        mock_df_reader = MagicMock()
        mock_df_writer = MagicMock()
        
        orchestrator = MetadataCollectionOrchestrator(
            spark=spark,
            secret_provider=mock_secret_provider,
            df_reader=mock_df_reader,
            df_writer=mock_df_writer,
            dbutils=mock_dbutils,
            http_client=mock_http_client,
            config=default_config
        )
        
        metadata_df, summary_df = orchestrator.collect_all([], full_load=True)
        
        assert is_dataframe_empty(metadata_df)
        assert summary_df.count() == 0
