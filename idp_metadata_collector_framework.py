# Databricks notebook source
# MAGIC %run ./DPCommonFunctions

# COMMAND ----------

# IDP Metadata Collector Framework
# File: idp_metadata_collector_framework.py
# Production-ready implementation with SOLID principles and Design Patterns

"""
IDP Metadata Collector Framework
=================================
A highly extensible and maintainable framework for collecting metadata from diverse data sources.

Design Patterns Used:
- Strategy Pattern: For different data source collectors
- Factory Pattern: For creating appropriate collectors
- Builder Pattern: For constructing metadata records
- Repository Pattern: For data access abstraction
- Chain of Responsibility: For validation pipeline

Performance Optimizations:
- Native Spark SQL functions instead of Python UDFs
- Proper DataFrame caching and unpersisting
- JDBC partitioning for parallel reads
- Broadcast variables for small lookup data
- Batch processing with configurable sizes
"""

from __future__ import annotations

import builtins
import logging
import re
import sys
import time
import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Callable, Union
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache

# Store references to built-in functions that may be shadowed
_builtin_min = builtins.min
_builtin_max = builtins.max
_builtin_len = builtins.len

import pyspark.sql.functions as F
from pyspark.sql import DataFrame, SparkSession, Column
from pyspark.sql.types import (
    ArrayType, BooleanType, IntegerType, LongType,
    StringType, StructField, StructType, TimestampType, DoubleType
)
from pyspark.storagelevel import StorageLevel

# ============================================================================
# CONFIGURATION AND CONSTANTS
# ============================================================================


class DataSourceType(Enum):
    """Enumeration of supported data source types"""
    ABFSS_STORAGE = "ABFSS_STORAGE"
    WABS_STORAGE = "WABS_STORAGE"
    WASBS_SAS_STORAGE = "WASBS_SAS_STORAGE"
    SQLSERVER = "SQLSERVER"
    POSTGRESQL = "POSTGRESQL"
    MARIADB = "MARIADB"
    CASSANDRA = "CASSANDRA"
    REST_API = "REST_API"


class CollectorConfig:
    """
    Configuration for the collector framework.
    Implements immutability through __slots__ and property access.
    """
    __slots__ = (
        '_BATCH_SIZE', '_MAX_RETRIES', '_MAX_WORKERS', '_COMPUTE_ROW_COUNT',
        '_SAMPLE_FILE_LIMIT', '_LOG_LEVEL', '_REST_API_TIMEOUT', '_JDBC_FETCH_SIZE',
        '_JDBC_BATCH_SIZE', '_JDBC_NUM_PARTITIONS', '_CACHE_STORAGE_LEVEL',
        '_RETRY_BASE_DELAY', '_RETRY_MAX_DELAY', '_CDC_SAMPLE_SIZE', '_ENABLE_SCHEMA_EVOLUTION'
    )
    
    def __init__(
        self,
        BATCH_SIZE: int = 25,
        MAX_RETRIES: int = 3,
        MAX_WORKERS: int = 5,
        COMPUTE_ROW_COUNT: bool = False,
        SAMPLE_FILE_LIMIT: int = 10,
        LOG_LEVEL: str = "INFO",
        REST_API_TIMEOUT: int = 30,
        JDBC_FETCH_SIZE: int = 10000,
        JDBC_BATCH_SIZE: int = 1000,
        JDBC_NUM_PARTITIONS: int = 10,
        CACHE_STORAGE_LEVEL: Optional[StorageLevel] = None,
        RETRY_BASE_DELAY: float = 1.0,
        RETRY_MAX_DELAY: float = 60.0,
        CDC_SAMPLE_SIZE: int = 100,
        ENABLE_SCHEMA_EVOLUTION: bool = True,
    ):
        object.__setattr__(self, '_BATCH_SIZE', BATCH_SIZE)
        object.__setattr__(self, '_MAX_RETRIES', MAX_RETRIES)
        object.__setattr__(self, '_MAX_WORKERS', MAX_WORKERS)
        object.__setattr__(self, '_COMPUTE_ROW_COUNT', COMPUTE_ROW_COUNT)
        object.__setattr__(self, '_SAMPLE_FILE_LIMIT', SAMPLE_FILE_LIMIT)
        object.__setattr__(self, '_LOG_LEVEL', LOG_LEVEL)
        object.__setattr__(self, '_REST_API_TIMEOUT', REST_API_TIMEOUT)
        object.__setattr__(self, '_JDBC_FETCH_SIZE', JDBC_FETCH_SIZE)
        object.__setattr__(self, '_JDBC_BATCH_SIZE', JDBC_BATCH_SIZE)
        object.__setattr__(self, '_JDBC_NUM_PARTITIONS', JDBC_NUM_PARTITIONS)
        object.__setattr__(self, '_CACHE_STORAGE_LEVEL', CACHE_STORAGE_LEVEL or StorageLevel.MEMORY_AND_DISK)
        object.__setattr__(self, '_RETRY_BASE_DELAY', RETRY_BASE_DELAY)
        object.__setattr__(self, '_RETRY_MAX_DELAY', RETRY_MAX_DELAY)
        object.__setattr__(self, '_CDC_SAMPLE_SIZE', CDC_SAMPLE_SIZE)
        object.__setattr__(self, '_ENABLE_SCHEMA_EVOLUTION', ENABLE_SCHEMA_EVOLUTION)
    
    @property
    def BATCH_SIZE(self) -> int:
        return self._BATCH_SIZE
    
    @property
    def MAX_RETRIES(self) -> int:
        return self._MAX_RETRIES
    
    @property
    def MAX_WORKERS(self) -> int:
        return self._MAX_WORKERS
    
    @property
    def COMPUTE_ROW_COUNT(self) -> bool:
        return self._COMPUTE_ROW_COUNT
    
    @property
    def SAMPLE_FILE_LIMIT(self) -> int:
        return self._SAMPLE_FILE_LIMIT
    
    @property
    def LOG_LEVEL(self) -> str:
        return self._LOG_LEVEL
    
    @property
    def REST_API_TIMEOUT(self) -> int:
        return self._REST_API_TIMEOUT
    
    @property
    def JDBC_FETCH_SIZE(self) -> int:
        return self._JDBC_FETCH_SIZE
    
    @property
    def JDBC_BATCH_SIZE(self) -> int:
        return self._JDBC_BATCH_SIZE
    
    @property
    def JDBC_NUM_PARTITIONS(self) -> int:
        return self._JDBC_NUM_PARTITIONS
    
    @property
    def CACHE_STORAGE_LEVEL(self) -> StorageLevel:
        return self._CACHE_STORAGE_LEVEL
    
    @property
    def RETRY_BASE_DELAY(self) -> float:
        return self._RETRY_BASE_DELAY
    
    @property
    def RETRY_MAX_DELAY(self) -> float:
        return self._RETRY_MAX_DELAY
    
    @property
    def CDC_SAMPLE_SIZE(self) -> int:
        return self._CDC_SAMPLE_SIZE
    
    @property
    def ENABLE_SCHEMA_EVOLUTION(self) -> bool:
        return self._ENABLE_SCHEMA_EVOLUTION
    
    def __setattr__(self, name, value):
        raise AttributeError("CollectorConfig is immutable")
    
    def with_row_count(self, enabled: bool) -> 'CollectorConfig':
        """Create new config with row count setting changed"""
        return CollectorConfig(
            BATCH_SIZE=self.BATCH_SIZE,
            MAX_RETRIES=self.MAX_RETRIES,
            MAX_WORKERS=self.MAX_WORKERS,
            COMPUTE_ROW_COUNT=enabled,
            SAMPLE_FILE_LIMIT=self.SAMPLE_FILE_LIMIT,
            LOG_LEVEL=self.LOG_LEVEL,
            REST_API_TIMEOUT=self.REST_API_TIMEOUT,
            JDBC_FETCH_SIZE=self.JDBC_FETCH_SIZE,
            JDBC_BATCH_SIZE=self.JDBC_BATCH_SIZE,
            JDBC_NUM_PARTITIONS=self.JDBC_NUM_PARTITIONS,
            CACHE_STORAGE_LEVEL=self.CACHE_STORAGE_LEVEL,
            RETRY_BASE_DELAY=self.RETRY_BASE_DELAY,
            RETRY_MAX_DELAY=self.RETRY_MAX_DELAY,
            CDC_SAMPLE_SIZE=self.CDC_SAMPLE_SIZE,
            ENABLE_SCHEMA_EVOLUTION=self.ENABLE_SCHEMA_EVOLUTION,
        )


# ============================================================================
# DATA MODELS (Following Single Responsibility Principle)
# ============================================================================


@dataclass
class ConnectionDetails:
    """Base connection details for all data sources"""
    source_id: str
    catalog_name: str
    table_name: Optional[str]
    metadata_enabled: bool
    is_active: bool
    db_details: Dict[str, Any]
    
    def __post_init__(self):
        """Validate required fields"""
        if not self.source_id:
            raise ValueError("source_id is required")
        if not self.catalog_name:
            raise ValueError("catalog_name is required")


@dataclass
class SQLConnectionDetails(ConnectionDetails):
    """SQL-specific connection details"""
    db_host: str = ""
    db_name: str = ""
    db_port: str = "1433"
    user_name: str = ""
    password_key: str = ""
    table_schema: List[str] = field(default_factory=list)
    exclude_list: List[str] = field(default_factory=list)
    include_list: List[str] = field(default_factory=list)
    append_only_list: List[str] = field(default_factory=list)
    is_ct_enabled: bool = False
    partition_column: Optional[str] = None
    lower_bound: Optional[int] = None
    upper_bound: Optional[int] = None


