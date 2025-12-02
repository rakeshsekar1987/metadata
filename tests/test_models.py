"""
Unit tests for data models in the IDP Metadata Collector Framework.
"""

import pytest

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from idp_metadata_collector_framework import (
    DataSourceType,
    CollectorConfig,
    ConnectionDetails,
    SQLConnectionDetails,
    StorageConnectionDetails,
    RESTAPIConnectionDetails,
    CollectionResult,
)


class TestDataSourceType:
    """Tests for DataSourceType enum"""
    
    def test_all_types_exist(self):
        """Test all expected data source types exist"""
        expected_types = [
            "ABFSS_STORAGE",
            "WABS_STORAGE",
            "WASBS_SAS_STORAGE",
            "SQLSERVER",
            "POSTGRESQL",
            "MARIADB",
            "CASSANDRA",
            "REST_API"
        ]
        
        actual_types = [t.value for t in DataSourceType]
        assert set(expected_types) == set(actual_types)
    
    def test_enum_value_access(self):
        """Test accessing enum values"""
        assert DataSourceType.SQLSERVER.value == "SQLSERVER"
        assert DataSourceType.ABFSS_STORAGE.value == "ABFSS_STORAGE"
    
    def test_enum_from_string(self):
        """Test creating enum from string value"""
        ds_type = DataSourceType("POSTGRESQL")
        assert ds_type == DataSourceType.POSTGRESQL


class TestCollectorConfig:
    """Tests for CollectorConfig dataclass"""
    
    def test_default_values(self):
        """Test default configuration values"""
        config = CollectorConfig()
        
        assert config.BATCH_SIZE == 25
        assert config.MAX_RETRIES == 3
        assert config.MAX_WORKERS == 5
        assert config.COMPUTE_ROW_COUNT is False
        assert config.SAMPLE_FILE_LIMIT == 10
        assert config.LOG_LEVEL == "INFO"
        assert config.REST_API_TIMEOUT == 30
        assert config.JDBC_FETCH_SIZE == 10000
        assert config.RETRY_BASE_DELAY == 1.0
        assert config.RETRY_MAX_DELAY == 60.0
    
    def test_frozen_immutability(self):
        """Test that config is immutable"""
        config = CollectorConfig()
        
        with pytest.raises(AttributeError, match="immutable"):
            config.BATCH_SIZE = 50
    
    def test_with_row_count(self):
        """Test with_row_count creates new config"""
        config = CollectorConfig()
        new_config = config.with_row_count(True)
        
        # Original unchanged
        assert config.COMPUTE_ROW_COUNT is False
        
        # New config has changed value
        assert new_config.COMPUTE_ROW_COUNT is True
        
        # Other values preserved
        assert new_config.BATCH_SIZE == config.BATCH_SIZE
        assert new_config.MAX_RETRIES == config.MAX_RETRIES
    
    def test_custom_values(self):
        """Test creating config with custom values"""
        config = CollectorConfig(
            BATCH_SIZE=50,
            MAX_RETRIES=5,
            LOG_LEVEL="DEBUG"
        )
        
        assert config.BATCH_SIZE == 50
        assert config.MAX_RETRIES == 5
        assert config.LOG_LEVEL == "DEBUG"


class TestConnectionDetails:
    """Tests for ConnectionDetails base class"""
    
    def test_valid_creation(self):
        """Test creating valid connection details"""
        conn = ConnectionDetails(
            source_id="test_source",
            catalog_name="TEST_CATALOG",
            table_name="test_table",
            metadata_enabled=True,
            is_active=True,
            db_details={"key": "value"}
        )
        
        assert conn.source_id == "test_source"
        assert conn.catalog_name == "TEST_CATALOG"
    
    def test_missing_source_id_raises(self):
        """Test that missing source_id raises ValueError"""
        with pytest.raises(ValueError, match="source_id is required"):
            ConnectionDetails(
                source_id="",
                catalog_name="TEST_CATALOG",
                table_name=None,
                metadata_enabled=True,
                is_active=True,
                db_details={}
            )
    
    def test_missing_catalog_name_raises(self):
        """Test that missing catalog_name raises ValueError"""
        with pytest.raises(ValueError, match="catalog_name is required"):
            ConnectionDetails(
                source_id="test",
                catalog_name="",
                table_name=None,
                metadata_enabled=True,
                is_active=True,
                db_details={}
            )
    
    def test_optional_table_name(self):
        """Test that table_name can be None"""
        conn = ConnectionDetails(
            source_id="test_source",
            catalog_name="TEST_CATALOG",
            table_name=None,
            metadata_enabled=True,
            is_active=True,
            db_details={}
        )
        
        assert conn.table_name is None


