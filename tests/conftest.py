"""
Pytest configuration and shared fixtures for IDP Metadata Collector tests.
"""

import pytest
from unittest.mock import MagicMock, Mock, patch
from datetime import datetime
from typing import Dict, List, Any, Optional

# Import PySpark components
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, 
    LongType, ArrayType, TimestampType, BooleanType
)

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================================
# SPARK SESSION FIXTURE
# ============================================================================

@pytest.fixture(scope="session")
def spark():
    """
    Create a SparkSession for testing.
    Uses local mode with minimal resources for fast tests.
    """
    spark_session = (
        SparkSession.builder
        .master("local[2]")
        .appName("IDP_Metadata_Collector_Tests")
        .config("spark.sql.shuffle.partitions", "2")
        .config("spark.default.parallelism", "2")
        .config("spark.ui.enabled", "false")
        .config("spark.sql.warehouse.dir", "/tmp/spark-warehouse")
        .config("spark.driver.memory", "1g")
        .config("spark.executor.memory", "1g")
        .getOrCreate()
    )
    
    yield spark_session
    
    spark_session.stop()


# ============================================================================
# MOCK FIXTURES
# ============================================================================

@pytest.fixture
def mock_dbutils():
    """Create mock dbutils object for Databricks"""
    dbutils = MagicMock()
    
    # Mock secrets
    dbutils.secrets.get.return_value = "mock_secret_value"
    
    # Mock fs operations
    mock_file_info = MagicMock()
    mock_file_info.path = "abfss://container@storage.dfs.core.windows.net/folder/file.parquet"
    mock_file_info.name = "file.parquet"
    mock_file_info.size = 1024
    mock_file_info.modificationTime = int(datetime.now().timestamp() * 1000)
    
    dbutils.fs.ls.return_value = [mock_file_info]
    
    # Mock widgets
    dbutils.widgets.get.side_effect = lambda x: {
        "full_load": "False",
        "job_run_id": "test-job-123",
        "compute_row_count": "False"
    }.get(x, "")
    
    return dbutils


@pytest.fixture
def mock_secret_provider():
    """Create mock secret provider"""
    from idp_metadata_collector_framework import SecretProvider
    
    class MockSecretProvider(SecretProvider):
        def __init__(self, secrets: Dict[str, str] = None):
            self._secrets = secrets or {"password_key": "mock_password"}
        
        def get_secret(self, key: str, default: Optional[str] = None) -> str:
            return self._secrets.get(key, default or f"mock_{key}")
    
    return MockSecretProvider()


@pytest.fixture
def mock_http_client():
    """Create mock HTTP client"""
    from idp_metadata_collector_framework import HTTPClient
    
    class MockHTTPClient(HTTPClient):
        def __init__(self):
            self.responses = {}
        
        def get(self, url: str, headers: Dict[str, str], timeout: int) -> Dict:
            return self.responses.get(url, {"id": 1, "name": "test", "value": "data"})
        
        def post(self, url: str, headers: Dict[str, str], data: Any, timeout: int) -> Dict:
            return {"status": "success", "data": data}
        
        def set_response(self, url: str, response: Dict):
            self.responses[url] = response
    
    return MockHTTPClient()


@pytest.fixture
def mock_logger():
    """Create mock structured logger"""
    from idp_metadata_collector_framework import StructuredLogger
    return StructuredLogger("test_logger", "DEBUG", "test-correlation-id")


@pytest.fixture
def default_config():
    """Create default collector config"""
    from idp_metadata_collector_framework import CollectorConfig
    return CollectorConfig()


# ============================================================================
# DATA MODEL FIXTURES
# ============================================================================

@pytest.fixture
def sql_connection_details():
    """Create SQL connection details for testing"""
    from idp_metadata_collector_framework import SQLConnectionDetails
    
    return SQLConnectionDetails(
        source_id="test_sql_source",
        catalog_name="TEST_CATALOG",
        table_name="test_table",
        metadata_enabled=True,
        is_active=True,
        db_details={
            "data_source_type": "SQLSERVER",
            "include_list": [],
            "exclude_list": [],
            "append_only_list": []
        },
        db_host="localhost",
        db_name="test_db",
        db_port="1433",
        user_name="test_user",
        password_key="password_key",
        table_schema=["dbo", "sales"],
        is_ct_enabled=True
    )


@pytest.fixture
def storage_connection_details():
    """Create storage connection details for testing"""
    from idp_metadata_collector_framework import StorageConnectionDetails
    
    return StorageConnectionDetails(
        source_id="test_storage_source",
        catalog_name="TEST_CATALOG",
        table_name=None,
        metadata_enabled=True,
        is_active=True,
        db_details={
            "data_source_type": "ABFSS_STORAGE",
            "include_list": [],
            "exclude_list": []
        },
        storage_name="teststorage",
        container_name="testcontainer",
        storage_access_key="storage_key",
        folder_path="data/files",
        file_extension="parquet",
        id_columns=["id", "customer_id"]
    )