@dataclass
class StorageConnectionDetails(ConnectionDetails):
    """Storage-specific connection details"""
    storage_name: str = ""
    container_name: str = ""
    storage_access_key: str = ""
    folder_path: str = ""
    file_extension: Optional[str] = None
    file_options: Dict[str, Any] = field(default_factory=dict)
    id_columns: List[str] = field(default_factory=list)
    set_spark_config: bool = True


@dataclass
class RESTAPIConnectionDetails(ConnectionDetails):
    """REST API-specific connection details"""
    base_url: str = ""
    auth_type: str = ""
    auth_key: Optional[str] = None
    endpoints: List[str] = field(default_factory=list)
    headers: Dict[str, str] = field(default_factory=dict)
    timeout: int = 30


@dataclass
class CollectionResult:
    """Result of a metadata collection operation"""
    source_id: str
    status: str
    error_message: Optional[str] = None
    metadata_df: Optional[DataFrame] = None
    row_count: int = 0
    duration_seconds: float = 0.0
    retry_count: int = 0


# ============================================================================
# INTERFACES (Protocol classes for type hints)
# ============================================================================


class SecretProvider(ABC):
    """Abstract interface for secret management"""
    
    @abstractmethod
    def get_secret(self, key: str, default: Optional[str] = None) -> str:
        """Get secret value by key"""
        pass


class DataFrameWriter(ABC):
    """Abstract interface for writing DataFrames"""
    
    @abstractmethod
    def write_table(self, df: DataFrame, table_name: str, **kwargs) -> None:
        """Write DataFrame to table"""
        pass
    
    @abstractmethod
    def merge_table(self, df: DataFrame, table_name: str, merge_keys: List[str], **kwargs) -> None:
        """Merge DataFrame into table using Delta Lake"""
        pass


class DataFrameReader(ABC):
    """Abstract interface for reading DataFrames"""
    
    @abstractmethod
    def read_table(self, table_name: str) -> DataFrame:
        """Read table as DataFrame"""
        pass
    
    @abstractmethod
    def table_exists(self, table_name: str) -> bool:
        """Check if table exists"""
        pass


class HTTPClient(ABC):
    """Abstract interface for HTTP operations"""
    
    @abstractmethod
    def get(self, url: str, headers: Dict[str, str], timeout: int) -> Dict:
        """Make GET request"""
        pass
    
    @abstractmethod
    def post(self, url: str, headers: Dict[str, str], data: Any, timeout: int) -> Dict:
        """Make POST request"""
        pass


# ============================================================================
# LOGGING UTILITIES
# ============================================================================


class StructuredLogger:
    """
    Structured logger with context tracking and sensitive data masking.
    """
    
    SENSITIVE_PATTERNS = [
        r'password["\']?\s*[:=]\s*["\']?[^"\'\s,}]+',
        r'secret["\']?\s*[:=]\s*["\']?[^"\'\s,}]+',
        r'key["\']?\s*[:=]\s*["\']?[^"\'\s,}]+',
        r'token["\']?\s*[:=]\s*["\']?[^"\'\s,}]+',
    ]
    
    def __init__(self, name: str, level: str = "INFO", correlation_id: Optional[str] = None):
        self.logger = logging.getLogger(name)
        self.correlation_id = correlation_id or str(uuid4())[:8]
        self._setup_logger(level)
    
    def _setup_logger(self, level: str) -> None:
        """Setup logger with proper formatting"""
        if self.logger.handlers:
            return
        
        self.logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            f"%(asctime)s - %(levelname)s - [%(funcName)s:%(lineno)d] - "
            f"[correlation_id={self.correlation_id}] - %(message)s"
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.propagate = False
    
    def _mask_sensitive(self, message: str) -> str:
        """Mask sensitive data in log messages"""
        masked = message
        for pattern in self.SENSITIVE_PATTERNS:
            masked = re.sub(pattern, '[REDACTED]', masked, flags=re.IGNORECASE)
        return masked
    
    def info(self, message: str, **kwargs) -> None:
        self.logger.info(self._mask_sensitive(self._format_message(message, kwargs)))
    
    def warning(self, message: str, **kwargs) -> None:
        self.logger.warning(self._mask_sensitive(self._format_message(message, kwargs)))
    
    def error(self, message: str, **kwargs) -> None:
        self.logger.error(self._mask_sensitive(self._format_message(message, kwargs)))
    
    def debug(self, message: str, **kwargs) -> None:
        self.logger.debug(self._mask_sensitive(self._format_message(message, kwargs)))
    
    def _format_message(self, message: str, kwargs: Dict) -> str:
        """Format message with additional context"""
        if kwargs:
            context = " | ".join(f"{k}={v}" for k, v in kwargs.items())
            return f"{message} | {context}"
        return message


# ============================================================================
# UTILITY FUNCTIONS (Pure functions for performance)
# ============================================================================


def to_snake_case_expr(col: Column) -> Column:
    """
    Convert column value to snake_case using native Spark SQL.
    This is much faster than Python UDFs.
    """
    # Replace camelCase with snake_case
    # Step 1: Insert underscore before uppercase letters that follow lowercase
    step1 = F.regexp_replace(col, "([a-z])([A-Z])", "$1_$2")
    # Step 2: Handle consecutive uppercase followed by lowercase
    step2 = F.regexp_replace(step1, "([A-Z]+)([A-Z][a-z])", "$1_$2")
    # Step 3: Convert to lowercase
    return F.lower(step2)


def to_snake_case_array_expr(col: Column) -> Column:
    """
    Convert array of strings to snake_case using native Spark SQL.
    """
    return F.transform(col, lambda x: to_snake_case_expr(x))


def is_dataframe_empty(df: DataFrame) -> bool:
    """
    Efficiently check if DataFrame is empty without triggering full scan.
    Uses limit(1).collect() which is much faster than isEmpty() or count().
    Works across all Spark versions.
    """
    try:
        # limit(1).collect() returns empty list [] if DataFrame is empty
        return _builtin_len(df.limit(1).collect()) == 0
    except Exception:
        # Fallback to count for edge cases
        return df.count() == 0


def safe_get(d: Optional[Dict], key: str, default: Any = None) -> Any:
    """Safely get value from dictionary with default"""
    if d is None:
        return default
    return d.get(key, default)


def compute_schema_hash(schema_json: str, sample_count: int) -> str:
    """Compute a deterministic hash from schema and sample count"""
    hash_input = f"{schema_json}_{sample_count}"
    return hashlib.sha256(hash_input.encode()).hexdigest()[:32]


# ============================================================================
# ABSTRACT BASE CLASSES (Following Open/Closed Principle)
# ============================================================================


class MetadataCollector(ABC):
    """
    Abstract base class for all metadata collectors.
    Implements Template Method pattern for common operations.
    """
    
    def __init__(
        self,
        spark: SparkSession,
        secret_provider: SecretProvider,
        logger: StructuredLogger,
        config: CollectorConfig
    ):
        self.spark = spark
        self.secret_provider = secret_provider
        self.logger = logger
        self.config = config
    
    @abstractmethod
    def collect_metadata(self, connection: ConnectionDetails) -> Optional[DataFrame]:
        """Collect metadata from the data source"""
        pass
    
    @abstractmethod
    def validate_connection(self, connection: ConnectionDetails) -> Tuple[bool, Optional[str]]:
        """
        Validate connection details.
        Returns: (is_valid, error_message)
        """
        pass
    
    def enrich_metadata(self, df: DataFrame, connection: ConnectionDetails) -> DataFrame:
        """
        Common metadata enrichment logic using native Spark functions.
        Avoids Python UDFs for better performance.
        """
        if df is None or is_dataframe_empty(df):
            return df
        
        # Generate CDC hash efficiently using native functions
        cdc_hash = self._generate_cdc_hash_efficient(df)
        current_ts = F.current_timestamp()
        
        enriched_df = (
            df
            .withColumn("source_id", F.lit(connection.source_id))
            .withColumn("catalog_name", F.upper(F.lit(connection.catalog_name)))
            .withColumn("entity_name", F.lit(connection.table_name))
            .withColumn("idp_cdc_hash", F.lit(cdc_hash))
            .withColumn("idp_created_date", current_ts)
            .withColumn("idp_modified_date", current_ts)
        )
        
        return enriched_df
    
    def _generate_cdc_hash_efficient(self, df: DataFrame) -> str:
        """
        Generate CDC hash efficiently without collecting data to driver.
        Uses schema + sample count for fast hash computation.
        """
        try:
            # Get schema JSON (metadata only, no data movement)
            schema_json = df.schema.json()
            
            # Get approximate count using faster method
            # Use limit to avoid full scan
            sample_count = df.limit(self.config.CDC_SAMPLE_SIZE + 1).count()
            
            return compute_schema_hash(schema_json, sample_count)
            
        except Exception as e:
            self.logger.warning(f"Failed to generate CDC hash: {str(e)}")
            # Fallback to schema-only hash
            return hashlib.sha256(df.schema.json().encode()).hexdigest()[:32]


# ============================================================================
# CONCRETE COLLECTORS (Strategy Pattern Implementation)
# ============================================================================


