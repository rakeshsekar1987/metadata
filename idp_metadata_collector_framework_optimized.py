# Databricks notebook source
# MAGIC %run ./DPCommonFunctions

# COMMAND ----------

"""
IDP Metadata Collector Framework - Optimized Version
=====================================================
Production-ready, highly optimized implementation for collecting metadata from diverse data sources.

Key Optimizations:
- Frozen dataclasses for immutable configs
- Batched DataFrame operations (reduced Catalyst overhead)
- Registry-based factory pattern (O(1) collector lookup)
- Single-pass DataFrame enrichment
- Lazy evaluation where possible
- Consolidated schema definitions
- Memory-efficient generators
"""

from __future__ import annotations

import builtins
import hashlib
import json
import logging
import re
import sys
import time
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, fields
from datetime import datetime
from enum import Enum
from functools import reduce
from typing import Any, Callable, Dict, List, Optional, Tuple
from uuid import uuid4

import pyspark.sql.functions as F
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.types import (
    ArrayType, DoubleType, IntegerType, LongType,
    StringType, StructField, StructType, TimestampType
)
from pyspark.storagelevel import StorageLevel

# Preserve builtins that may be shadowed
_min, _max, _len, _round = builtins.min, builtins.max, builtins.len, builtins.round


# ============================================================================
# ENUMS AND CONFIGURATION
# ============================================================================

class DataSourceType(Enum):
    """Supported data source types"""
    ABFSS_STORAGE = "ABFSS_STORAGE"
    WABS_STORAGE = "WABS_STORAGE"
    WASBS_SAS_STORAGE = "WASBS_SAS_STORAGE"
    SQLSERVER = "SQLSERVER"
    POSTGRESQL = "POSTGRESQL"
    MARIADB = "MARIADB"
    CASSANDRA = "CASSANDRA"
    REST_API = "REST_API"


@dataclass(frozen=True)
class CollectorConfig:
    """Immutable configuration using frozen dataclass"""
    BATCH_SIZE: int = 25
    MAX_RETRIES: int = 3
    MAX_WORKERS: int = 5
    COMPUTE_ROW_COUNT: bool = False
    SAMPLE_FILE_LIMIT: int = 10
    LOG_LEVEL: str = "INFO"
    REST_API_TIMEOUT: int = 30
    JDBC_FETCH_SIZE: int = 10000
    JDBC_BATCH_SIZE: int = 1000
    JDBC_NUM_PARTITIONS: int = 10
    CACHE_STORAGE_LEVEL: StorageLevel = field(default_factory=lambda: StorageLevel.MEMORY_AND_DISK)
    RETRY_BASE_DELAY: float = 1.0
    RETRY_MAX_DELAY: float = 60.0
    CDC_SAMPLE_SIZE: int = 100

    def with_row_count(self, enabled: bool) -> CollectorConfig:
        """Create new config with modified row count setting"""
        kwargs = {f.name: getattr(self, f.name) for f in fields(self)}
        kwargs['COMPUTE_ROW_COUNT'] = enabled
        return CollectorConfig(**kwargs)

    def with_updates(self, **updates) -> CollectorConfig:
        """Create new config with multiple updates"""
        kwargs = {f.name: getattr(self, f.name) for f in fields(self)}
        kwargs.update(updates)
        return CollectorConfig(**kwargs)


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class ConnectionDetails:
    """Base connection details"""
    source_id: str
    catalog_name: str
    table_name: Optional[str]
    metadata_enabled: bool
    is_active: bool
    db_details: Dict[str, Any]

    def __post_init__(self):
        if not self.source_id or not self.catalog_name:
            raise ValueError("source_id and catalog_name are required")


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
    """REST API connection details"""
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
# ABSTRACT INTERFACES
# ============================================================================

class SecretProvider(ABC):
    @abstractmethod
    def get_secret(self, key: str, default: Optional[str] = None, scope: Optional[str] = None) -> str:
        pass


class DataFrameWriter(ABC):
    @abstractmethod
    def write_table(self, df: DataFrame, table_name: str, **kwargs) -> None:
        pass

    @abstractmethod
    def merge_table(self, df: DataFrame, table_name: str, merge_keys: List[str]) -> None:
        pass


class DataFrameReader(ABC):
    @abstractmethod
    def read_table(self, table_name: str) -> DataFrame:
        pass

    @abstractmethod
    def table_exists(self, table_name: str) -> bool:
        pass


class HTTPClient(ABC):
    @abstractmethod
    def get(self, url: str, headers: Dict[str, str], timeout: int) -> Dict:
        pass


# ============================================================================
# LOGGING - Simplified structured logger
# ============================================================================

class StructuredLogger:
    """Structured logger with sensitive data masking"""
    _SENSITIVE_PATTERN = re.compile(
        r'(password|secret|key|token)["\']?\s*[:=]\s*["\']?[^"\'\s,}]+',
        re.IGNORECASE
    )

    def __init__(self, name: str, level: str = "INFO", correlation_id: Optional[str] = None):
        self.correlation_id = correlation_id or str(uuid4())[:8]
        self.logger = logging.getLogger(name)
        if not self.logger.handlers:
            self.logger.setLevel(getattr(logging, level.upper(), logging.INFO))
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter(
                f"%(asctime)s - %(levelname)s - [%(funcName)s:%(lineno)d] - "
                f"[cid={self.correlation_id}] - %(message)s"
            ))
            self.logger.addHandler(handler)
            self.logger.propagate = False

    def _fmt(self, msg: str, kw: Dict) -> str:
        text = f"{msg} | {' | '.join(f'{k}={v}' for k, v in kw.items())}" if kw else msg
        return self._SENSITIVE_PATTERN.sub('[REDACTED]', text)

    def info(self, msg: str, **kw) -> None:
        self.logger.info(self._fmt(msg, kw))

    def warning(self, msg: str, **kw) -> None:
        self.logger.warning(self._fmt(msg, kw))

    def error(self, msg: str, **kw) -> None:
        self.logger.error(self._fmt(msg, kw))

    def debug(self, msg: str, **kw) -> None:
        self.logger.debug(self._fmt(msg, kw))


# ============================================================================
# UTILITY FUNCTIONS - Pure functions, no side effects
# ============================================================================

def to_snake_case_col(col: F.Column) -> F.Column:
    """Convert column to snake_case using native Spark (much faster than UDFs)"""
    return F.lower(F.regexp_replace(
        F.regexp_replace(col, "([a-z])([A-Z])", "$1_$2"),
        "([A-Z]+)([A-Z][a-z])", "$1_$2"
    ))


def is_df_empty(df: Optional[DataFrame]) -> bool:
    """Efficiently check if DataFrame is empty (avoids full scan)"""
    if df is None:
        return True
    try:
        return _len(df.limit(1).collect()) == 0
    except Exception:
        return True


def safe_get(d: Optional[Dict], key: str, default: Any = None) -> Any:
    """Safe dictionary access"""
    return d.get(key, default) if d else default