@pytest.fixture
def rest_api_connection_details():
    """Create REST API connection details for testing"""
    from idp_metadata_collector_framework import RESTAPIConnectionDetails
    
    return RESTAPIConnectionDetails(
        source_id="test_api_source",
        catalog_name="TEST_CATALOG",
        table_name=None,
        metadata_enabled=True,
        is_active=True,
        db_details={
            "data_source_type": "REST_API",
            "include_list": [],
            "exclude_list": []
        },
        base_url="https://api.example.com",
        auth_type="API_KEY",
        auth_key="api_key_secret",
        endpoints=["users", "orders", "products"],
        headers={"Content-Type": "application/json"},
        timeout=30
    )


# ============================================================================
# DATAFRAME FIXTURES
# ============================================================================

@pytest.fixture
def sample_metadata_df(spark):
    """Create sample metadata DataFrame"""
    schema = StructType([
        StructField("full_table_name", StringType(), False),
        StructField("table_name", StringType(), False),
        StructField("id_columns", ArrayType(StringType()), True),
        StructField("partition_cols", ArrayType(StringType()), True),
        StructField("ct_enabled", IntegerType(), True),
        StructField("source_schema", ArrayType(StringType()), True),
        StructField("column_count", IntegerType(), True),
        StructField("db_name", StringType(), True)
    ])
    
    data = [
        ("dbo.customers", "customers", ["id"], [], 1, ["id", "name", "email"], 3, "test_db"),
        ("dbo.orders", "orders", ["order_id"], [], 0, ["order_id", "customer_id", "amount"], 3, "test_db"),
        ("sales.products", "products", ["product_id"], [], 1, ["product_id", "name", "price"], 3, "test_db"),
    ]
    
    return spark.createDataFrame(data, schema)


@pytest.fixture
def sample_sql_metadata_df(spark):
    """Create sample SQL metadata DataFrame (raw from JDBC)"""
    schema = StructType([
        StructField("full_table_name", StringType(), False),
        StructField("table_name", StringType(), False),
        StructField("column_name", StringType(), False),
        StructField("data_type", StringType(), False),
        StructField("is_nullable", StringType(), True),
        StructField("ordinal_position", IntegerType(), True),
        StructField("is_primary_key", StringType(), True)
    ])
    
    data = [
        ("dbo.customers", "customers", "id", "int", "NO", 1, "true"),
        ("dbo.customers", "customers", "name", "varchar", "YES", 2, "false"),
        ("dbo.customers", "customers", "email", "varchar", "YES", 3, "false"),
        ("dbo.orders", "orders", "order_id", "int", "NO", 1, "true"),
        ("dbo.orders", "orders", "customer_id", "int", "NO", 2, "false"),
        ("dbo.orders", "orders", "amount", "decimal", "YES", 3, "false"),
    ]
    
    return spark.createDataFrame(data, schema)


@pytest.fixture
def config_df(spark):
    """Create sample configuration DataFrame matching real table structure"""
    import json
    
    # Schema matches the real table: data_source_type is a separate column
    schema = StructType([
        StructField("id", StringType(), False),
        StructField("data_source_type", StringType(), False),  # Separate column, not in db_details
        StructField("catalog_name", StringType(), False),
        StructField("table_name", StringType(), True),
        StructField("metadata_enabled", BooleanType(), True),
        StructField("is_active", BooleanType(), True),
        StructField("db_details", StringType(), False)
    ])
    
    data = [
        (
            "source_1",
            "SQLSERVER",  # data_source_type as separate column
            "CATALOG_A",
            None,
            True,
            True,
            json.dumps({
                # No data_source_type here - it's in the row column
                "db_host": "localhost",
                "db_name": "test_db",
                "db_port": "1433",
                "user_name": "admin",
                "password_key": "sql_password",
                "table_schema": ["dbo"],
                "include_list": [],
                "exclude_list": []
            })
        ),
        (
            "source_2",
            "ABFSS_STORAGE",  # data_source_type as separate column
            "CATALOG_B",
            None,
            True,
            True,
            json.dumps({
                # No data_source_type here - it's in the row column
                "storage_name": "mystorageaccount",
                "container_name": "data",
                "folder_path": "raw/files",
                "file_extension": "parquet"
            })
        ),
        (
            "source_3",
            "POSTGRESQL",  # data_source_type as separate column
            "CATALOG_C",
            None,
            True,
            False,  # Inactive
            json.dumps({
                # No data_source_type here - it's in the row column
                "db_host": "pg.example.com"
            })
        )
    ]
    
    return spark.createDataFrame(data, schema)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_empty_df(spark, schema: StructType) -> DataFrame:
    """Create an empty DataFrame with given schema"""
    return spark.createDataFrame([], schema)


def assert_dataframe_equal(df1: DataFrame, df2: DataFrame, ignore_order: bool = True):
    """Assert two DataFrames are equal"""
    if ignore_order:
        # Sort by all columns for comparison
        cols = df1.columns
        df1_sorted = df1.orderBy(*cols)
        df2_sorted = df2.orderBy(*cols)
    else:
        df1_sorted = df1
        df2_sorted = df2
    
    assert df1_sorted.collect() == df2_sorted.collect()


def assert_schema_equal(df1: DataFrame, df2: DataFrame):
    """Assert two DataFrames have equal schemas"""
    assert df1.schema == df2.schema