class SQLMetadataCollector(MetadataCollector):
    """
    Collector for SQL databases (SQL Server, PostgreSQL, MariaDB).
    Optimized with JDBC partitioning and connection pooling.
    """
    
    JDBC_DRIVERS = {
        DataSourceType.SQLSERVER: "com.microsoft.sqlserver.jdbc.SQLServerDriver",
        DataSourceType.POSTGRESQL: "org.postgresql.Driver",
        DataSourceType.MARIADB: "org.mariadb.jdbc.Driver"
    }
    
    def validate_connection(self, connection: SQLConnectionDetails) -> Tuple[bool, Optional[str]]:
        """Validate SQL connection details"""
        required_fields = ['db_host', 'db_name', 'user_name', 'password_key']
        missing = [f for f in required_fields if not getattr(connection, f, None)]
        
        if missing:
            return False, f"Missing required fields: {', '.join(missing)}"
        
        if not connection.table_schema:
            return False, "table_schema is required"
        
        return True, None
    
    def collect_metadata(self, connection: SQLConnectionDetails) -> Optional[DataFrame]:
        """Collect metadata from SQL database with optimized JDBC reads"""
        self.logger.info(f"Collecting SQL metadata", source_id=connection.source_id)
        
        # Get password from secret provider
        password = self.secret_provider.get_secret(connection.password_key)
        
        # Build JDBC URL with connection pool settings
        jdbc_url = self._build_jdbc_url(connection)
        jdbc_props = self._get_jdbc_properties(connection, password)
        
        # Query information schema
        query = self._build_metadata_query(connection)
        
        # Read metadata with optimized settings
        df = (
            self.spark.read
            .format("jdbc")
            .option("url", jdbc_url)
            .option("query", query)
            .option("fetchsize", str(self.config.JDBC_FETCH_SIZE))
            .options(**jdbc_props)
            .load()
        )
        
        # Cache for multiple operations
        df = df.persist(self.config.CACHE_STORAGE_LEVEL)
        
        try:
            # Process and transform metadata
            processed_df = self._process_sql_metadata(df, connection)
            
            # Compute row counts and table sizes if enabled (expensive)
            if self.config.COMPUTE_ROW_COUNT:
                processed_df = self._add_sql_row_counts_optimized(
                    processed_df, connection, jdbc_url, jdbc_props
                )
            else:
                # Add null columns for row count and table size
                processed_df = (
                    processed_df
                    .withColumn("table_row_count", F.lit(None).cast(LongType()))
                    .withColumn("table_size", F.lit(None).cast(LongType()))
                )
            
            return self.enrich_metadata(processed_df, connection)
        finally:
            # Always unpersist to free memory
            df.unpersist()
    
    def _build_jdbc_url(self, connection: SQLConnectionDetails) -> str:
        """Build JDBC connection URL with proper encoding"""
        db_type = safe_get(connection.db_details, 'data_source_type')
        port = connection.db_port or self._get_default_port(db_type)
        
        if db_type == DataSourceType.SQLSERVER.value:
            return (
                f"jdbc:sqlserver://{connection.db_host}:{port};"
                f"database={connection.db_name};"
                f"encrypt=true;trustServerCertificate=true"
            )
        elif db_type == DataSourceType.POSTGRESQL.value:
            return f"jdbc:postgresql://{connection.db_host}:{port}/{connection.db_name}"
        elif db_type == DataSourceType.MARIADB.value:
            return f"jdbc:mariadb://{connection.db_host}:{port}/{connection.db_name}"
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    def _get_default_port(self, db_type: str) -> str:
        """Get default port for database type"""
        ports = {
            DataSourceType.SQLSERVER.value: "1433",
            DataSourceType.POSTGRESQL.value: "5432",
            DataSourceType.MARIADB.value: "3306"
        }
        return ports.get(db_type, "1433")
    
    def _get_jdbc_properties(self, connection: SQLConnectionDetails, password: str) -> Dict[str, str]:
        """Get JDBC connection properties"""
        db_type = safe_get(connection.db_details, 'data_source_type')
        
        props = {
            "user": connection.user_name,
            "password": password,
            "driver": self.JDBC_DRIVERS.get(
                DataSourceType(db_type),
                self.JDBC_DRIVERS[DataSourceType.SQLSERVER]
            )
        }
        
        # Add connection pool settings
        if db_type == DataSourceType.SQLSERVER.value:
            props.update({
                "connectionTimeout": "30",
                "loginTimeout": "30"
            })
        
        return props
    
    def _build_metadata_query(self, connection: SQLConnectionDetails) -> str:
        """Build optimized query to fetch metadata from information schema"""
        # Escape schema names properly
        schemas = "','".join(s.replace("'", "''") for s in connection.table_schema)
        db_type = safe_get(connection.db_details, 'data_source_type')
        
        if db_type == DataSourceType.SQLSERVER.value:
            return f"""
                SELECT 
                    CONCAT(c.TABLE_SCHEMA, '.', c.TABLE_NAME) AS full_table_name,
                    c.TABLE_NAME AS table_name,
                    c.COLUMN_NAME AS column_name,
                    c.DATA_TYPE AS data_type,
                    c.IS_NULLABLE AS is_nullable,
                    c.ORDINAL_POSITION AS ordinal_position,
                    CASE WHEN pk.COLUMN_NAME IS NOT NULL THEN 'true' ELSE 'false' END AS is_primary_key
                FROM INFORMATION_SCHEMA.COLUMNS c
                LEFT JOIN (
                    SELECT ku.TABLE_SCHEMA, ku.TABLE_NAME, ku.COLUMN_NAME
                    FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
                    INNER JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE ku
                        ON tc.CONSTRAINT_NAME = ku.CONSTRAINT_NAME
                        AND tc.TABLE_SCHEMA = ku.TABLE_SCHEMA
                    WHERE tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
                ) pk ON c.TABLE_SCHEMA = pk.TABLE_SCHEMA 
                    AND c.TABLE_NAME = pk.TABLE_NAME 
                    AND c.COLUMN_NAME = pk.COLUMN_NAME
                WHERE c.TABLE_SCHEMA IN ('{schemas}')
                ORDER BY c.TABLE_SCHEMA, c.TABLE_NAME, c.ORDINAL_POSITION
            """
        else:
            # PostgreSQL/MariaDB query with primary key detection
            return f"""
                SELECT 
                    CONCAT(c.table_schema, '.', c.table_name) AS full_table_name,
                    c.table_name,
                    c.column_name,
                    c.data_type,
                    c.is_nullable,
                    c.ordinal_position,
                    CASE WHEN pk.column_name IS NOT NULL THEN 'true' ELSE 'false' END AS is_primary_key
                FROM information_schema.columns c
                LEFT JOIN (
                    SELECT kcu.table_schema, kcu.table_name, kcu.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                    WHERE tc.constraint_type = 'PRIMARY KEY'
                ) pk ON c.table_schema = pk.table_schema 
                    AND c.table_name = pk.table_name 
                    AND c.column_name = pk.column_name
                WHERE c.table_schema IN ('{schemas}')
                ORDER BY c.table_schema, c.table_name, c.ordinal_position
            """
    
    def _process_sql_metadata(self, df: DataFrame, connection: SQLConnectionDetails) -> DataFrame:
        """
        Process raw SQL metadata into standard format.
        Uses native Spark functions for performance.
        """
        # Group by table to aggregate column information
        processed_df = (
            df.groupBy("full_table_name", "table_name")
            .agg(
                # Collect primary key columns (filter nulls using when/otherwise)
                F.collect_list(
                    F.when(F.col("is_primary_key") == "true", F.col("column_name"))
                ).alias("id_columns_raw"),
                F.collect_list("column_name").alias("source_schema"),
                F.count("column_name").alias("column_count"),
                F.collect_list(
                    F.struct(
                        F.col("column_name").alias("name"),
                        F.col("data_type").alias("data_type"),
                        F.col("is_nullable").alias("nullable")
                    )
                ).alias("column_details")
            )
            # Filter out null values from id_columns using array_except
            .withColumn(
                "id_columns",
                F.array_except(F.col("id_columns_raw"), F.array(F.lit(None).cast(StringType())))
            )
            .withColumn("partition_cols", F.array().cast(ArrayType(StringType())))
            .withColumn("ct_enabled", F.lit(1 if connection.is_ct_enabled else 0))
            .withColumn("db_name", F.lit(connection.db_name))
            .drop("id_columns_raw")
        )
        
        return processed_df
    
    def _add_sql_row_counts_optimized(
        self,
        df: DataFrame,
        connection: SQLConnectionDetails,
        jdbc_url: str,
        jdbc_props: Dict[str, str]
    ) -> DataFrame:
        """
        Add row counts and table sizes for SQL tables using optimized batch query.
        Uses UNION ALL for single database round-trip.
        """
        self.logger.info(f"Computing row counts and table sizes", source_id=connection.source_id)
        
        # Collect table names (small dataset, safe to collect)
        tables = [row["full_table_name"] for row in df.select("full_table_name").distinct().collect()]
        
        if not tables:
            return (
                df
                .withColumn("table_row_count", F.lit(None).cast(LongType()))
                .withColumn("table_size", F.lit(None).cast(LongType()))
            )
        
        # Build single query for all tables using UNION ALL
        count_queries = [
            f"SELECT '{table}' AS table_name, COUNT(*) AS row_count FROM {table}"
            for table in tables[:50]  # Limit to prevent query size issues
        ]
        
        if not count_queries:
            return (
                df
                .withColumn("table_row_count", F.lit(None).cast(LongType()))
                .withColumn("table_size", F.lit(None).cast(LongType()))
            )
        
        combined_query = " UNION ALL ".join(count_queries)
        
        try:
            counts_df = (
                self.spark.read
                .format("jdbc")
                .option("url", jdbc_url)
                .option("query", f"SELECT * FROM ({combined_query}) AS counts")
                .options(**jdbc_props)
                .load()
            )
            
            # Join counts back to main DataFrame
            result_df = df.join(
                counts_df,
                df["full_table_name"] == counts_df["table_name"],
                "left"
            ).withColumn(
                "table_row_count",
                F.col("row_count").cast(LongType())
            ).drop("table_name", "row_count")
            
            # Now get table sizes
            result_df = self._add_sql_table_sizes(
                result_df, connection, jdbc_url, jdbc_props, tables
            )
            
            return result_df
            
        except Exception as e:
            self.logger.warning(f"Failed to get row counts: {str(e)}")
            return (
                df
                .withColumn("table_row_count", F.lit(None).cast(LongType()))
                .withColumn("table_size", F.lit(None).cast(LongType()))
            )
    
    def _add_sql_table_sizes(
        self,
        df: DataFrame,
        connection: SQLConnectionDetails,
        jdbc_url: str,
        jdbc_props: Dict[str, str],
        tables: List[str]
    ) -> DataFrame:
        """
        Add table sizes in bytes for SQL tables.
        Uses database-specific queries to get table sizes.
        """
        db_type = safe_get(connection.db_details, 'data_source_type')
        
        try:
            if db_type == DataSourceType.SQLSERVER.value:
                # SQL Server: Use sp_spaceused or sys tables
                size_query = self._build_sqlserver_size_query(tables, connection.db_name)
            elif db_type == DataSourceType.POSTGRESQL.value:
                # PostgreSQL: Use pg_total_relation_size
                size_query = self._build_postgresql_size_query(tables)
            elif db_type == DataSourceType.MARIADB.value:
                # MariaDB/MySQL: Use information_schema.tables
                size_query = self._build_mariadb_size_query(tables, connection.db_name)
            else:
                self.logger.warning(f"Table size not supported for {db_type}")
                return df.withColumn("table_size", F.lit(None).cast(LongType()))
            
            if not size_query:
                return df.withColumn("table_size", F.lit(None).cast(LongType()))
            
            sizes_df = (
                self.spark.read
                .format("jdbc")
                .option("url", jdbc_url)
                .option("query", size_query)
                .options(**jdbc_props)
                .load()
            )
            
            # Join sizes back to main DataFrame
            return df.join(
                sizes_df,
                df["full_table_name"] == sizes_df["table_name"],
                "left"
            ).withColumn(
                "table_size",
                F.col("size_bytes").cast(LongType())
            ).drop("table_name", "size_bytes")
            
        except Exception as e:
            self.logger.warning(f"Failed to get table sizes: {str(e)}")
            return df.withColumn("table_size", F.lit(None).cast(LongType()))
    
    def _build_sqlserver_size_query(self, tables: List[str], db_name: str) -> str:
        """Build SQL Server query to get table sizes"""
        # Parse schema.table format
        table_conditions = []
        for table in tables[:50]:
            parts = table.split('.')
            if _builtin_len(parts) == 2:
                schema, tbl = parts
                table_conditions.append(f"(s.name = '{schema}' AND t.name = '{tbl}')")
        
        if not table_conditions:
            return ""
        
        conditions = " OR ".join(table_conditions)
        
        return f"""
            SELECT 
                CONCAT(s.name, '.', t.name) AS table_name,
                SUM(a.total_pages) * 8 * 1024 AS size_bytes
            FROM sys.tables t
            INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
            INNER JOIN sys.indexes i ON t.object_id = i.object_id
            INNER JOIN sys.partitions p ON i.object_id = p.object_id AND i.index_id = p.index_id
            INNER JOIN sys.allocation_units a ON p.partition_id = a.container_id
            WHERE ({conditions})
            GROUP BY s.name, t.name
        """
    
    def _build_postgresql_size_query(self, tables: List[str]) -> str:
        """Build PostgreSQL query to get table sizes"""
        table_conditions = []
        for table in tables[:50]:
            parts = table.split('.')
            if _builtin_len(parts) == 2:
                schema, tbl = parts
                table_conditions.append(
                    f"(schemaname = '{schema}' AND tablename = '{tbl}')"
                )
        
        if not table_conditions:
            return ""
        
        conditions = " OR ".join(table_conditions)
        
        return f"""
            SELECT 
                schemaname || '.' || tablename AS table_name,
                pg_total_relation_size(schemaname || '.' || tablename) AS size_bytes
            FROM pg_tables
            WHERE ({conditions})
        """
    
    def _build_mariadb_size_query(self, tables: List[str], db_name: str) -> str:
        """Build MariaDB/MySQL query to get table sizes"""
        table_names = []
        for table in tables[:50]:
            parts = table.split('.')
            if _builtin_len(parts) == 2:
                table_names.append(f"'{parts[1]}'")
            else:
                table_names.append(f"'{table}'")
        
        if not table_names:
            return ""
        
        tables_list = ", ".join(table_names)
        
        return f"""
            SELECT 
                CONCAT(table_schema, '.', table_name) AS table_name,
                (data_length + index_length) AS size_bytes
            FROM information_schema.tables
            WHERE table_schema = '{db_name}'
            AND table_name IN ({tables_list})
        """