def compute_schema_hash(schema_json: str, sample_count: int) -> str:
    """Compute deterministic hash from schema"""
    return hashlib.sha256(f"{schema_json}_{sample_count}".encode()).hexdigest()[:32]


def get_data_source_type(db_details: Dict[str, Any]) -> str:
    """Extract data source type trying multiple key names"""
    keys = ('data_source_type', 'dataSourceType', 'source_type', 'sourceType',
            'type', 'connection_type', 'db_type', 'database_type')
    for key in keys:
        value = db_details.get(key)
        if value:
            return str(value).upper()
    return ''


def get_row_value(row, key: str, default: Any = None) -> Any:
    """Safely get value from Spark Row"""
    try:
        val = row[key]
        return val if val is not None else default
    except (KeyError, ValueError, IndexError):
        return default


def escape_sql_string(s: str) -> str:
    """Escape single quotes in SQL strings"""
    return s.replace("'", "''") if s else ""


# ============================================================================
# SCHEMA DEFINITIONS - Single source of truth
# ============================================================================

COLUMN_DETAIL_SCHEMA = StructType([
    StructField("name", StringType(), True),
    StructField("data_type", StringType(), True),
    StructField("nullable", StringType(), True)
])

METADATA_SCHEMA = StructType([
    StructField("full_table_name", StringType(), False),
    StructField("table_name", StringType(), False),
    StructField("id_columns", ArrayType(StringType()), True),
    StructField("partition_cols", ArrayType(StringType()), True),
    StructField("ct_enabled", IntegerType(), True),
    StructField("source_id", StringType(), True),
    StructField("catalog_name", StringType(), True),
    StructField("entity_name", StringType(), True),
    StructField("db_name", StringType(), True),
    StructField("id", StringType(), True),
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
    StructField("column_details", ArrayType(COLUMN_DETAIL_SCHEMA), True),
    StructField("file_size_bytes", LongType(), True),
    StructField("file_last_modified", TimestampType(), True),
    StructField("sample_file_paths", ArrayType(StringType()), True),
    StructField("api_endpoint", StringType(), True),
    StructField("response_format", StringType(), True)
])

