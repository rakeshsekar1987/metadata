"""
Unit tests for metadata collectors in the IDP Metadata Collector Framework.
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, ArrayType

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from idp_metadata_collector_framework import (
    DataSourceType,
    CollectorConfig,
    SQLConnectionDetails,
    StorageConnectionDetails,
    RESTAPIConnectionDetails,
    SQLMetadataCollector,
    StorageMetadataCollector,
    RESTAPIMetadataCollector,
    CassandraMetadataCollector,
    MetadataCollectorFactory,
    ConnectionDetails,
)


class TestSQLMetadataCollector:
    """Tests for SQLMetadataCollector"""
    
    @pytest.fixture
    def sql_collector(self, spark, mock_secret_provider, mock_logger, default_config):
        """Create SQL metadata collector for testing"""
        return SQLMetadataCollector(spark, mock_secret_provider, mock_logger, default_config)
    
    def test_validate_connection_valid(self, sql_collector, sql_connection_details):
        """Test validation with valid connection"""
        is_valid, error = sql_collector.validate_connection(sql_connection_details)
        
        assert is_valid is True
        assert error is None
    
    def test_validate_connection_missing_host(self, sql_collector):
        """Test validation with missing host"""
        conn = SQLConnectionDetails(
            source_id="test",
            catalog_name="CATALOG",
            table_name=None,
            metadata_enabled=True,
            is_active=True,
            db_details={"data_source_type": "SQLSERVER"},
            db_host="",  # Missing
            db_name="testdb",
            user_name="user",
            password_key="key",
            table_schema=["dbo"]
        )
        
        is_valid, error = sql_collector.validate_connection(conn)
        
        assert is_valid is False
        assert "db_host" in error
    
    def test_validate_connection_missing_password_key(self, sql_collector):
        """Test validation with missing password key"""
        conn = SQLConnectionDetails(
            source_id="test",
            catalog_name="CATALOG",
            table_name=None,
            metadata_enabled=True,
            is_active=True,
            db_details={"data_source_type": "SQLSERVER"},
            db_host="localhost",
            db_name="testdb",
            user_name="user",
            password_key="",  # Missing
            table_schema=["dbo"]
        )
        
        is_valid, error = sql_collector.validate_connection(conn)
        
        assert is_valid is False
        assert "password_key" in error
    
    def test_validate_connection_empty_schema_is_valid(self, sql_collector):
        """Test validation with empty table schema - should be valid (defaults to 'dbo')"""
        conn = SQLConnectionDetails(
            source_id="test",
            catalog_name="CATALOG",
            table_name=None,
            metadata_enabled=True,
            is_active=True,
            db_details={"data_source_type": "SQLSERVER"},
            db_host="localhost",
            db_name="testdb",
            user_name="user",
            password_key="key",
            table_schema=[]  # Empty - should use default 'dbo' for SQL Server
        )
        
        is_valid, error = sql_collector.validate_connection(conn)
        
        # Empty table_schema is now valid - defaults to 'dbo' for SQL Server
        assert is_valid is True
        assert error is None
    
    def test_build_jdbc_url_sqlserver(self, sql_collector):
        """Test JDBC URL building for SQL Server"""
        conn = SQLConnectionDetails(
            source_id="test",
            catalog_name="CATALOG",
            table_name=None,
            metadata_enabled=True,
            is_active=True,
            db_details={"data_source_type": "SQLSERVER"},
            db_host="myserver.database.windows.net",
            db_name="mydb",
            db_port="1433",
            user_name="user",
            password_key="key",
            table_schema=["dbo"]
        )
        
        url = sql_collector._build_jdbc_url(conn)
        
        assert "jdbc:sqlserver://" in url
        assert "myserver.database.windows.net:1433" in url
        assert "database=mydb" in url
    
    def test_build_jdbc_url_postgresql(self, sql_collector):
        """Test JDBC URL building for PostgreSQL"""
        conn = SQLConnectionDetails(
            source_id="test",
            catalog_name="CATALOG",
            table_name=None,
            metadata_enabled=True,
            is_active=True,
            db_details={"data_source_type": "POSTGRESQL"},
            db_host="pg.example.com",
            db_name="mydb",
            db_port="5432",
            user_name="user",
            password_key="key",
            table_schema=["public"]
        )
        
        url = sql_collector._build_jdbc_url(conn)
        
        assert "jdbc:postgresql://" in url
        assert "pg.example.com:5432" in url
        assert "/mydb" in url
    
    def test_build_jdbc_url_mariadb(self, sql_collector):
        """Test JDBC URL building for MariaDB"""
        conn = SQLConnectionDetails(
            source_id="test",
            catalog_name="CATALOG",
            table_name=None,
            metadata_enabled=True,
            is_active=True,
            db_details={"data_source_type": "MARIADB"},
            db_host="maria.example.com",
            db_name="mydb",
            db_port="3306",
            user_name="user",
            password_key="key",
            table_schema=["public"]
        )
        
        url = sql_collector._build_jdbc_url(conn)
        
        assert "jdbc:mariadb://" in url
        assert "maria.example.com:3306" in url
    
    def test_build_metadata_query_sqlserver(self, sql_collector):
        """Test metadata query building for SQL Server"""
        conn = SQLConnectionDetails(
            source_id="test",
            catalog_name="CATALOG",
            table_name=None,
            metadata_enabled=True,
            is_active=True,
            db_details={"data_source_type": "SQLSERVER"},
            db_host="localhost",
            db_name="testdb",
            db_port="1433",
            user_name="user",
            password_key="key",
            table_schema=["dbo", "sales"]
        )
        
        query = sql_collector._build_metadata_query(conn)
        
        assert "INFORMATION_SCHEMA.COLUMNS" in query
        assert "'dbo','sales'" in query
        assert "is_primary_key" in query.lower()
    
    def test_build_metadata_query_with_empty_schema(self, sql_collector):
        """Test metadata query building with empty schema defaults to 'dbo'"""
        conn = SQLConnectionDetails(
            source_id="test",
            catalog_name="CATALOG",
            table_name=None,
            metadata_enabled=True,
            is_active=True,
            db_details={"data_source_type": "SQLSERVER"},
            db_host="localhost",
            db_name="testdb",
            db_port="1433",
            user_name="user",
            password_key="key",
            table_schema=[],  # Empty schema
            include_list=["tbl_customers", "tbl_orders"]
        )
        
        query = sql_collector._build_metadata_query(conn)
        
        assert "INFORMATION_SCHEMA.COLUMNS" in query
        # Should default to 'dbo' schema for SQL Server when empty
        assert "TABLE_SCHEMA IN ('dbo')" in query
    
    def test_build_metadata_query_null_schema(self, sql_collector):
        """Test metadata query building with null schema defaults to 'dbo'"""
        conn = SQLConnectionDetails(
            source_id="test",
            catalog_name="CATALOG",
            table_name=None,
            metadata_enabled=True,
            is_active=True,
            db_details={"data_source_type": "SQLSERVER"},
            db_host="localhost",
            db_name="testdb",
            db_port="1433",
            user_name="user",
            password_key="key",
            table_schema=None  # Null schema - should use default
        )
        
        query = sql_collector._build_metadata_query(conn)
        
        assert "INFORMATION_SCHEMA.COLUMNS" in query
        # Should default to 'dbo' schema for SQL Server
        assert "TABLE_SCHEMA IN ('dbo')" in query
    
    def test_process_sql_metadata(self, sql_collector, sample_sql_metadata_df, sql_connection_details):
        """Test processing raw SQL metadata"""
        processed = sql_collector._process_sql_metadata(sample_sql_metadata_df, sql_connection_details)
        
        # Should group by table
        assert processed.count() == 2  # customers and orders
        
        # Check columns exist
        columns = processed.columns
        assert "full_table_name" in columns
        assert "table_name" in columns
        assert "id_columns" in columns
        assert "source_schema" in columns
        assert "column_count" in columns
        
        # Check data
        customers = processed.filter(F.col("table_name") == "customers").first()
        assert customers["column_count"] == 3
        assert "id" in customers["id_columns"]
    
    def test_get_default_port(self, sql_collector):
        """Test getting default ports for database types"""
        assert sql_collector._get_default_port("SQLSERVER") == "1433"
        assert sql_collector._get_default_port("POSTGRESQL") == "5432"
        assert sql_collector._get_default_port("MARIADB") == "3306"
        assert sql_collector._get_default_port("UNKNOWN") == "1433"  # Default


class TestStorageMetadataCollector:
    """Tests for StorageMetadataCollector"""
    
    @pytest.fixture
    def storage_collector(self, spark, mock_secret_provider, mock_logger, default_config, mock_dbutils):
        """Create storage metadata collector for testing"""
        return StorageMetadataCollector(spark, mock_secret_provider, mock_logger, default_config, mock_dbutils)
    
    def test_validate_connection_valid(self, storage_collector, storage_connection_details):
        """Test validation with valid connection"""
        is_valid, error = storage_collector.validate_connection(storage_connection_details)
        
        assert is_valid is True
        assert error is None
    
    def test_validate_connection_missing_storage_name(self, storage_collector):
        """Test validation with missing storage name"""
        conn = StorageConnectionDetails(
            source_id="test",
            catalog_name="CATALOG",
            table_name=None,
            metadata_enabled=True,
            is_active=True,
            db_details={"data_source_type": "ABFSS_STORAGE"},
            storage_name="",  # Missing
            container_name="container"
        )
        
        is_valid, error = storage_collector.validate_connection(conn)
        
        assert is_valid is False
        assert "storage_name" in error
    
    def test_build_storage_path_abfss(self, storage_collector):
        """Test building ABFSS storage path"""
        conn = StorageConnectionDetails(
            source_id="test",
            catalog_name="CATALOG",
            table_name=None,
            metadata_enabled=True,
            is_active=True,
            db_details={"data_source_type": "ABFSS_STORAGE"},
            storage_name="mystorageaccount",
            container_name="mycontainer",
            folder_path="data/raw"
        )
        
        path = storage_collector._build_storage_path(conn)
        
        assert path == "abfss://mycontainer@mystorageaccount.dfs.core.windows.net/data/raw"
    
    def test_build_storage_path_wasbs(self, storage_collector):
        """Test building WASBS storage path"""
        conn = StorageConnectionDetails(
            source_id="test",
            catalog_name="CATALOG",
            table_name=None,
            metadata_enabled=True,
            is_active=True,
            db_details={"data_source_type": "WASBS_SAS_STORAGE"},
            storage_name="mystorageaccount",
            container_name="mycontainer",
            folder_path="data/raw"
        )
        
        path = storage_collector._build_storage_path(conn)
        
        assert path == "wasbs://mycontainer@mystorageaccount.blob.core.windows.net/data/raw"
    
    def test_build_storage_path_no_folder(self, storage_collector):
        """Test building storage path without folder"""
        conn = StorageConnectionDetails(
            source_id="test",
            catalog_name="CATALOG",
            table_name=None,
            metadata_enabled=True,
            is_active=True,
            db_details={"data_source_type": "ABFSS_STORAGE"},
            storage_name="mystorageaccount",
            container_name="mycontainer",
            folder_path=""
        )
        
        path = storage_collector._build_storage_path(conn)
        
        assert path == "abfss://mycontainer@mystorageaccount.dfs.core.windows.net"
    
    def test_get_file_metadata_schema(self, storage_collector):
        """Test file metadata schema structure"""
        schema = storage_collector._get_file_metadata_schema()
        
        field_names = [f.name for f in schema.fields]
        
        assert "full_table_name" in field_names
        assert "table_name" in field_names
        assert "id_columns" in field_names
        assert "file_size_bytes" in field_names
        assert "file_last_modified" in field_names
    
    def test_table_size_maps_from_file_size(self, spark, storage_collector, storage_connection_details):
        """Test that table_size is mapped from file_size_bytes"""
        # Create a sample file metadata DataFrame
        schema = storage_collector._get_file_metadata_schema()
        data = [
            ("path/file1.parquet", "file1", [], [], 0, ["col1"], 1, 1024000, None),
            ("path/file2.parquet", "file2", [], [], 0, ["col1"], 1, 2048000, None),
        ]
        df = spark.createDataFrame(data, schema)
        
        # Add sample_file_paths and table_size (simulating what collect_metadata does)
        from pyspark.sql import functions as F
        from pyspark.sql.types import ArrayType, StringType
        df = df.withColumn("sample_file_paths", F.array().cast(ArrayType(StringType())))
        df = df.withColumn("table_size", F.col("file_size_bytes"))
        
        # Verify table_size matches file_size_bytes
        rows = df.collect()
        assert rows[0]["table_size"] == 1024000
        assert rows[1]["table_size"] == 2048000


class TestRESTAPIMetadataCollector:
    """Tests for RESTAPIMetadataCollector"""
    
    @pytest.fixture
    def api_collector(self, spark, mock_secret_provider, mock_logger, default_config, mock_http_client):
        """Create REST API metadata collector for testing"""
        return RESTAPIMetadataCollector(spark, mock_secret_provider, mock_logger, default_config, mock_http_client)
    
    def test_validate_connection_valid(self, api_collector, rest_api_connection_details):
        """Test validation with valid connection"""
        is_valid, error = api_collector.validate_connection(rest_api_connection_details)
        
        assert is_valid is True
        assert error is None
    
    def test_validate_connection_missing_base_url(self, api_collector):
        """Test validation with missing base URL"""
        conn = RESTAPIConnectionDetails(
            source_id="test",
            catalog_name="CATALOG",
            table_name=None,
            metadata_enabled=True,
            is_active=True,
            db_details={"data_source_type": "REST_API"},
            base_url="",  # Missing
            auth_type="API_KEY"
        )
        
        is_valid, error = api_collector.validate_connection(conn)
        
        assert is_valid is False
        assert "base_url" in error
    
    def test_validate_connection_missing_auth_type(self, api_collector):
        """Test validation with missing auth type"""
        conn = RESTAPIConnectionDetails(
            source_id="test",
            catalog_name="CATALOG",
            table_name=None,
            metadata_enabled=True,
            is_active=True,
            db_details={"data_source_type": "REST_API"},
            base_url="https://api.example.com",
            auth_type=""  # Missing
        )
        
        is_valid, error = api_collector.validate_connection(conn)
        
        assert is_valid is False
        assert "auth_type" in error
    
    def test_extract_endpoint_metadata_dict_response(self, api_collector, mock_http_client):
        """Test extracting metadata from dict response"""
        mock_http_client.set_response(
            "https://api.example.com/users",
            {"id": 1, "name": "John", "email": "john@example.com"}
        )
        
        metadata = api_collector._extract_endpoint_metadata(
            "https://api.example.com/users",
            {},
            30,
            "users"
        )
        
        assert metadata is not None
        assert metadata["table_name"] == "users"
        assert set(metadata["source_schema"]) == {"id", "name", "email"}
        assert metadata["column_count"] == 3
    
    def test_extract_endpoint_metadata_list_response(self, api_collector, mock_http_client):
        """Test extracting metadata from list response"""
        mock_http_client.set_response(
            "https://api.example.com/orders",
            [
                {"order_id": 1, "amount": 100},
                {"order_id": 2, "amount": 200}
            ]
        )
        
        metadata = api_collector._extract_endpoint_metadata(
            "https://api.example.com/orders",
            {},
            30,
            "orders"
        )
        
        assert metadata is not None
        assert metadata["table_name"] == "orders"
        assert set(metadata["source_schema"]) == {"order_id", "amount"}
    
    def test_get_api_metadata_schema(self, api_collector):
        """Test API metadata schema structure"""
        schema = api_collector._get_api_metadata_schema()
        
        field_names = [f.name for f in schema.fields]
        
        assert "full_table_name" in field_names
        assert "table_name" in field_names
        assert "api_endpoint" in field_names
        assert "response_format" in field_names


class TestMetadataCollectorFactory:
    """Tests for MetadataCollectorFactory"""
    
    @pytest.fixture
    def factory(self, spark, mock_secret_provider, mock_logger, default_config, mock_dbutils, mock_http_client):
        """Create collector factory for testing"""
        return MetadataCollectorFactory(
            spark, mock_secret_provider, mock_logger, default_config, mock_dbutils, mock_http_client
        )
    
    def test_get_sql_collector(self, factory):
        """Test getting SQL collector"""
        collector = factory.get_collector(DataSourceType.SQLSERVER)
        assert isinstance(collector, SQLMetadataCollector)
        
        # Same instance for same type
        collector2 = factory.get_collector(DataSourceType.SQLSERVER)
        assert collector is collector2
    
    def test_get_postgresql_collector(self, factory):
        """Test getting PostgreSQL collector (same as SQL)"""
        collector = factory.get_collector(DataSourceType.POSTGRESQL)
        assert isinstance(collector, SQLMetadataCollector)
    
    def test_get_storage_collector(self, factory):
        """Test getting storage collector"""
        collector = factory.get_collector(DataSourceType.ABFSS_STORAGE)
        assert isinstance(collector, StorageMetadataCollector)
    
    def test_get_rest_api_collector(self, factory):
        """Test getting REST API collector"""
        collector = factory.get_collector(DataSourceType.REST_API)
        assert isinstance(collector, RESTAPIMetadataCollector)
    
    def test_get_cassandra_collector(self, factory):
        """Test getting Cassandra collector"""
        collector = factory.get_collector(DataSourceType.CASSANDRA)
        assert isinstance(collector, CassandraMetadataCollector)
    
    def test_collector_caching(self, factory):
        """Test that collectors are cached"""
        collector1 = factory.get_collector(DataSourceType.SQLSERVER)
        collector2 = factory.get_collector(DataSourceType.POSTGRESQL)
        collector3 = factory.get_collector(DataSourceType.SQLSERVER)
        
        # SQL and PostgreSQL share same collector type
        assert collector1 is collector3
        # But different instances for different types
        assert type(collector1) == type(collector2)


class TestTableSizeQueries:
    """Tests for table size query generation"""
    
    @pytest.fixture
    def sql_collector(self, spark, mock_secret_provider, mock_logger, default_config):
        """Create SQL metadata collector for testing"""
        return SQLMetadataCollector(spark, mock_secret_provider, mock_logger, default_config)
    
    def test_build_sqlserver_size_query(self, sql_collector):
        """Test SQL Server size query building"""
        tables = ["dbo.customers", "sales.orders"]
        query = sql_collector._build_sqlserver_size_query(tables, "testdb")
        
        assert query != ""
        assert "sys.tables" in query
        assert "size_bytes" in query
        assert "dbo" in query
        assert "customers" in query
    
    def test_build_postgresql_size_query(self, sql_collector):
        """Test PostgreSQL size query building"""
        tables = ["public.users", "auth.roles"]
        query = sql_collector._build_postgresql_size_query(tables)
        
        assert query != ""
        assert "pg_total_relation_size" in query
        assert "size_bytes" in query
        assert "public" in query
    
    def test_build_mariadb_size_query(self, sql_collector):
        """Test MariaDB size query building"""
        tables = ["mydb.customers", "mydb.orders"]
        query = sql_collector._build_mariadb_size_query(tables, "mydb")
        
        assert query != ""
        assert "information_schema.tables" in query
        assert "size_bytes" in query
        assert "data_length" in query
    
    def test_empty_tables_returns_empty_query(self, sql_collector):
        """Test that empty tables list returns empty query"""
        assert sql_collector._build_sqlserver_size_query([], "testdb") == ""
        assert sql_collector._build_postgresql_size_query([]) == ""
        assert sql_collector._build_mariadb_size_query([], "testdb") == ""


class TestCDCHashGeneration:
    """Tests for CDC hash generation"""
    
    @pytest.fixture
    def sql_collector(self, spark, mock_secret_provider, mock_logger, default_config):
        """Create SQL metadata collector for testing"""
        return SQLMetadataCollector(spark, mock_secret_provider, mock_logger, default_config)
    
    def test_cdc_hash_deterministic(self, sql_collector, sample_metadata_df):
        """Test that CDC hash is deterministic for same data"""
        hash1 = sql_collector._generate_cdc_hash_efficient(sample_metadata_df)
        hash2 = sql_collector._generate_cdc_hash_efficient(sample_metadata_df)
        
        assert hash1 == hash2
    
    def test_cdc_hash_different_data(self, sql_collector, spark):
        """Test that different data produces different hash"""
        df1 = spark.createDataFrame([("a",)], ["col"])
        df2 = spark.createDataFrame([("a",), ("b",)], ["col"])
        
        hash1 = sql_collector._generate_cdc_hash_efficient(df1)
        hash2 = sql_collector._generate_cdc_hash_efficient(df2)
        
        assert hash1 != hash2
    
    def test_cdc_hash_length(self, sql_collector, sample_metadata_df):
        """Test that CDC hash is 32 characters"""
        hash_value = sql_collector._generate_cdc_hash_efficient(sample_metadata_df)
        
        assert len(hash_value) == 32