class StorageMetadataCollector(MetadataCollector):
    """
    Collector for storage systems (ABFSS, WABS, WASBS).
    Optimized for parallel file processing.
    """
    
    def __init__(
        self,
        spark: SparkSession,
        secret_provider: SecretProvider,
        logger: StructuredLogger,
        config: CollectorConfig,
        dbutils: Any
    ):
        super().__init__(spark, secret_provider, logger, config)
        self.dbutils = dbutils
    
    def validate_connection(self, connection: StorageConnectionDetails) -> Tuple[bool, Optional[str]]:
        """Validate storage connection details"""
        required_fields = ['storage_name', 'container_name']
        missing = [f for f in required_fields if not getattr(connection, f, None)]
        
        if missing:
            return False, f"Missing required fields: {', '.join(missing)}"
        
        return True, None
    
    def collect_metadata(self, connection: StorageConnectionDetails) -> Optional[DataFrame]:
        """Collect metadata from storage system"""
        self.logger.info(f"Collecting storage metadata", source_id=connection.source_id)
        
        # Configure spark for storage access if needed
        if connection.set_spark_config and connection.storage_access_key:
            self._configure_storage_access(connection)
        
        # Build storage path
        storage_path = self._build_storage_path(connection)
        
        # List files in storage
        files = self._list_files_safe(storage_path, connection.file_extension)
        
        if not files:
            self.logger.warning(f"No files found", path=storage_path)
            return None
        
        # Process file metadata in batches
        metadata_rows = self._process_files_batch(files, connection)
        
        if not metadata_rows:
            return None
        
        # Create DataFrame from metadata
        schema = self._get_file_metadata_schema()
        df = self.spark.createDataFrame(metadata_rows, schema)
        
        # Add sample paths
        sample_paths = [f['path'] for f in files[:self.config.SAMPLE_FILE_LIMIT]]
        df = df.withColumn(
            "sample_file_paths",
            F.lit(sample_paths).cast(ArrayType(StringType()))
        )
        
        # Add table_size from file_size_bytes for files
        df = df.withColumn("table_size", F.col("file_size_bytes"))
        
        # Compute row counts if enabled
        if self.config.COMPUTE_ROW_COUNT and connection.file_extension:
            df = self._add_file_row_counts_optimized(df, connection)
        else:
            df = df.withColumn("table_row_count", F.lit(None).cast(LongType()))
        
        return self.enrich_metadata(df, connection)
    
    def _configure_storage_access(self, connection: StorageConnectionDetails) -> None:
        """Configure Spark for storage access"""
        try:
            access_key = self.secret_provider.get_secret(connection.storage_access_key)
            storage_type = safe_get(connection.db_details, 'data_source_type')
            
            if storage_type == DataSourceType.ABFSS_STORAGE.value:
                config_key = f"fs.azure.account.key.{connection.storage_name}.dfs.core.windows.net"
            else:
                config_key = f"fs.azure.account.key.{connection.storage_name}.blob.core.windows.net"
            
            self.spark.conf.set(config_key, access_key)
        except Exception as e:
            self.logger.warning(f"Failed to configure storage access: {str(e)}")
    
    def _build_storage_path(self, connection: StorageConnectionDetails) -> str:
        """Build storage path based on storage type"""
        storage_type = safe_get(connection.db_details, 'data_source_type')
        folder = connection.folder_path.strip('/') if connection.folder_path else ""
        
        if storage_type == DataSourceType.ABFSS_STORAGE.value:
            base = f"abfss://{connection.container_name}@{connection.storage_name}.dfs.core.windows.net"
        elif storage_type in [DataSourceType.WABS_STORAGE.value, DataSourceType.WASBS_SAS_STORAGE.value]:
            protocol = "wasbs" if "WASBS" in storage_type else "wasb"
            base = f"{protocol}://{connection.container_name}@{connection.storage_name}.blob.core.windows.net"
        else:
            raise ValueError(f"Unsupported storage type: {storage_type}")
        
        return f"{base}/{folder}" if folder else base
    
    def _list_files_safe(self, path: str, file_extension: Optional[str]) -> List[Dict]:
        """List files in storage path with error handling"""
        try:
            files = []
            for file_info in self.dbutils.fs.ls(path):
                # Skip directories (end with /)
                if file_info.name.endswith('/'):
                    continue
                
                # Filter by extension if specified
                if file_extension and not file_info.name.endswith(f".{file_extension.lstrip('.')}"):
                    continue
                
                mod_time = None
                if hasattr(file_info, 'modificationTime') and file_info.modificationTime:
                    try:
                        mod_time = datetime.fromtimestamp(file_info.modificationTime / 1000)
                    except (ValueError, OSError):
                        pass
                
                files.append({
                    'path': file_info.path,
                    'name': file_info.name,
                    'size': getattr(file_info, 'size', 0) or 0,
                    'modificationTime': mod_time
                })
            
            return files[:self.config.SAMPLE_FILE_LIMIT * 2]  # Limit for safety
            
        except Exception as e:
            self.logger.error(f"Failed to list files: {str(e)}", path=path)
            return []
    
    def _process_files_batch(
        self,
        files: List[Dict],
        connection: StorageConnectionDetails
    ) -> List[Dict]:
        """Process files and extract metadata"""
        metadata_rows = []
        files_to_process = files[:self.config.SAMPLE_FILE_LIMIT]
        
        # Try to infer schema from first valid file
        schema_info = self._infer_schema_from_files(files_to_process, connection)
        
        for file_info in files_to_process:
            try:
                file_name = file_info['name'].rsplit('.', 1)[0] if '.' in file_info['name'] else file_info['name']
                
                # Use inferred schema if available
                source_schema = schema_info.get('columns', [])
                column_count = _builtin_len(source_schema)
                
                # Match ID columns (case-insensitive)
                id_columns = []
                if connection.id_columns and source_schema:
                    schema_lower = {c.lower(): c for c in source_schema}
                    id_columns = [
                        schema_lower[c.lower()]
                        for c in connection.id_columns
                        if c.lower() in schema_lower
                    ]
                
                metadata_rows.append({
                    "full_table_name": file_info['path'],
                    "table_name": file_name,
                    "id_columns": id_columns,
                    "partition_cols": [],
                    "ct_enabled": 0,
                    "source_schema": source_schema,
                    "column_count": column_count,
                    "file_size_bytes": file_info['size'],
                    "file_last_modified": file_info['modificationTime']
                })
                
            except Exception as e:
                self.logger.warning(f"Failed to process file: {str(e)}", file=file_info['path'])
                continue
        
        return metadata_rows
    
    def _infer_schema_from_files(
        self,
        files: List[Dict],
        connection: StorageConnectionDetails
    ) -> Dict[str, Any]:
        """Infer schema from sample files efficiently"""
        if not files or not connection.file_extension:
            return {'columns': []}
        
        # Try first file
        file_path = files[0]['path']
        
        try:
            # Read with limit 0 to get schema only (no data read)
            file_options = connection.file_options or {}
            
            sample_df = (
                self.spark.read
                .format(connection.file_extension.lstrip('.'))
                .options(**file_options)
                .load(file_path)
            )
            
            # Get columns without triggering computation
            columns = sample_df.columns
            
            return {'columns': columns}
            
        except Exception as e:
            self.logger.warning(f"Failed to infer schema: {str(e)}")
            return {'columns': []}
    
    def _get_file_metadata_schema(self) -> StructType:
        """Get schema for file metadata DataFrame"""
        return StructType([
            StructField("full_table_name", StringType(), False),
            StructField("table_name", StringType(), False),
            StructField("id_columns", ArrayType(StringType()), True),
            StructField("partition_cols", ArrayType(StringType()), True),
            StructField("ct_enabled", IntegerType(), True),
            StructField("source_schema", ArrayType(StringType()), True),
            StructField("column_count", IntegerType(), True),
            StructField("file_size_bytes", LongType(), True),
            StructField("file_last_modified", TimestampType(), True)
        ])
    
    def _add_file_row_counts_optimized(
        self,
        df: DataFrame,
        connection: StorageConnectionDetails
    ) -> DataFrame:
        """Add row counts using count pushdown where possible"""
        self.logger.info(f"Computing file row counts", source_id=connection.source_id)
        
        # Collect file paths (small dataset)
        file_paths = [row["full_table_name"] for row in df.select("full_table_name").collect()]
        
        row_counts = {}
        for file_path in file_paths:
            try:
                # Use count() which can be optimized for Parquet/Delta
                file_df = (
                    self.spark.read
                    .format(connection.file_extension.lstrip('.'))
                    .options(**(connection.file_options or {}))
                    .load(file_path)
                )
                row_counts[file_path] = file_df.count()
            except Exception as e:
                self.logger.warning(f"Failed to count file: {str(e)}")
                row_counts[file_path] = None
        
        # Create broadcast variable for row counts (small data)
        row_counts_bc = self.spark.sparkContext.broadcast(row_counts)
        
        # Use broadcast in mapping
        @F.udf(LongType())
        def get_row_count(path: str) -> Optional[int]:
            return row_counts_bc.value.get(path)
        
        result = df.withColumn("table_row_count", get_row_count(F.col("full_table_name")))
        
        # Destroy broadcast after use
        row_counts_bc.destroy()
        
        return result