FILE_METADATA_SCHEMA = StructType([
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

API_METADATA_SCHEMA = StructType([
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

SUMMARY_SCHEMA = StructType([
    StructField("source_id", StringType(), False),
    StructField("status", StringType(), False),
    StructField("error_message", StringType(), True),
    StructField("row_count", IntegerType(), True),
    StructField("duration_seconds", DoubleType(), True),
    StructField("retry_count", IntegerType(), True)
])


# ============================================================================
# ABSTRACT COLLECTOR BASE
# ============================================================================

class MetadataCollector(ABC):
    """Base class for metadata collectors with common operations"""

    def __init__(self, spark: SparkSession, secret_provider: SecretProvider,
                 logger: StructuredLogger, config: CollectorConfig):
        self.spark = spark
        self.secret_provider = secret_provider
        self.logger = logger
        self.config = config

    @abstractmethod
    def collect_metadata(self, connection: ConnectionDetails) -> Optional[DataFrame]:
        pass

    @abstractmethod
    def validate_connection(self, connection: ConnectionDetails) -> Tuple[bool, Optional[str]]:
        pass

    def enrich_metadata(self, df: DataFrame, connection: ConnectionDetails) -> DataFrame:
        """Common metadata enrichment using native Spark functions"""
        if is_df_empty(df):
            return df

        cdc_hash = self._generate_cdc_hash(df)
        ts = F.current_timestamp()

        return df.select(
            "*",
            F.lit(connection.source_id).alias("source_id"),
            F.upper(F.lit(connection.catalog_name)).alias("catalog_name"),
            F.lit(connection.table_name).alias("entity_name"),
            F.lit(cdc_hash).alias("idp_cdc_hash"),
            ts.alias("idp_created_date"),
            ts.alias("idp_modified_date")
        )

    def _generate_cdc_hash(self, df: DataFrame) -> str:
        """Generate CDC hash efficiently"""
        try:
            schema_json = df.schema.json()
            sample_count = df.limit(self.config.CDC_SAMPLE_SIZE + 1).count()
            return compute_schema_hash(schema_json, sample_count)
        except Exception:
            return hashlib.sha256(df.schema.json().encode()).hexdigest()[:32]


# ============================================================================
# SQL METADATA COLLECTOR - Optimized
# ============================================================================

class SQLMetadataCollector(MetadataCollector):
    """SQL database collector with optimized JDBC operations"""

    DRIVERS = {
        DataSourceType.SQLSERVER: "com.microsoft.sqlserver.jdbc.SQLServerDriver",
        DataSourceType.POSTGRESQL: "org.postgresql.Driver",
        DataSourceType.MARIADB: "org.mariadb.jdbc.Driver"
    }
    PORTS = {
        DataSourceType.SQLSERVER: "1433",
        DataSourceType.POSTGRESQL: "5432",
        DataSourceType.MARIADB: "3306"
    }

    def validate_connection(self, conn: SQLConnectionDetails) -> Tuple[bool, Optional[str]]:
        missing = [f for f in ('db_host', 'db_name', 'user_name', 'password_key')
                   if not getattr(conn, f, None)]
        return (False, f"Missing: {', '.join(missing)}") if missing else (True, None)

    def collect_metadata(self, conn: SQLConnectionDetails) -> Optional[DataFrame]:
        self.logger.info("Collecting SQL metadata", source_id=conn.source_id)

        password = self.secret_provider.get_secret(
            conn.password_key, scope=safe_get(conn.db_details, 'secret_scope')
        )
        jdbc_url = self._build_jdbc_url(conn)
        jdbc_props = self._get_jdbc_props(conn, password)
        query = self._build_metadata_query(conn)

        df = (self.spark.read.format("jdbc")
              .option("url", jdbc_url)
              .option("query", query)
              .option("fetchsize", str(self.config.JDBC_FETCH_SIZE))
              .options(**jdbc_props)
              .load())

        df = df.persist(self.config.CACHE_STORAGE_LEVEL)
        try:
            processed = self._process_metadata(df, conn)
            processed = self._add_row_counts(processed, conn, jdbc_url, jdbc_props)
            return self.enrich_metadata(processed, conn)
        finally:
            df.unpersist()

    def _build_jdbc_url(self, conn: SQLConnectionDetails) -> str:
        db_type = safe_get(conn.db_details, 'data_source_type', '').upper()
        port = conn.db_port or self._get_default_port(db_type)

        if 'SQLSERVER' in db_type or 'MSSQL' in db_type:
            return f"jdbc:sqlserver://{conn.db_host}:{port};database={conn.db_name};encrypt=true;trustServerCertificate=true"
        elif 'POSTGRESQL' in db_type:
            return f"jdbc:postgresql://{conn.db_host}:{port}/{conn.db_name}"
        elif 'MARIADB' in db_type:
            return f"jdbc:mariadb://{conn.db_host}:{port}/{conn.db_name}"
        raise ValueError(f"Unsupported database type: {db_type}")

    def _get_default_port(self, db_type: str) -> str:
        if 'SQLSERVER' in db_type or 'MSSQL' in db_type:
            return "1433"
        elif 'POSTGRESQL' in db_type:
            return "5432"
        elif 'MARIADB' in db_type:
            return "3306"
        return "1433"

    def _get_jdbc_props(self, conn: SQLConnectionDetails, password: str) -> Dict[str, str]:
        db_type = safe_get(conn.db_details, 'data_source_type', '').upper()

        # Determine driver
        driver = self.DRIVERS[DataSourceType.SQLSERVER]  # default
        for ds_type, drv in self.DRIVERS.items():
            if ds_type.value in db_type:
                driver = drv
                break

        props = {"user": conn.user_name, "password": password, "driver": driver}
        if 'SQLSERVER' in db_type or 'MSSQL' in db_type:
            props.update({"connectionTimeout": "30", "loginTimeout": "30"})
        return props

    def _build_metadata_query(self, conn: SQLConnectionDetails) -> str:
        db_type = safe_get(conn.db_details, 'data_source_type', '').upper()
        is_mssql = 'SQLSERVER' in db_type or 'MSSQL' in db_type

        conditions = []

        # Schema filter
        if conn.table_schema:
            schemas = "','".join(escape_sql_string(s) for s in conn.table_schema)
            col = "c.TABLE_SCHEMA" if is_mssql else "c.table_schema"
            conditions.append(f"{col} IN ('{schemas}')")
        elif is_mssql:
            conditions.append("c.TABLE_SCHEMA = 'dbo'")
        else:
            conditions.append("c.table_schema NOT IN ('information_schema', 'pg_catalog', 'mysql', 'performance_schema', 'sys')")

        # Include list filter
        if conn.include_list:
            tables = "','".join(escape_sql_string(t) for t in conn.include_list)
            col = "c.TABLE_NAME" if is_mssql else "c.table_name"
            conditions.append(f"{col} IN ('{tables}')")

        where = " AND ".join(conditions) if conditions else "1=1"

        if is_mssql:
            return f"""
                SELECT CONCAT(c.TABLE_SCHEMA, '.', c.TABLE_NAME) AS full_table_name,
                       c.TABLE_NAME AS table_name, c.COLUMN_NAME AS column_name,
                       c.DATA_TYPE AS data_type, c.IS_NULLABLE AS is_nullable,
                       c.ORDINAL_POSITION AS ordinal_position,
                       CASE WHEN pk.COLUMN_NAME IS NOT NULL THEN 'true' ELSE 'false' END AS is_primary_key
                FROM INFORMATION_SCHEMA.COLUMNS c
                LEFT JOIN (
                    SELECT ku.TABLE_SCHEMA, ku.TABLE_NAME, ku.COLUMN_NAME
                    FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
                    INNER JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE ku
                        ON tc.CONSTRAINT_NAME = ku.CONSTRAINT_NAME AND tc.TABLE_SCHEMA = ku.TABLE_SCHEMA
                    WHERE tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
                ) pk ON c.TABLE_SCHEMA = pk.TABLE_SCHEMA AND c.TABLE_NAME = pk.TABLE_NAME AND c.COLUMN_NAME = pk.COLUMN_NAME
                WHERE {where}"""
        else:
            return f"""
                SELECT CONCAT(c.table_schema, '.', c.table_name) AS full_table_name,
                       c.table_name, c.column_name, c.data_type, c.is_nullable, c.ordinal_position,
                       CASE WHEN pk.column_name IS NOT NULL THEN 'true' ELSE 'false' END AS is_primary_key
                FROM information_schema.columns c
                LEFT JOIN (
                    SELECT kcu.table_schema, kcu.table_name, kcu.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                        ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
                    WHERE tc.constraint_type = 'PRIMARY KEY'
                ) pk ON c.table_schema = pk.table_schema AND c.table_name = pk.table_name AND c.column_name = pk.column_name
                WHERE {where}"""

    def _process_metadata(self, df: DataFrame, conn: SQLConnectionDetails) -> DataFrame:
        """Process SQL metadata into standard format using batched operations"""
        return (
            df.groupBy("full_table_name", "table_name")
            .agg(
                F.array_except(
                    F.collect_list(F.when(F.col("is_primary_key") == "true", F.col("column_name"))),
                    F.array(F.lit(None).cast(StringType()))
                ).alias("id_columns"),
                F.collect_list("column_name").alias("source_schema"),
                F.count("column_name").alias("column_count"),
                F.collect_list(F.struct(
                    F.col("column_name").alias("name"),
                    F.col("data_type").alias("data_type"),
                    F.col("is_nullable").alias("nullable")
                )).alias("column_details")
            )
            .select(
                "*",
                F.array().cast(ArrayType(StringType())).alias("partition_cols"),
                F.lit(1 if conn.is_ct_enabled else 0).alias("ct_enabled"),
                F.lit(conn.db_name).alias("db_name")
            )
        )

    def _add_row_counts(self, df: DataFrame, conn: SQLConnectionDetails,
                        jdbc_url: str, jdbc_props: Dict[str, str]) -> DataFrame:
        """Add row counts and table sizes if enabled"""
        null_long = F.lit(None).cast(LongType())

        if not self.config.COMPUTE_ROW_COUNT:
            return df.select("*", null_long.alias("table_row_count"), null_long.alias("table_size"))

        self.logger.info("Computing row counts", source_id=conn.source_id)
        tables = [r["full_table_name"] for r in df.select("full_table_name").distinct().collect()]

        if not tables:
            return df.select("*", null_long.alias("table_row_count"), null_long.alias("table_size"))

        # Single query for all table counts (limit to 50 for query size)
        tables_batch = tables[:50]
        count_query = " UNION ALL ".join(
            f"SELECT '{escape_sql_string(t)}' AS tbl_name, COUNT(*) AS row_count FROM {t}"
            for t in tables_batch
        )

        try:
            counts_df = (self.spark.read.format("jdbc")
                         .option("url", jdbc_url)
                         .option("query", f"SELECT * FROM ({count_query}) AS counts")
                         .options(**jdbc_props)
                         .load())

            # Broadcast small lookup table
            counts_lookup = F.broadcast(counts_df.select(
                F.col("tbl_name").alias("_lt"),
                F.col("row_count").cast(LongType()).alias("_lc")
            ))

            result = (df
                      .join(counts_lookup, F.col("full_table_name") == F.col("_lt"), "left")
                      .withColumn("table_row_count", F.col("_lc"))
                      .drop("_lt", "_lc"))

            return self._add_table_sizes(result, conn, jdbc_url, jdbc_props, tables_batch)

        except Exception as e:
            self.logger.warning(f"Failed to get row counts: {e}")
            return df.select("*", null_long.alias("table_row_count"), null_long.alias("table_size"))

    def _add_table_sizes(self, df: DataFrame, conn: SQLConnectionDetails,
                         jdbc_url: str, jdbc_props: Dict[str, str], tables: List[str]) -> DataFrame:
        """Add table sizes in bytes"""
        null_long = F.lit(None).cast(LongType())
        db_type = safe_get(conn.db_details, 'data_source_type', '').upper()
        size_query = self._build_size_query(db_type, tables, conn.db_name)

        if not size_query:
            return df.withColumn("table_size", null_long)

        try:
            sizes_df = (self.spark.read.format("jdbc")
                        .option("url", jdbc_url)
                        .option("query", size_query)
                        .options(**jdbc_props)
                        .load())

            sizes_lookup = F.broadcast(sizes_df.select(
                F.col("table_name").alias("_st"),
                F.col("size_bytes").cast(LongType()).alias("_sb")
            ))

            return (df
                    .join(sizes_lookup, F.col("full_table_name") == F.col("_st"), "left")
                    .withColumn("table_size", F.col("_sb"))
                    .drop("_st", "_sb"))

        except Exception as e:
            self.logger.warning(f"Failed to get table sizes: {e}")
            return df.withColumn("table_size", null_long)

    def _build_size_query(self, db_type: str, tables: List[str], db_name: str) -> str:
        """Build database-specific size query"""
        # Parse schema.table format
        parsed = []
        for t in tables:
            parts = t.split('.', 1)
            if _len(parts) == 2:
                parsed.append((parts[0], parts[1]))

        if not parsed:
            return ""

        if 'SQLSERVER' in db_type or 'MSSQL' in db_type:
            conds = " OR ".join(
                f"(s.name = '{escape_sql_string(s)}' AND t.name = '{escape_sql_string(tbl)}')"
                for s, tbl in parsed
            )
            return f"""
                SELECT CONCAT(s.name, '.', t.name) AS table_name, SUM(a.total_pages) * 8 * 1024 AS size_bytes
                FROM sys.tables t
                INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
                INNER JOIN sys.indexes i ON t.object_id = i.object_id
                INNER JOIN sys.partitions p ON i.object_id = p.object_id AND i.index_id = p.index_id
                INNER JOIN sys.allocation_units a ON p.partition_id = a.container_id
                WHERE ({conds}) GROUP BY s.name, t.name"""

        elif 'POSTGRESQL' in db_type:
            conds = " OR ".join(
                f"(schemaname = '{escape_sql_string(s)}' AND tablename = '{escape_sql_string(tbl)}')"
                for s, tbl in parsed
            )
            return f"""
                SELECT schemaname || '.' || tablename AS table_name,
                       pg_total_relation_size(schemaname || '.' || tablename) AS size_bytes
                FROM pg_tables WHERE ({conds})"""

        elif 'MARIADB' in db_type:
            tnames = ", ".join(f"'{escape_sql_string(tbl)}'" for _, tbl in parsed)
            return f"""
                SELECT CONCAT(table_schema, '.', table_name) AS table_name,
                       (data_length + index_length) AS size_bytes
                FROM information_schema.tables
                WHERE table_schema = '{escape_sql_string(db_name)}' AND table_name IN ({tnames})"""

        return ""


# ============================================================================
# STORAGE METADATA COLLECTOR - Optimized
# ============================================================================

class StorageMetadataCollector(MetadataCollector):
    """Storage collector (ABFSS, WABS, WASBS) with parallel file processing"""

    def __init__(self, spark: SparkSession, secret_provider: SecretProvider,
                 logger: StructuredLogger, config: CollectorConfig, dbutils: Any):
        super().__init__(spark, secret_provider, logger, config)
        self.dbutils = dbutils

    def validate_connection(self, conn: StorageConnectionDetails) -> Tuple[bool, Optional[str]]:
        missing = [f for f in ('storage_name', 'container_name') if not getattr(conn, f, None)]
        return (False, f"Missing: {', '.join(missing)}") if missing else (True, None)

    def collect_metadata(self, conn: StorageConnectionDetails) -> Optional[DataFrame]:
        self.logger.info("Collecting storage metadata", source_id=conn.source_id)

        if conn.set_spark_config and conn.storage_access_key:
            self._configure_storage(conn)

        path = self._build_path(conn)
        files = self._list_files(path, conn.file_extension)

        if not files:
            self.logger.warning("No files found", path=path)
            return None

        metadata_rows = self._process_files(files, conn)
        if not metadata_rows:
            return None

        df = self.spark.createDataFrame(metadata_rows, FILE_METADATA_SCHEMA)
        sample_paths = [f['path'] for f in files[:self.config.SAMPLE_FILE_LIMIT]]
        null_long = F.lit(None).cast(LongType())

        df = df.select(
            "*",
            F.lit(sample_paths).cast(ArrayType(StringType())).alias("sample_file_paths"),
            F.col("file_size_bytes").alias("table_size"),
            null_long.alias("table_row_count")
        )

        if self.config.COMPUTE_ROW_COUNT and conn.file_extension:
            df = self._add_file_row_counts(df, conn)

        return self.enrich_metadata(df, conn)

    def _configure_storage(self, conn: StorageConnectionDetails) -> None:
        try:
            key = self.secret_provider.get_secret(
                conn.storage_access_key, scope=safe_get(conn.db_details, 'secret_scope')
            )
            storage_type = safe_get(conn.db_details, 'data_source_type', '')
            suffix = "dfs" if storage_type == DataSourceType.ABFSS_STORAGE.value else "blob"
            self.spark.conf.set(f"fs.azure.account.key.{conn.storage_name}.{suffix}.core.windows.net", key)
        except Exception as e:
            self.logger.warning(f"Failed to configure storage: {e}")

    def _build_path(self, conn: StorageConnectionDetails) -> str:
        storage_type = safe_get(conn.db_details, 'data_source_type', '')
        folder = conn.folder_path.strip('/') if conn.folder_path else ""

        if storage_type == DataSourceType.ABFSS_STORAGE.value:
            base = f"abfss://{conn.container_name}@{conn.storage_name}.dfs.core.windows.net"
        else:
            proto = "wasbs" if "WASBS" in storage_type else "wasb"
            base = f"{proto}://{conn.container_name}@{conn.storage_name}.blob.core.windows.net"

        return f"{base}/{folder}" if folder else base

    def _list_files(self, path: str, ext: Optional[str]) -> List[Dict]:
        try:
            files = []
            ext_suffix = f".{ext.lstrip('.')}" if ext else None
            limit = self.config.SAMPLE_FILE_LIMIT * 2

            for f in self.dbutils.fs.ls(path):
                if f.name.endswith('/'):
                    continue
                if ext_suffix and not f.name.endswith(ext_suffix):
                    continue

                mod_time = None
                if hasattr(f, 'modificationTime') and f.modificationTime:
                    try:
                        mod_time = datetime.fromtimestamp(f.modificationTime / 1000)
                    except (ValueError, OSError):
                        pass

                files.append({
                    'path': f.path,
                    'name': f.name,
                    'size': getattr(f, 'size', 0) or 0,
                    'modificationTime': mod_time
                })

                if _len(files) >= limit:
                    break

            return files
        except Exception as e:
            self.logger.error(f"Failed to list files: {e}", path=path)
            return []

    def _process_files(self, files: List[Dict], conn: StorageConnectionDetails) -> List[Dict]:
        sample_files = files[:self.config.SAMPLE_FILE_LIMIT]
        schema_cols = self._infer_schema(sample_files, conn)

        # Match ID columns case-insensitively
        id_cols_lower = {c.lower(): c for c in schema_cols}
        matched_ids = [id_cols_lower[c.lower()] for c in (conn.id_columns or []) if c.lower() in id_cols_lower]

        return [
            {
                "full_table_name": f['path'],
                "table_name": f['name'].rsplit('.', 1)[0] if '.' in f['name'] else f['name'],
                "id_columns": matched_ids,
                "partition_cols": [],
                "ct_enabled": 0,
                "source_schema": schema_cols,
                "column_count": _len(schema_cols),
                "file_size_bytes": f['size'],
                "file_last_modified": f['modificationTime']
            }
            for f in sample_files
        ]

    def _infer_schema(self, files: List[Dict], conn: StorageConnectionDetails) -> List[str]:
        if not files or not conn.file_extension:
            return []
        try:
            df = (self.spark.read
                  .format(conn.file_extension.lstrip('.'))
                  .options(**(conn.file_options or {}))
                  .load(files[0]['path']))
            return df.columns
        except Exception as e:
            self.logger.warning(f"Failed to infer schema: {e}")
            return []

    def _add_file_row_counts(self, df: DataFrame, conn: StorageConnectionDetails) -> DataFrame:
        self.logger.info("Computing file row counts", source_id=conn.source_id)
        paths = [r["full_table_name"] for r in df.select("full_table_name").collect()]

        counts = {}
        fmt = conn.file_extension.lstrip('.')
        opts = conn.file_options or {}

        for p in paths:
            try:
                file_df = self.spark.read.format(fmt).options(**opts).load(p)
                counts[p] = file_df.count()
            except Exception:
                counts[p] = None

        bc = self.spark.sparkContext.broadcast(counts)

        @F.udf(LongType())
        def get_count(path: str) -> Optional[int]:
            return bc.value.get(path)

        result = df.withColumn("table_row_count", get_count(F.col("full_table_name")))
        bc.destroy()
        return result


# ============================================================================
# CASSANDRA METADATA COLLECTOR
# ============================================================================

class CassandraMetadataCollector(MetadataCollector):
    """Cassandra metadata collector"""

    def validate_connection(self, conn: ConnectionDetails) -> Tuple[bool, Optional[str]]:
        if not safe_get(conn.db_details, 'keyspace_name'):
            return False, "Missing keyspace_name in db_details"
        return True, None

    def collect_metadata(self, conn: ConnectionDetails) -> Optional[DataFrame]:
        self.logger.info("Collecting Cassandra metadata", source_id=conn.source_id)
        keyspace = conn.db_details['keyspace_name']

        df = (self.spark.read
              .format("org.apache.spark.sql.cassandra")
              .option("keyspace", "system_schema")
              .option("table", "columns")
              .load()
              .filter(F.col("keyspace_name") == keyspace))

        df = df.persist(self.config.CACHE_STORAGE_LEVEL)
        null_long = F.lit(None).cast(LongType())

        try:
            processed = (
                df.groupBy("table_name")
                .agg(
                    F.array_except(
                        F.collect_list(F.when(F.col("kind").isin("partition_key", "clustering"), F.col("column_name"))),
                        F.array(F.lit(None).cast(StringType()))
                    ).alias("id_columns"),
                    F.collect_list("column_name").alias("source_schema"),
                    F.count("column_name").alias("column_count")
                )
                .select(
                    F.concat(F.lit(f"{keyspace}."), F.col("table_name")).alias("full_table_name"),
                    "table_name", "id_columns", "source_schema", "column_count",
                    F.array().cast(ArrayType(StringType())).alias("partition_cols"),
                    null_long.alias("table_row_count"),
                    null_long.alias("table_size"),
                    F.lit(0).alias("ct_enabled"),
                    F.lit(keyspace).alias("db_name")
                )
            )
            return self.enrich_metadata(processed, conn)
        finally:
            df.unpersist()


# ============================================================================
# REST API METADATA COLLECTOR
# ============================================================================

class RESTAPIMetadataCollector(MetadataCollector):
    """REST API metadata collector"""

    def __init__(self, spark: SparkSession, secret_provider: SecretProvider,
                 logger: StructuredLogger, config: CollectorConfig, http_client: HTTPClient):
        super().__init__(spark, secret_provider, logger, config)
        self.http_client = http_client

    def validate_connection(self, conn: RESTAPIConnectionDetails) -> Tuple[bool, Optional[str]]:
        if not conn.base_url:
            return False, "base_url is required"
        if not conn.auth_type:
            return False, "auth_type is required"
        return True, None

    def collect_metadata(self, conn: RESTAPIConnectionDetails) -> Optional[DataFrame]:
        self.logger.info("Collecting REST API metadata", source_id=conn.source_id)
        headers = dict(conn.headers) if conn.headers else {}
        scope = safe_get(conn.db_details, 'secret_scope')

        if conn.auth_type == "API_KEY" and conn.auth_key:
            headers["Authorization"] = f"Bearer {self.secret_provider.get_secret(conn.auth_key, scope=scope)}"
        elif conn.auth_type == "BASIC_AUTH" and conn.auth_key:
            import base64
            creds = self.secret_provider.get_secret(conn.auth_key, scope=scope)
            headers["Authorization"] = f"Basic {base64.b64encode(creds.encode()).decode()}"

        timeout = conn.timeout or self.config.REST_API_TIMEOUT
        rows = []

        for endpoint in conn.endpoints:
            try:
                url = f"{conn.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
                resp = self.http_client.get(url, headers, timeout)

                schema = []
                if isinstance(resp, dict):
                    schema = list(resp.keys())
                elif isinstance(resp, list) and resp and isinstance(resp[0], dict):
                    schema = list(resp[0].keys())

                rows.append({
                    "full_table_name": url,
                    "table_name": endpoint.strip('/').replace('/', '_') or "api_endpoint",
                    "id_columns": [], "partition_cols": [], "ct_enabled": 0,
                    "source_schema": schema, "column_count": _len(schema),
                    "table_row_count": None, "table_size": None,
                    "api_endpoint": url, "response_format": "JSON"
                })
            except Exception as e:
                self.logger.warning(f"Failed endpoint: {e}", endpoint=endpoint)

        if not rows:
            return None

        return self.enrich_metadata(self.spark.createDataFrame(rows, API_METADATA_SCHEMA), conn)


# ============================================================================
# COLLECTOR FACTORY - Registry-based (O(1) lookup)
# ============================================================================

class MetadataCollectorFactory:
    """Factory using registry pattern for O(1) collector lookup"""

    def __init__(self, spark: SparkSession, secret_provider: SecretProvider,
                 logger: StructuredLogger, config: CollectorConfig,
                 dbutils: Any, http_client: HTTPClient):
        self.spark = spark
        self.secret_provider = secret_provider
        self.logger = logger
        self.config = config
        self.dbutils = dbutils
        self.http_client = http_client
        self._cache: Dict[DataSourceType, MetadataCollector] = {}

    def get_collector(self, ds_type: DataSourceType) -> MetadataCollector:
        if ds_type not in self._cache:
            self._cache[ds_type] = self._create_collector(ds_type)
        return self._cache[ds_type]

    def _create_collector(self, ds_type: DataSourceType) -> MetadataCollector:
        # SQL databases
        if ds_type in (DataSourceType.SQLSERVER, DataSourceType.POSTGRESQL, DataSourceType.MARIADB):
            return SQLMetadataCollector(self.spark, self.secret_provider, self.logger, self.config)

        # Storage systems
        if ds_type in (DataSourceType.ABFSS_STORAGE, DataSourceType.WABS_STORAGE, DataSourceType.WASBS_SAS_STORAGE):
            return StorageMetadataCollector(self.spark, self.secret_provider, self.logger, self.config, self.dbutils)

        # Cassandra
        if ds_type == DataSourceType.CASSANDRA:
            return CassandraMetadataCollector(self.spark, self.secret_provider, self.logger, self.config)

        # REST API
        if ds_type == DataSourceType.REST_API:
            return RESTAPIMetadataCollector(self.spark, self.secret_provider, self.logger, self.config, self.http_client)

        raise ValueError(f"No collector for {ds_type}")


# ============================================================================
# METADATA ENRICHMENT - Functional, single-pass
# ============================================================================

def enrich_metadata_df(df: DataFrame, db_details: Dict[str, Any]) -> DataFrame:
    """Single-pass metadata enrichment using batched column operations"""
    if is_df_empty(df):
        return df

    include_list = safe_get(db_details, 'include_list', []) or []
    exclude_list = safe_get(db_details, 'exclude_list', []) or []
    append_only = safe_get(db_details, 'append_only_list', []) or []

    # Create array literals
    include_arr = F.array(*[F.lit(x) for x in include_list]) if include_list else F.array()
    exclude_arr = F.array(*[F.lit(x) for x in exclude_list]) if exclude_list else F.array()
    append_arr = F.array(*[F.lit(x) for x in append_only]) if append_only else F.array()

    # Compute is_included expression
    is_included = F.when(
        (F.size(include_arr) == 0) & (F.size(exclude_arr) == 0), F.lit(1)
    ).when(
        F.array_contains(include_arr, F.col("table_name")) & ~F.array_contains(exclude_arr, F.col("table_name")), F.lit(1)
    ).when(
        (F.size(include_arr) == 0) & ~F.array_contains(exclude_arr, F.col("table_name")), F.lit(1)
    ).otherwise(F.lit(0))

    # Compute is_append_only expression
    is_append_only = (
        F.when(F.array_contains(append_arr, F.col("table_name")), F.lit(1)).otherwise(F.lit(0))
        if append_only else F.lit(0)
    )

    # Transform arrays to snake_case
    id_cols_snake = F.when(
        F.col("id_columns").isNotNull(),
        F.transform(F.col("id_columns"), lambda x: to_snake_case_col(x))
    ).otherwise(F.array().cast(ArrayType(StringType())))

    schema_snake = F.when(
        F.col("source_schema").isNotNull(),
        F.transform(F.col("source_schema"), lambda x: to_snake_case_col(x))
    ).otherwise(F.array().cast(ArrayType(StringType())))

    return df.select(
        "*",
        to_snake_case_col(F.col("table_name")).alias("idp_db_name"),
        id_cols_snake.alias("idp_id_columns"),
        schema_snake.alias("idp_schema"),
        include_arr.cast(ArrayType(StringType())).alias("include_list"),
        exclude_arr.cast(ArrayType(StringType())).alias("exclude_list"),
        is_included.alias("is_included"),
        is_append_only.alias("is_append_only"),
        is_included.alias("is_active"),
        (is_included * 4 + F.col("ct_enabled") * 2 + is_append_only).cast(IntegerType()).alias("table_run_properties"),
        F.concat_ws("_", F.col("source_id"), F.col("table_name")).alias("id")
    )


# ============================================================================
# DUPLICATE HANDLER - Using window functions
# ============================================================================

class DuplicateHandler:
    """Efficient duplicate resolution using window functions"""

    def __init__(self, logger: StructuredLogger):
        self.logger = logger

    def resolve(self, df: DataFrame) -> DataFrame:
        if is_df_empty(df):
            return df

        from pyspark.sql.window import Window

        # Add count per id
        w = Window.partitionBy("id")
        df_with_count = df.withColumn("_dup_cnt", F.count("*").over(w))

        # Check if any duplicates exist (fast check)
        has_dups = df_with_count.filter(F.col("_dup_cnt") > 1).limit(1).count() > 0

        if not has_dups:
            return df_with_count.drop("_dup_cnt")

        self.logger.info("Resolving duplicate IDs")

        # Extract schema prefix from full_table_name (second-to-last part when split by .)
        schema_prefix = F.element_at(F.split(F.col("full_table_name"), "\\."), -2)

        # Resolve duplicates by adding schema prefix to table_name
        resolved = (
            df_with_count
            .withColumn("table_name",
                        F.when((F.col("_dup_cnt") > 1) & schema_prefix.isNotNull(),
                               F.concat_ws("_", schema_prefix, F.col("table_name")))
                        .otherwise(F.col("table_name")))
            .withColumn("id", F.concat_ws("_", F.col("source_id"), F.col("table_name")))
            .drop("_dup_cnt")
            .dropDuplicates(["id"])
        )
        return resolved


# ============================================================================
# ORCHESTRATOR
# ============================================================================

class MetadataCollectionOrchestrator:
    """Main orchestrator with parallel processing and retry logic"""

    def __init__(self, spark: SparkSession, secret_provider: SecretProvider,
                 df_reader: DataFrameReader, df_writer: DataFrameWriter,
                 dbutils: Any, http_client: HTTPClient,
                 config: CollectorConfig = None):
        self.spark = spark
        self.secret_provider = secret_provider
        self.df_reader = df_reader
        self.df_writer = df_writer
        self.config = config or CollectorConfig()
        self.logger = StructuredLogger(__name__, self.config.LOG_LEVEL)
        self.factory = MetadataCollectorFactory(
            spark, secret_provider, self.logger, self.config, dbutils, http_client
        )
        self.dup_handler = DuplicateHandler(self.logger)
        self.results: List[CollectionResult] = []

    def collect_all(self, connections: List[ConnectionDetails],
                    full_load: bool = False) -> Tuple[DataFrame, DataFrame]:
        """Collect metadata from all connections"""
        self.logger.info("Starting collection",
                         count=_len(connections),
                         mode="FULL" if full_load else "INCREMENTAL")
        self.results = []
        all_dfs: List[DataFrame] = []

        # Process in batches
        total_batches = (_len(connections) + self.config.BATCH_SIZE - 1) // self.config.BATCH_SIZE

        for i in range(0, _len(connections), self.config.BATCH_SIZE):
            batch = connections[i:i + self.config.BATCH_SIZE]
            batch_num = i // self.config.BATCH_SIZE + 1
            self.logger.info(f"Processing batch {batch_num}/{total_batches}")

            for result in self._process_batch(batch):
                self.results.append(result)
                if result.status == "Success" and result.metadata_df is not None:
                    all_dfs.append(result.metadata_df)

                icon = "✅" if result.status == "Success" else "❌"
                self.logger.info(
                    f"{icon} {result.source_id}",
                    status=result.status,
                    rows=result.row_count,
                    duration=f"{result.duration_seconds:.2f}s"
                )

        # Combine all DataFrames
        if all_dfs:
            combined = self._combine_dfs(all_dfs)
            combined = self.dup_handler.resolve(combined)
        else:
            combined = self.spark.createDataFrame([], METADATA_SCHEMA)

        return combined, self._create_summary()

    def _process_batch(self, batch: List[ConnectionDetails]) -> List[CollectionResult]:
        """Process a batch of connections in parallel"""
        results = []

        with ThreadPoolExecutor(max_workers=self.config.MAX_WORKERS) as executor:
            futures = {executor.submit(self._process_one, c): c for c in batch}

            for future in as_completed(futures):
                conn = futures[future]
                try:
                    results.append(future.result())
                except Exception as e:
                    self.logger.error(f"Unexpected error", source_id=conn.source_id, error=str(e))
                    results.append(CollectionResult(conn.source_id, "Failure", str(e)[:500]))

        return results

    def _process_one(self, conn: ConnectionDetails) -> CollectionResult:
        """Process single connection with retries"""
        start = time.time()
        last_error = None

        for attempt in range(1, self.config.MAX_RETRIES + 1):
            try:
                # Get data source type
                ds_type_str = get_data_source_type(conn.db_details or {})
                if not ds_type_str:
                    raise ValueError("data_source_type not found in db_details")

                # Match data source type (with partial matching)
                ds_type = None
                for t in DataSourceType:
                    if t.value in ds_type_str or ds_type_str in t.value:
                        ds_type = t
                        break
                if not ds_type:
                    raise ValueError(f"Unknown data_source_type: {ds_type_str}")

                # Get collector and validate
                collector = self.factory.get_collector(ds_type)
                is_valid, err = collector.validate_connection(conn)
                if not is_valid:
                    raise ValueError(f"Invalid connection: {err}")

                # Collect metadata
                df = collector.collect_metadata(conn)
                if is_df_empty(df):
                    raise ValueError("No metadata collected")

                # Enrich metadata
                df = enrich_metadata_df(df, conn.db_details or {})
                df = df.persist(self.config.CACHE_STORAGE_LEVEL)
                count = df.count()

                return CollectionResult(
                    conn.source_id, "Success", None, df, count,
                    time.time() - start, attempt - 1
                )

            except Exception as e:
                last_error = e
                self.logger.warning(
                    f"Attempt {attempt} failed",
                    source_id=conn.source_id,
                    error=str(e)[:200]
                )
                if attempt < self.config.MAX_RETRIES:
                    delay = _min(
                        self.config.RETRY_BASE_DELAY * (2 ** (attempt - 1)),
                        self.config.RETRY_MAX_DELAY
                    )
                    time.sleep(delay)

        return CollectionResult(
            conn.source_id, "Failure",
            str(last_error)[:500] if last_error else "Unknown error",
            None, 0, time.time() - start, self.config.MAX_RETRIES
        )

    def _combine_dfs(self, dfs: List[DataFrame]) -> DataFrame:
        """Combine multiple DataFrames with schema alignment"""
        if _len(dfs) == 1:
            return dfs[0]
        combined = reduce(
            lambda a, b: a.unionByName(b, allowMissingColumns=True),
            dfs
        )
        return combined.dropDuplicates(["id"])

    def _create_summary(self) -> DataFrame:
        """Create summary DataFrame from results"""
        rows = [
            (r.source_id, r.status, r.error_message, r.row_count,
             _round(r.duration_seconds, 2), r.retry_count)
            for r in self.results
        ]
        return self.spark.createDataFrame(rows, SUMMARY_SCHEMA)

    def write_results(self, df: DataFrame, table: str, full_load: bool = False,
                      merge_keys: Optional[List[str]] = None) -> None:
        """Write metadata results to target table"""
        if is_df_empty(df):
            self.logger.warning("No metadata to write")
            return

        row_count = df.count()
        self.logger.info(f"Writing results", rows=row_count, target=table)

        try:
            if full_load:
                self.df_writer.write_table(df, table, mode="overwrite", overwriteSchema="true")
            else:
                self.df_writer.merge_table(df, table, merge_keys or ["id"])
            self.logger.info(f"Successfully wrote to {table}")
        except Exception as e:
            self.logger.error(f"Write failed: {e}")
            raise


# ============================================================================
# IMPLEMENTATION CLASSES
# ============================================================================

class DatabricksSecretProvider(SecretProvider):
    """Databricks secret provider with caching"""

    def __init__(self, dbutils: Any, scope: str = "idp-secrets"):
        self.dbutils = dbutils
        self.default_scope = scope
        self._cache: Dict[str, str] = {}

    def get_secret(self, key: str, default: Optional[str] = None,
                   scope: Optional[str] = None) -> str:
        secret_scope = scope or self.default_scope
        cache_key = f"{secret_scope}:{key}"

        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            value = self.dbutils.secrets.get(scope=secret_scope, key=key)
            self._cache[cache_key] = value
            return value
        except Exception as e:
            if default is not None:
                return default
            raise ValueError(f"Secret not found: {key} in scope {secret_scope}. Error: {e}")


class DatabricksDataFrameWriter(DataFrameWriter):
    """Delta writer with merge support"""

    def __init__(self, spark: SparkSession):
        self.spark = spark

    def write_table(self, df: DataFrame, table: str, **kwargs) -> None:
        mode = kwargs.pop("mode", "overwrite")
        writer = df.write.format("delta").mode(mode)
        for k, v in kwargs.items():
            writer = writer.option(k, v)
        writer.saveAsTable(table)

    def merge_table(self, df: DataFrame, table: str, keys: List[str]) -> None:
        from delta.tables import DeltaTable

        if not self.spark.catalog.tableExists(table):
            self.write_table(df, table)
            return

        delta = DeltaTable.forName(self.spark, table)
        cond = " AND ".join(f"t.{k} = s.{k}" for k in keys)
        (delta.alias("t")
         .merge(df.alias("s"), cond)
         .whenMatchedUpdateAll()
         .whenNotMatchedInsertAll()
         .execute())


class DatabricksDataFrameReader(DataFrameReader):
    """Databricks DataFrame reader"""

    def __init__(self, spark: SparkSession):
        self.spark = spark

    def read_table(self, table: str) -> DataFrame:
        return self.spark.table(table)

    def table_exists(self, table: str) -> bool:
        try:
            return self.spark.catalog.tableExists(table)
        except Exception:
            return False


class RequestsHTTPClient(HTTPClient):
    """HTTP client with retry strategy"""

    def __init__(self):
        self.session = None
        try:
            import requests
            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry

            self.session = requests.Session()
            retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
            adapter = HTTPAdapter(max_retries=retry)
            self.session.mount("http://", adapter)
            self.session.mount("https://", adapter)
        except ImportError:
            pass

    def get(self, url: str, headers: Dict[str, str], timeout: int) -> Dict:
        if not self.session:
            raise RuntimeError("requests library not available")
        r = self.session.get(url, headers=headers, timeout=timeout)
        r.raise_for_status()
        return r.json()


# ============================================================================
# CONNECTION PARSER
# ============================================================================

def parse_connections(config_df: DataFrame) -> List[ConnectionDetails]:
    """Parse connection configurations from DataFrame"""
    connections = []

    # Filter active sources
    active = config_df.filter(F.col("is_active").cast("boolean") == True).collect()

    for row in active:
        try:
            # Parse db_details
            db_details = row["db_details"]
            if isinstance(db_details, str):
                try:
                    db_details = json.loads(db_details)
                except json.JSONDecodeError:
                    db_details = {}
            elif db_details is None:
                db_details = {}
            elif hasattr(db_details, 'asDict'):
                db_details = db_details.asDict()
            elif not isinstance(db_details, dict):
                db_details = {}

            # Get data source type
            ds_type = get_row_value(row, 'data_source_type', '') or get_data_source_type(db_details)
            db_details['data_source_type'] = ds_type
            ds_upper = ds_type.upper()

            # Base connection params
            base = {
                "source_id": row["id"],
                "catalog_name": row["catalog_name"],
                "table_name": get_row_value(row, "table_name"),
                "metadata_enabled": get_row_value(row, "metadata_enabled", True),
                "is_active": row["is_active"],
                "db_details": db_details
            }

            # Create appropriate connection type
            if any(x in ds_upper for x in ("STORAGE", "ABFSS", "WABS", "BLOB", "ADLS", "S3", "GCS")):
                conn = StorageConnectionDetails(
                    **base,
                    storage_name=db_details.get('storage_name', ''),
                    container_name=db_details.get('container_name', ''),
                    storage_access_key=db_details.get('storage_access_key', ''),
                    folder_path=db_details.get('folder_path', ''),
                    file_extension=db_details.get('file_extension'),
                    file_options=db_details.get('file_options') or {},
                    id_columns=db_details.get('id_columns') or []
                )
            elif ds_upper in ("REST_API", "RESTAPI", "REST", "API", "HTTP", "HTTPS"):
                conn = RESTAPIConnectionDetails(
                    **base,
                    base_url=db_details.get('base_url', ''),
                    auth_type=db_details.get('auth_type', ''),
                    auth_key=db_details.get('auth_key'),
                    endpoints=db_details.get('endpoints') or [],
                    headers=db_details.get('headers') or {},
                    timeout=db_details.get('timeout', 30)
                )
            else:
                conn = SQLConnectionDetails(
                    **base,
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
            source_id = get_row_value(row, 'id', 'unknown')
            print(f"Warning: Failed to parse connection {source_id}: {e}")

    return connections


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main_notebook_execution(dbutils, spark: SparkSession) -> str:
    """Main execution function for Databricks notebook"""
    import os

    # Get environment configuration
    env = os.environ.get("ENV", "qa")
    default_scope = os.environ.get("SECRET_SCOPE", "idp-secrets")

    # Setup widgets
    dbutils.widgets.text("full_load", "False", "Full Load?")
    dbutils.widgets.text("job_run_id", "", "Job Run ID")
    dbutils.widgets.text("compute_row_count", "False", "Compute Row Counts?")
    dbutils.widgets.text("secret_scope", default_scope, "Secret Scope Name")

    # Parse widget values
    full_load = dbutils.widgets.get("full_load").strip().lower() == "true"
    compute_row_count = dbutils.widgets.get("compute_row_count").strip().lower() == "true"
    secret_scope = dbutils.widgets.get("secret_scope").strip() or default_scope

    print(f"🔧 Config: env={env}, scope={secret_scope}, full_load={full_load}, row_count={compute_row_count}")

    # Initialize configuration and components
    config = CollectorConfig().with_row_count(compute_row_count)
    secret_provider = DatabricksSecretProvider(dbutils, scope=secret_scope)
    df_reader = DatabricksDataFrameReader(spark)
    df_writer = DatabricksDataFrameWriter(spark)
    http_client = RequestsHTTPClient()

    # Load and parse connections
    config_table = f"{env}_idp.config.metadata_source_connection_details"
    print(f"   Config Table: {config_table}")
    connections = parse_connections(df_reader.read_table(config_table))

    if not connections:
        print("⚠️ No active connections found")
        return "SUCCESS"

    # Execute collection
    orchestrator = MetadataCollectionOrchestrator(
        spark, secret_provider, df_reader, df_writer, dbutils, http_client, config
    )

    metadata_df, summary_df = orchestrator.collect_all(connections, full_load)

    # Display summary
    print("=" * 70)
    print("METADATA COLLECTION SUMMARY")
    print("=" * 70)
    summary_df.show(truncate=False)

    success = summary_df.filter(F.col("status") == "Success").count()
    failure = summary_df.filter(F.col("status") == "Failure").count()
    print(f"\nTotal: {_len(connections)}, Success: {success}, Failed: {failure}")
    print("=" * 70)

    # Write results
    if not is_df_empty(metadata_df):
        target = f"{env}_idp.config.meta_data_registry"
        orchestrator.write_results(metadata_df, target, full_load)
        print(f"✅ Metadata written to {target}")
    else:
        print("⚠️ No metadata to write")

    # Return status
    if failure == 0:
        return "SUCCESS"
    elif success > 0:
        return "PARTIAL_SUCCESS"
    else:
        return "FAILURE"


# COMMAND ----------

# Execute when run as notebook
if __name__ == "__main__":
    status = main_notebook_execution(dbutils, spark)
    print(f"\n🏁 Final Status: {status}")