class TestSQLConnectionDetails:
    """Tests for SQLConnectionDetails dataclass"""
    
    def test_inheritance(self):
        """Test that SQLConnectionDetails inherits from ConnectionDetails"""
        conn = SQLConnectionDetails(
            source_id="sql_source",
            catalog_name="CATALOG",
            table_name=None,
            metadata_enabled=True,
            is_active=True,
            db_details={},
            db_host="localhost",
            db_name="testdb"
        )
        
        assert isinstance(conn, ConnectionDetails)
    
    def test_default_values(self):
        """Test default values for SQL connection"""
        conn = SQLConnectionDetails(
            source_id="sql_source",
            catalog_name="CATALOG",
            table_name=None,
            metadata_enabled=True,
            is_active=True,
            db_details={}
        )
        
        assert conn.db_host == ""
        assert conn.db_port == "1433"
        assert conn.table_schema == []
        assert conn.exclude_list == []
        assert conn.include_list == []
        assert conn.is_ct_enabled is False
    
    def test_full_connection_details(self, sql_connection_details):
        """Test fully populated SQL connection"""
        conn = sql_connection_details
        
        assert conn.db_host == "localhost"
        assert conn.db_name == "test_db"
        assert conn.db_port == "1433"
        assert conn.user_name == "test_user"
        assert conn.password_key == "password_key"
        assert "dbo" in conn.table_schema
        assert conn.is_ct_enabled is True


class TestStorageConnectionDetails:
    """Tests for StorageConnectionDetails dataclass"""
    
    def test_inheritance(self):
        """Test that StorageConnectionDetails inherits from ConnectionDetails"""
        conn = StorageConnectionDetails(
            source_id="storage_source",
            catalog_name="CATALOG",
            table_name=None,
            metadata_enabled=True,
            is_active=True,
            db_details={},
            storage_name="mystorage",
            container_name="container"
        )
        
        assert isinstance(conn, ConnectionDetails)
    
    def test_default_values(self):
        """Test default values for storage connection"""
        conn = StorageConnectionDetails(
            source_id="storage_source",
            catalog_name="CATALOG",
            table_name=None,
            metadata_enabled=True,
            is_active=True,
            db_details={}
        )
        
        assert conn.storage_name == ""
        assert conn.container_name == ""
        assert conn.folder_path == ""
        assert conn.file_extension is None
        assert conn.file_options == {}
        assert conn.id_columns == []
        assert conn.set_spark_config is True
    
    def test_full_connection_details(self, storage_connection_details):
        """Test fully populated storage connection"""
        conn = storage_connection_details
        
        assert conn.storage_name == "teststorage"
        assert conn.container_name == "testcontainer"
        assert conn.folder_path == "data/files"
        assert conn.file_extension == "parquet"
        assert "id" in conn.id_columns


class TestRESTAPIConnectionDetails:
    """Tests for RESTAPIConnectionDetails dataclass"""
    
    def test_inheritance(self):
        """Test that RESTAPIConnectionDetails inherits from ConnectionDetails"""
        conn = RESTAPIConnectionDetails(
            source_id="api_source",
            catalog_name="CATALOG",
            table_name=None,
            metadata_enabled=True,
            is_active=True,
            db_details={},
            base_url="https://api.example.com",
            auth_type="API_KEY"
        )
        
        assert isinstance(conn, ConnectionDetails)
    
    def test_default_values(self):
        """Test default values for REST API connection"""
        conn = RESTAPIConnectionDetails(
            source_id="api_source",
            catalog_name="CATALOG",
            table_name=None,
            metadata_enabled=True,
            is_active=True,
            db_details={}
        )
        
        assert conn.base_url == ""
        assert conn.auth_type == ""
        assert conn.auth_key is None
        assert conn.endpoints == []
        assert conn.headers == {}
        assert conn.timeout == 30
    
    def test_full_connection_details(self, rest_api_connection_details):
        """Test fully populated REST API connection"""
        conn = rest_api_connection_details
        
        assert conn.base_url == "https://api.example.com"
        assert conn.auth_type == "API_KEY"
        assert conn.auth_key == "api_key_secret"
        assert "users" in conn.endpoints
        assert conn.timeout == 30


class TestCollectionResult:
    """Tests for CollectionResult dataclass"""
    
    def test_success_result(self):
        """Test creating successful collection result"""
        result = CollectionResult(
            source_id="test_source",
            status="Success",
            row_count=100,
            duration_seconds=5.5
        )
        
        assert result.source_id == "test_source"
        assert result.status == "Success"
        assert result.error_message is None
        assert result.row_count == 100
        assert result.duration_seconds == 5.5
        assert result.retry_count == 0
    
    def test_failure_result(self):
        """Test creating failed collection result"""
        result = CollectionResult(
            source_id="test_source",
            status="Failure",
            error_message="Connection timeout",
            duration_seconds=30.0,
            retry_count=3
        )
        
        assert result.status == "Failure"
        assert result.error_message == "Connection timeout"
        assert result.retry_count == 3
    
    def test_default_values(self):
        """Test default values for collection result"""
        result = CollectionResult(
            source_id="test_source",
            status="Success"
        )
        
        assert result.error_message is None
        assert result.metadata_df is None
        assert result.row_count == 0
        assert result.duration_seconds == 0.0
        assert result.retry_count == 0