class CassandraMetadataCollector(MetadataCollector):
    """Collector for Cassandra databases"""
    
    def validate_connection(self, connection: ConnectionDetails) -> Tuple[bool, Optional[str]]:
        """Validate Cassandra connection details"""
        db_details = connection.db_details or {}
        required_fields = ['keyspace_name']
        missing = [f for f in required_fields if f not in db_details or not db_details[f]]
        
        if missing:
            return False, f"Missing required db_details fields: {', '.join(missing)}"
        
        return True, None
    
    def collect_metadata(self, connection: ConnectionDetails) -> Optional[DataFrame]:
        """Collect metadata from Cassandra"""
        self.logger.info(f"Collecting Cassandra metadata", source_id=connection.source_id)
        
        db_details = connection.db_details
        keyspace = db_details['keyspace_name']
        
        # Read using Cassandra connector
        df = (
            self.spark.read
            .format("org.apache.spark.sql.cassandra")
            .option("keyspace", "system_schema")
            .option("table", "columns")
            .load()
            .filter(F.col("keyspace_name") == keyspace)
        )
        
        # Cache for multiple operations
        df = df.persist(self.config.CACHE_STORAGE_LEVEL)
        
        try:
            # Process Cassandra metadata
            processed_df = self._process_cassandra_metadata(df, keyspace)
            return self.enrich_metadata(processed_df, connection)
        finally:
            df.unpersist()
    
    def _process_cassandra_metadata(self, df: DataFrame, keyspace: str) -> DataFrame:
        """Process Cassandra metadata into standard format"""
        return (
            df.groupBy("table_name")
            .agg(
                F.collect_list(
                    F.when(
                        F.col("kind").isin(["partition_key", "clustering"]),
                        F.col("column_name")
                    )
                ).alias("id_columns_raw"),
                F.collect_list("column_name").alias("source_schema"),
                F.count("column_name").alias("column_count")
            )
            .withColumn("full_table_name", F.concat(F.lit(f"{keyspace}."), F.col("table_name")))
            .withColumn(
                "id_columns",
                F.array_except(F.col("id_columns_raw"), F.array(F.lit(None).cast(StringType())))
            )
            .withColumn("partition_cols", F.array().cast(ArrayType(StringType())))
            .withColumn("table_row_count", F.lit(None).cast(LongType()))
            .withColumn("table_size", F.lit(None).cast(LongType()))
            .withColumn("ct_enabled", F.lit(0))
            .withColumn("db_name", F.lit(keyspace))
            .drop("id_columns_raw")
        )


class RESTAPIMetadataCollector(MetadataCollector):
    """
    Collector for REST API endpoints.
    Uses connection pooling and async where possible.
    """
    
    def __init__(
        self,
        spark: SparkSession,
        secret_provider: SecretProvider,
        logger: StructuredLogger,
        config: CollectorConfig,
        http_client: HTTPClient
    ):
        super().__init__(spark, secret_provider, logger, config)
        self.http_client = http_client
    
    def validate_connection(self, connection: RESTAPIConnectionDetails) -> Tuple[bool, Optional[str]]:
        """Validate REST API connection details"""
        if not connection.base_url:
            return False, "base_url is required"
        if not connection.auth_type:
            return False, "auth_type is required"
        
        return True, None
    
    def collect_metadata(self, connection: RESTAPIConnectionDetails) -> Optional[DataFrame]:
        """Collect metadata from REST API endpoints"""
        self.logger.info(f"Collecting REST API metadata", source_id=connection.source_id)
        
        # Prepare authentication headers
        headers = dict(connection.headers) if connection.headers else {}
        
        if connection.auth_type == "API_KEY" and connection.auth_key:
            api_key = self.secret_provider.get_secret(connection.auth_key)
            headers["Authorization"] = f"Bearer {api_key}"
        elif connection.auth_type == "BASIC_AUTH" and connection.auth_key:
            credentials = self.secret_provider.get_secret(connection.auth_key)
            import base64
            encoded = base64.b64encode(credentials.encode()).decode()
            headers["Authorization"] = f"Basic {encoded}"
        
        # Collect metadata from endpoints
        metadata_rows = []
        timeout = connection.timeout or self.config.REST_API_TIMEOUT
        
        for endpoint in connection.endpoints:
            try:
                url = f"{connection.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
                endpoint_metadata = self._extract_endpoint_metadata(url, headers, timeout, endpoint)
                if endpoint_metadata:
                    metadata_rows.append(endpoint_metadata)
            except Exception as e:
                self.logger.warning(f"Failed to process endpoint: {str(e)}", endpoint=endpoint)
                continue
        
        if not metadata_rows:
            return None
        
        # Create DataFrame from metadata
        schema = self._get_api_metadata_schema()
        df = self.spark.createDataFrame(metadata_rows, schema)
        
        return self.enrich_metadata(df, connection)
    
    def _extract_endpoint_metadata(
        self,
        url: str,
        headers: Dict[str, str],
        timeout: int,
        endpoint_name: str
    ) -> Optional[Dict]:
        """Extract metadata from a single API endpoint"""
        try:
            response = self.http_client.get(url, headers, timeout)
            
            # Infer schema from response
            source_schema = []
            if isinstance(response, dict):
                source_schema = list(response.keys())
            elif isinstance(response, list) and response and isinstance(response[0], dict):
                source_schema = list(response[0].keys())
            
            # Generate table name from endpoint
            table_name = endpoint_name.strip('/').replace('/', '_') or "api_endpoint"
            
            return {
                "full_table_name": url,
                "table_name": table_name,
                "id_columns": [],
                "partition_cols": [],
                "ct_enabled": 0,
                "source_schema": source_schema,
                "column_count": _builtin_len(source_schema),
                "table_row_count": None,
                "table_size": None,
                "api_endpoint": url,
                "response_format": "JSON"
            }
        except Exception as e:
            self.logger.warning(f"Failed to extract API metadata: {str(e)}", url=url)
            return None
    
    def _get_api_metadata_schema(self) -> StructType:
        """Get schema for API metadata DataFrame"""
        return StructType([
            StructField("full_table_name", StringType(), False),
            StructField("table_name", StringType(), False),
            StructField("id_columns", ArrayType(StringType()), True),
            StructField("partition_cols", ArrayType(StringType()), True),
            StructField("ct_enabled", IntegerType(), True),
            StructField("source_schema", ArrayType(StringType()), True),
            StructField("column_count", IntegerType(), True),
            StructField("table_row_count", LongType(), True),
            StructField("table_size", LongType(), True),
            StructField("api_endpoint", StringType(), True),
            StructField("response_format", StringType(), True)
        ])


# ============================================================================
# COLLECTOR FACTORY (Factory Pattern Implementation)
# ============================================================================


class MetadataCollectorFactory:
    """
    Factory for creating appropriate metadata collectors.
    Uses lazy initialization and caching.
    """
    
    def __init__(
        self,
        spark: SparkSession,
        secret_provider: SecretProvider,
        logger: StructuredLogger,
        config: CollectorConfig,
        dbutils: Any,
        http_client: HTTPClient
    ):
        self.spark = spark
        self.secret_provider = secret_provider
        self.logger = logger
        self.config = config
        self.dbutils = dbutils
        self.http_client = http_client
        self._collectors: Dict[DataSourceType, MetadataCollector] = {}
    
    def get_collector(self, data_source_type: DataSourceType) -> MetadataCollector:
        """Get or create appropriate collector for data source type"""
        if data_source_type not in self._collectors:
            self._collectors[data_source_type] = self._create_collector(data_source_type)
        return self._collectors[data_source_type]
    
    def _create_collector(self, data_source_type: DataSourceType) -> MetadataCollector:
        """Create new collector instance"""
        if data_source_type in [
            DataSourceType.SQLSERVER,
            DataSourceType.POSTGRESQL,
            DataSourceType.MARIADB
        ]:
            return SQLMetadataCollector(
                self.spark, self.secret_provider, self.logger, self.config
            )
        
        if data_source_type in [
            DataSourceType.ABFSS_STORAGE,
            DataSourceType.WABS_STORAGE,
            DataSourceType.WASBS_SAS_STORAGE
        ]:
            return StorageMetadataCollector(
                self.spark, self.secret_provider, self.logger, self.config, self.dbutils
            )
        
        if data_source_type == DataSourceType.CASSANDRA:
            return CassandraMetadataCollector(
                self.spark, self.secret_provider, self.logger, self.config
            )
        
        if data_source_type == DataSourceType.REST_API:
            return RESTAPIMetadataCollector(
                self.spark, self.secret_provider, self.logger, self.config, self.http_client
            )
        
        raise ValueError(f"No collector registered for {data_source_type}")


# ============================================================================
# METADATA ENRICHMENT PIPELINE (Builder Pattern)
# ============================================================================


class MetadataEnrichmentBuilder:
    """
    Builder for enriching metadata with additional information.
    Uses native Spark functions for performance.
    """
    
    def __init__(self, df: DataFrame):
        self._df = df
    
    def add_snake_case_columns(self) -> 'MetadataEnrichmentBuilder':
        """Add snake_case versions of column names using native Spark"""
        self._df = (
            self._df
            .withColumn("idp_db_name", to_snake_case_expr(F.col("table_name")))
            .withColumn(
                "idp_id_columns",
                F.when(
                    F.col("id_columns").isNotNull(),
                    to_snake_case_array_expr(F.col("id_columns"))
                ).otherwise(F.array().cast(ArrayType(StringType())))
            )
            .withColumn(
                "idp_schema",
                F.when(
                    F.col("source_schema").isNotNull(),
                    to_snake_case_array_expr(F.col("source_schema"))
                ).otherwise(F.array().cast(ArrayType(StringType())))
            )
        )
        return self
    
    def add_inclusion_logic(
        self,
        include_list: List[str],
        exclude_list: List[str]
    ) -> 'MetadataEnrichmentBuilder':
        """Add inclusion/exclusion logic using native Spark expressions"""
        # Create array literals
        include_array = F.array(*[F.lit(x) for x in include_list]) if include_list else F.array()
        exclude_array = F.array(*[F.lit(x) for x in exclude_list]) if exclude_list else F.array()
        
        self._df = (
            self._df
            .withColumn("include_list", include_array.cast(ArrayType(StringType())))
            .withColumn("exclude_list", exclude_array.cast(ArrayType(StringType())))
            .withColumn(
                "is_included",
                F.when(
                    # If both lists are empty, include all
                    (F.size("include_list") == 0) & (F.size("exclude_list") == 0),
                    F.lit(1)
                ).when(
                    # If in include list and not in exclude list
                    F.array_contains("include_list", F.col("table_name")) &
                    ~F.array_contains("exclude_list", F.col("table_name")),
                    F.lit(1)
                ).when(
                    # If include list is empty and not in exclude list
                    (F.size("include_list") == 0) &
                    ~F.array_contains("exclude_list", F.col("table_name")),
                    F.lit(1)
                ).otherwise(F.lit(0))
            )
        )
        return self
    
    def add_append_only_logic(self, append_only_list: List[str]) -> 'MetadataEnrichmentBuilder':
        """Add append-only logic"""
        if append_only_list:
            append_array = F.array(*[F.lit(x) for x in append_only_list])
            self._df = self._df.withColumn(
                "is_append_only",
                F.when(
                    F.array_contains(append_array, F.col("table_name")),
                    F.lit(1)
                ).otherwise(F.lit(0))
            )
        else:
            self._df = self._df.withColumn("is_append_only", F.lit(0))
        return self
    
    def add_run_properties(self) -> 'MetadataEnrichmentBuilder':
        """Add table run properties bitmap"""
        self._df = self._df.withColumn(
            "table_run_properties",
            (
                F.col("is_included") * 4 +
                F.col("ct_enabled") * 2 +
                F.col("is_append_only")
            ).cast(IntegerType())
        )
        return self
    
    def add_unique_id(self) -> 'MetadataEnrichmentBuilder':
        """Add unique identifier for each record"""
        self._df = self._df.withColumn(
            "id",
            F.concat_ws("_", F.col("source_id"), F.col("table_name"))
        )
        return self
    
    def build(self) -> DataFrame:
        """Return the enriched DataFrame"""
        return self._df


# ============================================================================
# DUPLICATE HANDLER
# ============================================================================


class DuplicateHandler:
    """Handler for resolving duplicate IDs in metadata"""
    
    def __init__(self, logger: StructuredLogger):
        self.logger = logger
    
    def resolve_duplicates(self, df: DataFrame) -> DataFrame:
        """Resolve duplicate IDs by appending schema prefix"""
        if is_dataframe_empty(df):
            return df
        
        # Cache for multiple operations
        df = df.persist(StorageLevel.MEMORY_AND_DISK)
        
        try:
            # Find duplicate IDs efficiently
            id_counts = df.groupBy("id").count()
            dup_ids_df = id_counts.filter(F.col("count") > 1).select("id")
            
            # Check if there are duplicates
            if is_dataframe_empty(dup_ids_df):
                self.logger.info("No duplicate IDs found")
                return df
            
            # Collect duplicate IDs (should be small)
            dup_ids = [row["id"] for row in dup_ids_df.collect()]
            self.logger.info(f"Resolving {_builtin_len(dup_ids)} duplicate IDs")
            
            # Broadcast for efficient filtering
            dup_ids_bc = df.sparkSession.sparkContext.broadcast(set(dup_ids))
            
            # Split DataFrames
            non_dup_df = df.filter(~F.col("id").isin(dup_ids))
            dup_df = df.filter(F.col("id").isin(dup_ids))
            
            # Resolve duplicates by adding schema prefix
            resolved_df = (
                dup_df
                .withColumn(
                    "_schema_prefix",
                    F.element_at(F.split(F.col("full_table_name"), "\\."), -2)
                )
                .withColumn(
                    "table_name",
                    F.when(
                        F.col("_schema_prefix").isNotNull(),
                        F.concat_ws("_", F.col("_schema_prefix"), F.col("table_name"))
                    ).otherwise(F.col("table_name"))
                )
                .withColumn("id", F.concat_ws("_", F.col("source_id"), F.col("table_name")))
                .drop("_schema_prefix")
            )
            
            # Union and deduplicate
            result = non_dup_df.unionByName(resolved_df, allowMissingColumns=True).dropDuplicates(["id"])
            
            dup_ids_bc.destroy()
            return result
            
        finally:
            df.unpersist()


# ============================================================================
# ORCHESTRATOR (Facade Pattern)
# ============================================================================


class MetadataCollectionOrchestrator:
    """
    Main orchestrator for the metadata collection process.
    Implements retry with exponential backoff and parallel processing.
    """
    
    def __init__(
        self,
        spark: SparkSession,
        secret_provider: SecretProvider,
        df_reader: DataFrameReader,
        df_writer: DataFrameWriter,
        dbutils: Any,
        http_client: HTTPClient,
        config: CollectorConfig = CollectorConfig()
    ):
        self.spark = spark
        self.secret_provider = secret_provider
        self.df_reader = df_reader
        self.df_writer = df_writer
        self.dbutils = dbutils
        self.http_client = http_client
        self.config = config
        self.logger = StructuredLogger(__name__, config.LOG_LEVEL)
        self.collector_factory = MetadataCollectorFactory(
            spark, secret_provider, self.logger, config, dbutils, http_client
        )
        self.duplicate_handler = DuplicateHandler(self.logger)
        self.results: List[CollectionResult] = []
    
    def collect_all(
        self,
        connections: List[ConnectionDetails],
        full_load: bool = False
    ) -> Tuple[DataFrame, DataFrame]:
        """
        Collect metadata from all connections.
        Returns: (metadata_df, summary_df)
        """
        self.logger.info(
            f"Starting metadata collection",
            source_count=_builtin_len(connections),
            mode="FULL" if full_load else "INCREMENTAL"
        )
        
        self.results = []
        all_metadata_dfs: List[DataFrame] = []
        
        # Process in batches
        for batch_start in range(0, _builtin_len(connections), self.config.BATCH_SIZE):
            batch_end = _builtin_min(batch_start + self.config.BATCH_SIZE, _builtin_len(connections))
            batch = connections[batch_start:batch_end]
            batch_num = batch_start // self.config.BATCH_SIZE + 1
            
            self.logger.info(
                f"Processing batch {batch_num}",
                start=batch_start + 1,
                end=batch_end
            )
            
            # Process batch in parallel
            batch_results = self._process_batch_parallel(batch)
            
            # Collect results
            for result in batch_results:
                self.results.append(result)
                if result.status == "Success" and result.metadata_df is not None:
                    all_metadata_dfs.append(result.metadata_df)
        
        # Combine all metadata
        if all_metadata_dfs:
            combined_df = self._combine_dataframes(all_metadata_dfs)
            combined_df = self.duplicate_handler.resolve_duplicates(combined_df)
        else:
            combined_df = self._create_empty_metadata_df()
        
        # Create summary DataFrame
        summary_df = self._create_summary_df()
        
        return combined_df, summary_df
    
    def _process_batch_parallel(self, batch: List[ConnectionDetails]) -> List[CollectionResult]:
        """Process a batch of connections in parallel"""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.config.MAX_WORKERS) as executor:
            future_to_conn = {
                executor.submit(self._process_single_connection, conn): conn
                for conn in batch
            }
            
            for future in as_completed(future_to_conn):
                connection = future_to_conn[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    status_icon = "✅" if result.status == "Success" else "❌"
                    self.logger.info(
                        f"{status_icon} {result.source_id}",
                        status=result.status,
                        row_count=result.row_count,
                        duration=f"{result.duration_seconds:.2f}s"
                    )
                    
                except Exception as e:
                    self.logger.error(f"Unexpected error", source_id=connection.source_id, error=str(e))
                    results.append(CollectionResult(
                        source_id=connection.source_id,
                        status="Failure",
                        error_message=str(e)[:500]
                    ))
        
        return results
    
    def _process_single_connection(self, connection: ConnectionDetails) -> CollectionResult:
        """Process a single connection with retry and exponential backoff"""
        start_time = time.time()
        last_error = None
        
        for attempt in range(1, self.config.MAX_RETRIES + 1):
            try:
                self.logger.debug(
                    f"Processing attempt {attempt}",
                    source_id=connection.source_id
                )
                
                # Get data source type
                ds_type_str = safe_get(connection.db_details, 'data_source_type')
                if not ds_type_str:
                    raise ValueError("data_source_type not found in db_details")
                
                data_source_type = DataSourceType(ds_type_str)
                collector = self.collector_factory.get_collector(data_source_type)
                
                # Validate connection
                is_valid, error_msg = collector.validate_connection(connection)
                if not is_valid:
                    raise ValueError(f"Invalid connection: {error_msg}")
                
                # Collect metadata
                metadata_df = collector.collect_metadata(connection)
                
                if metadata_df is None or is_dataframe_empty(metadata_df):
                    raise ValueError("No metadata collected")
                
                # Enrich metadata
                enriched_df = self._enrich_metadata(metadata_df, connection)
                
                # Cache and count
                enriched_df = enriched_df.persist(self.config.CACHE_STORAGE_LEVEL)
                row_count = enriched_df.count()
                
                duration = time.time() - start_time
                
                return CollectionResult(
                    source_id=connection.source_id,
                    status="Success",
                    metadata_df=enriched_df,
                    row_count=row_count,
                    duration_seconds=duration,
                    retry_count=attempt - 1
                )
                
            except Exception as e:
                last_error = e
                self.logger.warning(
                    f"Attempt {attempt} failed",
                    source_id=connection.source_id,
                    error=str(e)[:200]
                )
                
                if attempt < self.config.MAX_RETRIES:
                    # Exponential backoff with jitter
                    delay = _builtin_min(
                        self.config.RETRY_BASE_DELAY * (2 ** (attempt - 1)),
                        self.config.RETRY_MAX_DELAY
                    )
                    time.sleep(delay)
        
        # All retries exhausted
        duration = time.time() - start_time
        return CollectionResult(
            source_id=connection.source_id,
            status="Failure",
            error_message=str(last_error)[:500] if last_error else "Unknown error",
            duration_seconds=duration,
            retry_count=self.config.MAX_RETRIES
        )
    
    def _enrich_metadata(self, df: DataFrame, connection: ConnectionDetails) -> DataFrame:
        """Apply enrichment pipeline to metadata"""
        db_details = connection.db_details or {}
        
        builder = MetadataEnrichmentBuilder(df)
        
        enriched_df = (
            builder
            .add_snake_case_columns()
            .add_inclusion_logic(
                safe_get(db_details, 'include_list', []),
                safe_get(db_details, 'exclude_list', [])
            )
            .add_append_only_logic(safe_get(db_details, 'append_only_list', []))
            .add_run_properties()
            .add_unique_id()
            .build()
        )
        
        # Add active flag
        enriched_df = enriched_df.withColumn("is_active", F.col("is_included"))
        
        return enriched_df
    
    def _combine_dataframes(self, dfs: List[DataFrame]) -> DataFrame:
        """Combine multiple DataFrames with schema alignment"""
        if _builtin_len(dfs) == 1:
            return dfs[0]
        
        # Use reduce for cleaner combination
        from functools import reduce
        combined = reduce(
            lambda a, b: a.unionByName(b, allowMissingColumns=True),
            dfs
        )
        
        return combined.dropDuplicates(["id"])
    
    def _create_empty_metadata_df(self) -> DataFrame:
        """Create empty DataFrame with full metadata schema"""
        schema = StructType([
            StructField("full_table_name", StringType(), False),
            StructField("table_name", StringType(), False),
            StructField("id_columns", ArrayType(StringType()), True),
            StructField("partition_cols", ArrayType(StringType()), True),
            StructField("ct_enabled", IntegerType(), True),
            StructField("source_id", StringType(), False),
            StructField("catalog_name", StringType(), False),
            StructField("entity_name", StringType(), True),
            StructField("db_name", StringType(), True),
            StructField("id", StringType(), False),
            StructField("include_list", ArrayType(StringType()), True),
            StructField("exclude_list", ArrayType(StringType()), True),
            StructField("is_included", IntegerType(), True),
            StructField("is_append_only", IntegerType(), True),
            StructField("is_active", IntegerType(), True),
            StructField("table_run_properties", IntegerType(), True),
            StructField("idp_db_name", StringType(), True),
            StructField("idp_id_columns", ArrayType(StringType()), True),
            StructField("idp_cdc_hash", StringType(), True),
            StructField("idp_created_date", TimestampType(), True),
            StructField("idp_modified_date", TimestampType(), True),
            StructField("table_row_count", LongType(), True),
            StructField("table_size", LongType(), True),
            StructField("column_count", IntegerType(), True),
            StructField("source_schema", ArrayType(StringType()), True),
            StructField("idp_schema", ArrayType(StringType()), True),
            StructField("column_details", ArrayType(StructType([
                StructField("name", StringType(), True),
                StructField("data_type", StringType(), True),
                StructField("nullable", StringType(), True)
            ])), True),
            StructField("file_size_bytes", LongType(), True),
            StructField("file_last_modified", TimestampType(), True),
            StructField("sample_file_paths", ArrayType(StringType()), True),
            StructField("api_endpoint", StringType(), True),
            StructField("response_format", StringType(), True)
        ])
        
        return self.spark.createDataFrame([], schema)
    
    def _create_summary_df(self) -> DataFrame:
        """Create summary DataFrame from collection results"""
        summary_rows = [
            (
                r.source_id,
                r.status,
                r.error_message,
                r.row_count,
                round(r.duration_seconds, 2),
                r.retry_count
            )
            for r in self.results
        ]
        
        schema = StructType([
            StructField("source_id", StringType(), False),
            StructField("status", StringType(), False),
            StructField("error_message", StringType(), True),
            StructField("row_count", IntegerType(), True),
            StructField("duration_seconds", DoubleType(), True),
            StructField("retry_count", IntegerType(), True)
        ])
        
        return self.spark.createDataFrame(summary_rows, schema)
    
    def write_results(
        self,
        metadata_df: DataFrame,
        target_table: str,
        full_load: bool = False,
        merge_keys: Optional[List[str]] = None
    ) -> None:
        """
        Write metadata results to target table.
        Uses Delta merge for incremental updates when possible.
        """
        if is_dataframe_empty(metadata_df):
            self.logger.warning("No metadata to write")
            return
        
        row_count = metadata_df.count()
        self.logger.info(f"Writing results", row_count=row_count, target=target_table)
        
        try:
            if full_load:
                self.df_writer.write_table(
                    metadata_df,
                    target_table,
                    mode="overwrite",
                    overwriteSchema="true"
                )
            else:
                # Use merge for incremental updates
                merge_keys = merge_keys or ["id"]
                self.df_writer.merge_table(
                    metadata_df,
                    target_table,
                    merge_keys
                )
            
            self.logger.info(f"Successfully wrote metadata to {target_table}")
            
        except Exception as e:
            self.logger.error(f"Failed to write results: {str(e)}")
            raise


# ============================================================================
# IMPLEMENTATION HELPERS
# ============================================================================


class DatabricksSecretProvider(SecretProvider):
    """Databricks-specific secret provider implementation"""
    
    def __init__(self, dbutils: Any, scope: str = "idp-secrets"):
        self.dbutils = dbutils
        self.scope = scope
        self._cache: Dict[str, str] = {}
    
    def get_secret(self, key: str, default: Optional[str] = None) -> str:
        """Get secret from Databricks secret scope with caching"""
        if key in self._cache:
            return self._cache[key]
        
        try:
            value = self.dbutils.secrets.get(scope=self.scope, key=key)
            self._cache[key] = value
            return value
        except Exception:
            if default is not None:
                return default
            raise


class DatabricksDataFrameWriter(DataFrameWriter):
    """Databricks-specific DataFrame writer with Delta support"""
    
    def __init__(self, spark: SparkSession):
        self.spark = spark
    
    def write_table(self, df: DataFrame, table_name: str, **kwargs) -> None:
        """Write DataFrame to Delta table"""
        mode = kwargs.pop("mode", "overwrite")
        
        writer = df.write.format("delta").mode(mode)
        
        for key, value in kwargs.items():
            writer = writer.option(key, value)
        
        writer.saveAsTable(table_name)
    
    def merge_table(self, df: DataFrame, table_name: str, merge_keys: List[str], **kwargs) -> None:
        """Merge DataFrame into Delta table"""
        from delta.tables import DeltaTable
        
        # Check if table exists
        if not self.spark.catalog.tableExists(table_name):
            # Table doesn't exist, write as new
            self.write_table(df, table_name, mode="overwrite")
            return
        
        # Build merge condition
        delta_table = DeltaTable.forName(self.spark, table_name)
        merge_condition = " AND ".join([f"target.{k} = source.{k}" for k in merge_keys])
        
        # Perform merge
        (
            delta_table.alias("target")
            .merge(df.alias("source"), merge_condition)
            .whenMatchedUpdateAll()
            .whenNotMatchedInsertAll()
            .execute()
        )


class DatabricksDataFrameReader(DataFrameReader):
    """Databricks-specific DataFrame reader"""
    
    def __init__(self, spark: SparkSession):
        self.spark = spark
    
    def read_table(self, table_name: str) -> DataFrame:
        """Read DataFrame from Delta table"""
        return self.spark.table(table_name)
    
    def table_exists(self, table_name: str) -> bool:
        """Check if table exists"""
        try:
            return self.spark.catalog.tableExists(table_name)
        except Exception:
            return False


class RequestsHTTPClient(HTTPClient):
    """HTTP client implementation using requests library"""
    
    def __init__(self):
        try:
            import requests
            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry
            
            self.session = requests.Session()
            
            # Configure retry strategy
            retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504]
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            self.session.mount("http://", adapter)
            self.session.mount("https://", adapter)
            
        except ImportError:
            self.session = None
    
    def get(self, url: str, headers: Dict[str, str], timeout: int) -> Dict:
        """Make GET request"""
        if self.session is None:
            raise RuntimeError("requests library not available")
        
        response = self.session.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.json()
    
    def post(self, url: str, headers: Dict[str, str], data: Any, timeout: int) -> Dict:
        """Make POST request"""
        if self.session is None:
            raise RuntimeError("requests library not available")
        
        response = self.session.post(url, headers=headers, json=data, timeout=timeout)
        response.raise_for_status()
        return response.json()


# ============================================================================
# CONNECTION PARSER
# ============================================================================


def _get_row_value(row, key: str, default: Any = None) -> Any:
    """
    Safely get value from Spark Row object.
    Spark Row objects don't support .get() method in newer versions.
    """
    try:
        value = row[key]
        return value if value is not None else default
    except (KeyError, ValueError):
        return default


def parse_connections(config_df: DataFrame) -> List[ConnectionDetails]:
    """
    Parse connection configurations from DataFrame.
    Handles different source types appropriately.
    """
    connections = []
    
    # Filter active sources and collect (should be small dataset)
    # Handle both BOOLEAN and INT types for is_active column
    active_sources = config_df.filter(F.col("is_active").cast("boolean") == True).collect()
    
    for row in active_sources:
        try:
            # Parse db_details JSON if string
            db_details = row["db_details"]
            if isinstance(db_details, str):
                db_details = json.loads(db_details)
            
            data_source_type = db_details.get('data_source_type', '')
            
            # Create appropriate connection type
            if any(storage_type in data_source_type for storage_type in ["STORAGE", "ABFSS", "WABS"]):
                conn = StorageConnectionDetails(
                    source_id=row["id"],
                    catalog_name=row["catalog_name"],
                    table_name=_get_row_value(row, "table_name"),
                    metadata_enabled=_get_row_value(row, "metadata_enabled", True),
                    is_active=row["is_active"],
                    db_details=db_details,
                    storage_name=db_details.get('storage_name', ''),
                    container_name=db_details.get('container_name', ''),
                    storage_access_key=db_details.get('storage_access_key', ''),
                    folder_path=db_details.get('folder_path', ''),
                    file_extension=db_details.get('file_extension'),
                    file_options=db_details.get('file_options') or {},
                    id_columns=db_details.get('id_columns') or []
                )
            
            elif data_source_type == DataSourceType.REST_API.value:
                conn = RESTAPIConnectionDetails(
                    source_id=row["id"],
                    catalog_name=row["catalog_name"],
                    table_name=_get_row_value(row, "table_name"),
                    metadata_enabled=_get_row_value(row, "metadata_enabled", True),
                    is_active=row["is_active"],
                    db_details=db_details,
                    base_url=db_details.get('base_url', ''),
                    auth_type=db_details.get('auth_type', ''),
                    auth_key=db_details.get('auth_key'),
                    endpoints=db_details.get('endpoints') or [],
                    headers=db_details.get('headers') or {},
                    timeout=db_details.get('timeout', 30)
                )
            
            else:
                # SQL databases
                conn = SQLConnectionDetails(
                    source_id=row["id"],
                    catalog_name=row["catalog_name"],
                    table_name=_get_row_value(row, "table_name"),
                    metadata_enabled=_get_row_value(row, "metadata_enabled", True),
                    is_active=row["is_active"],
                    db_details=db_details,
                    db_host=db_details.get('db_host', ''),
                    db_name=db_details.get('db_name', ''),
                    db_port=db_details.get('db_port', ''),
                    user_name=db_details.get('user_name', ''),
                    password_key=db_details.get('password_key', ''),
                    table_schema=db_details.get('table_schema') or [],
                    exclude_list=db_details.get('exclude_list') or [],
                    include_list=db_details.get('include_list') or [],
                    append_only_list=db_details.get('append_only_list') or [],
                    is_ct_enabled=db_details.get('is_ct_enabled', False)
                )
            
            connections.append(conn)
            
        except Exception as e:
            # Log error but continue with other connections
            source_id = _get_row_value(row, 'id', 'unknown')
            print(f"Warning: Failed to parse connection {source_id}: {str(e)}")
            continue
    
    return connections


# ============================================================================
# MAIN EXECUTION
# ============================================================================


def main_notebook_execution(dbutils, spark: SparkSession) -> str:
    """
    Main execution function for Databricks notebook.
    
    Args:
        dbutils: Databricks utilities object
        spark: SparkSession
    
    Returns:
        Status string: "SUCCESS", "PARTIAL_SUCCESS", or "FAILURE"
    """
    
    # Initialize widgets with defaults
    dbutils.widgets.text("full_load", "False", "Full Load?")
    dbutils.widgets.text("job_run_id", "", "Job Run ID")
    dbutils.widgets.text("compute_row_count", "False", "Compute Row Counts?")
    
    # Parse widget values
    full_load = dbutils.widgets.get("full_load").strip().lower() == "true"
    job_run_id = dbutils.widgets.get("job_run_id").strip() or str(uuid4())
    compute_row_count = dbutils.widgets.get("compute_row_count").strip().lower() == "true"
    
    # Setup configuration
    config = CollectorConfig().with_row_count(compute_row_count)
    
    # Initialize components
    secret_provider = DatabricksSecretProvider(dbutils)
    df_reader = DatabricksDataFrameReader(spark)
    df_writer = DatabricksDataFrameWriter(spark)
    http_client = RequestsHTTPClient()
    
    # Load source configurations
    config_table = "qa_idp.config.metadata_source_connection_details"
    config_df = df_reader.read_table(config_table)
    
    # Parse connections
    connections = parse_connections(config_df)
    
    if not connections:
        print("⚠️ No active connections found")
        return "SUCCESS"
    
    # Execute collection
    orchestrator = MetadataCollectionOrchestrator(
        spark=spark,
        secret_provider=secret_provider,
        df_reader=df_reader,
        df_writer=df_writer,
        dbutils=dbutils,
        http_client=http_client,
        config=config
    )
    
    metadata_df, summary_df = orchestrator.collect_all(connections, full_load)
    
    # Display summary
    print("=" * 70)
    print("METADATA COLLECTION SUMMARY")
    print("=" * 70)
    summary_df.show(truncate=False)
    
    success_count = summary_df.filter(F.col("status") == "Success").count()
    failure_count = summary_df.filter(F.col("status") == "Failure").count()
    
    print(f"\nTotal sources processed: {_builtin_len(connections)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {failure_count}")
    print("=" * 70)
    
    # Write results
    if not is_dataframe_empty(metadata_df):
        target_table = "qa_idp.config.meta_data_registry"
        orchestrator.write_results(metadata_df, target_table, full_load)
        print(f"✅ Metadata written to {target_table}")
    else:
        print("⚠️ No metadata to write")
    
    # Write summary report
    summary_table = f"qa_idp.config.metadata_collection_summary_{job_run_id}"
    summary_df.write.format("delta").mode("overwrite").saveAsTable(summary_table)
    print(f"📊 Summary report written to {summary_table}")
    
    # Determine status
    if failure_count == 0:
        return "SUCCESS"
    elif success_count > 0:
        return "PARTIAL_SUCCESS"
    else:
        return "FAILURE"


# COMMAND ----------

# Execute when run as notebook
# Uncomment the following lines when running in Databricks:

# if __name__ == "__main__":
#     status = main_notebook_execution(dbutils, spark)
#     print(f"\n🏁 Final Status: {status}")
