# Databricks notebook source
# MAGIC %md
# MAGIC # IDP Metadata Collector Framework
# MAGIC 
# MAGIC This framework collects metadata about every configured data-source in
# MAGIC `qa_idp.config.metadata_source_connection_details` and produces a canonical
# MAGIC `meta_data_registry` dataset for downstream pipelines and audits.
# MAGIC
# MAGIC ## Supported Data Sources
# MAGIC - **JDBC**: SQLSERVER, POSTGRESQL, MARIADB
# MAGIC - **NoSQL**: CASSANDRA
# MAGIC - **Azure Storage**: ABFSS_STORAGE, WABS_STORAGE, WASBS_SAS_STORAGE
# MAGIC - **API**: REST_API
# MAGIC
# MAGIC ## Design Principles
# MAGIC - SOLID principles for maintainability and extensibility
# MAGIC - Strategy Pattern for different data source types
# MAGIC - Factory Pattern for collector instantiation
# MAGIC - Template Method for common processing flow

# COMMAND ----------
# MAGIC %run ./DPCommonFunctions

# COMMAND ----------
# DBTITLE 1,Imports and Dependencies
import logging
import re
import sys
import hashlib
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Type, Union
from uuid import uuid4

import pyspark.sql.functions as F
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.types import (
    ArrayType,
    BooleanType,
    IntegerType,
    LongType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

# COMMAND ----------
# DBTITLE 1,Logger Setup

def setup_logger(name: str, log_level: str = "INFO") -> logging.Logger:
    """
    Configure and return a logger with consistent formatting.
    
    Args:
        name: Logger name (typically __name__)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid adding duplicate handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False
    
    return logger


logger = setup_logger(__name__, "INFO")

# COMMAND ----------
# DBTITLE 1,Enums and Constants

class DataSourceType(str, Enum):
    """Enumeration of supported data source types."""
    SQLSERVER = "SQLSERVER"
    POSTGRESQL = "POSTGRESQL"
    MARIADB = "MARIADB"
    CASSANDRA = "CASSANDRA"
    ABFSS_STORAGE = "ABFSS_STORAGE"
    WABS_STORAGE = "WABS_STORAGE"
    WASBS_SAS_STORAGE = "WASBS_SAS_STORAGE"
    REST_API = "REST_API"


class CollectorCategory(str, Enum):
    """Categories of metadata collectors."""
    JDBC = "JDBC"
    NOSQL = "NOSQL"
    STORAGE = "STORAGE"
    API = "API"


# Mapping of data source types to their categories
SOURCE_TYPE_CATEGORY: Dict[DataSourceType, CollectorCategory] = {
    DataSourceType.SQLSERVER: CollectorCategory.JDBC,
    DataSourceType.POSTGRESQL: CollectorCategory.JDBC,
    DataSourceType.MARIADB: CollectorCategory.JDBC,
    DataSourceType.CASSANDRA: CollectorCategory.NOSQL,
    DataSourceType.ABFSS_STORAGE: CollectorCategory.STORAGE,
    DataSourceType.WABS_STORAGE: CollectorCategory.STORAGE,
    DataSourceType.WASBS_SAS_STORAGE: CollectorCategory.STORAGE,
    DataSourceType.REST_API: CollectorCategory.API,
}


# Processing configuration
class ProcessingConfig:
    """Configuration constants for processing."""
    BATCH_SIZE: int = 25
    MAX_RETRIES: int = 3
    MAX_WORKERS: int = 5
    RETRY_DELAY_SECONDS: float = 1.0
    COMPUTE_ROW_COUNT: bool = False  # Default: skip expensive COUNT(*)
    MAX_SAMPLE_FILES: int = 5  # Max sample file paths to include

# COMMAND ----------
# DBTITLE 1,Data Models

@dataclass
class DBDetails:
    """Database connection details model."""
    db_host: Optional[str] = None
    db_name: Optional[str] = None
    db_port: Optional[str] = None
    user_name: Optional[str] = None
    password_key: Optional[str] = None
    table_schema: Optional[List[str]] = None
    exclude_list: Optional[List[str]] = None
    include_list: Optional[List[str]] = None
    append_only_list: Optional[List[str]] = None
    id_columns: Optional[List[str]] = None
    is_ct_enabled: bool = False
    table_name_prefix: Optional[str] = None


@dataclass
class StorageDetails:
    """Azure storage connection details model."""
    storage_name: Optional[str] = None
    container_name: Optional[str] = None
    storage_access_key: Optional[str] = None
    folder_path: Optional[str] = None
    file_extension: Optional[str] = None
    file_options: Optional[Dict[str, str]] = None
    checkpoint_location: Optional[str] = None
    set_spark_config: bool = False
    id_columns: Optional[List[str]] = None
    exclude_list: Optional[List[str]] = None
    include_list: Optional[List[str]] = None
    append_only_list: Optional[List[str]] = None


@dataclass
class CassandraDetails:
    """Cassandra connection details model."""
    user_name: Optional[str] = None
    password_key: Optional[str] = None
    client_id_key: Optional[str] = None
    client_secret_key: Optional[str] = None
    keyspace_name: Optional[str] = None
    secure_connect_bundle_path: Optional[str] = None
    exclude_list: Optional[List[str]] = None
    include_list: Optional[List[str]] = None
    append_only_list: Optional[List[str]] = None
    id_columns: Optional[List[str]] = None


@dataclass
class RESTAPIDetails:
    """REST API connection details model."""
    api_parameter_id: Optional[str] = None
    api_url: Optional[str] = None
    api_method: Optional[str] = None
    select_exprs: Optional[List[str]] = None
    exclude_list: Optional[List[str]] = None
    include_list: Optional[List[str]] = None
    append_only_list: Optional[List[str]] = None
    id_columns: Optional[List[str]] = None


@dataclass
class DataSourceConfig:
    """
    Main configuration model for a data source.
    
    This model represents a row from the metadata_source_connection_details table.
    """
    id: str
    data_source_type: str
    catalog_name: str
    table_name: Optional[str]
    metadata_enabled: bool
    db_details: Dict[str, Any]
    is_active: bool
    idp_cdc_hash: Optional[str] = None
    idp_created_date: Optional[datetime] = None
    idp_modified_date: Optional[datetime] = None
    
    def get_db_details(self) -> DBDetails:
        """Parse db_details as DBDetails."""
        return DBDetails(**{k: v for k, v in self.db_details.items() if k in DBDetails.__dataclass_fields__})
    
    def get_storage_details(self) -> StorageDetails:
        """Parse db_details as StorageDetails."""
        return StorageDetails(**{k: v for k, v in self.db_details.items() if k in StorageDetails.__dataclass_fields__})
    
    def get_cassandra_details(self) -> CassandraDetails:
        """Parse db_details as CassandraDetails."""
        return CassandraDetails(**{k: v for k, v in self.db_details.items() if k in CassandraDetails.__dataclass_fields__})
    
    def get_api_details(self) -> RESTAPIDetails:
        """Parse db_details as RESTAPIDetails."""
        return RESTAPIDetails(**{k: v for k, v in self.db_details.items() if k in RESTAPIDetails.__dataclass_fields__})


@dataclass
class MetadataResult:
    """
    Result model for metadata collection.
    
    Contains all the fields required for the meta_data_registry output.
    """
    full_table_name: str
    table_name: str
    id_columns: List[str]
    partition_cols: List[str]
    ct_enabled: int
    source_id: str
    catalog_name: str
    entity_name: Optional[str]
    db_name: str
    include_list: List[str]
    exclude_list: List[str]
    is_included: int
    is_append_only: int
    is_active: int
    table_run_properties: int
    idp_db_name: str
    idp_id_columns: List[str]
    column_count: int
    source_schema: List[str]
    idp_schema: List[str]
    column_details: List[Dict[str, Any]]
    table_row_count: Optional[int] = None
    file_size_bytes: Optional[int] = None
    file_last_modified: Optional[datetime] = None
    sample_file_paths: Optional[List[str]] = None

    @property
    def id(self) -> str:
        """Generate unique ID for this metadata row."""
        return f"{self.source_id}_{self.table_name}"


@dataclass
class CollectionResult:
    """Result of a single source collection operation."""
    source_id: str
    success: bool
    dataframe: Optional[DataFrame] = None
    error_message: Optional[str] = None
    tables_collected: int = 0
    duration_seconds: float = 0.0

# COMMAND ----------
# DBTITLE 1,Helper Functions

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
        
    Examples:
        >>> to_snake_case("CamelCase")
        'camel_case'
        >>> to_snake_case("already_snake")
        'already_snake'
        >>> to_snake_case("FontReplacement")
        'font_replacement'
    """
    if not name:
        return ""
    
    # Handle common abbreviations by inserting underscore before them
    # e.g., "XMLParser" -> "XML_Parser" -> "xml_parser"
    s = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', name)
    
    # Handle transition from lowercase/digit to uppercase
    # e.g., "camelCase" -> "camel_Case"
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


def compute_cdc_hash(data: Dict[str, Any]) -> str:
    """
    Compute a CDC hash for metadata change detection.
    
    Args:
        data: Dictionary of data to hash
        
    Returns:
        SHA256 hash string
    """
    # Sort keys for consistent ordering
    sorted_data = str(sorted(data.items()))
    return hashlib.sha256(sorted_data.encode()).hexdigest()


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
    
    Args:
        table_name: Name of the table to check
        include_list: List of tables to include
        exclude_list: List of tables to exclude
        
    Returns:
        True if table should be included
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
    
    Args:
        is_included: 0 or 1
        ct_enabled: 0 or 1
        is_append_only: 0 or 1
        
    Returns:
        Combined properties as integer
    """
    return int(f"{is_included}{ct_enabled}{is_append_only}")


def get_column_details(df: DataFrame) -> List[Dict[str, Any]]:
    """
    Extract column details from a DataFrame schema.
    
    Args:
        df: DataFrame to extract schema from
        
    Returns:
        List of column detail dictionaries
    """
    details = []
    for field in df.schema.fields:
        details.append({
            "name": field.name,
            "data_type": str(field.dataType),
            "nullable": field.nullable,
            "metadata": dict(field.metadata) if field.metadata else {}
        })
    return details


# Register UDFs for Spark
def register_udfs(spark: SparkSession) -> Dict[str, Any]:
    """Register helper functions as Spark UDFs."""
    to_snake_case_udf = F.udf(to_snake_case, StringType())
    to_snake_case_list_udf = F.udf(to_snake_case_list, ArrayType(StringType()))
    
    return {
        "to_snake_case": to_snake_case_udf,
        "to_snake_case_list": to_snake_case_list_udf
    }

# COMMAND ----------
# DBTITLE 1,Output Schema Definition

# Define the output schema for metadata registry
METADATA_REGISTRY_SCHEMA = StructType([
    StructField("full_table_name", StringType(), False),
    StructField("table_name", StringType(), False),
    StructField("id_columns", ArrayType(StringType()), True),
    StructField("partition_cols", ArrayType(StringType()), True),
    StructField("ct_enabled", IntegerType(), False),
    StructField("source_id", StringType(), False),
    StructField("catalog_name", StringType(), False),
    StructField("entity_name", StringType(), True),
    StructField("db_name", StringType(), True),
    StructField("id", StringType(), False),
    StructField("include_list", ArrayType(StringType()), True),
    StructField("exclude_list", ArrayType(StringType()), True),
    StructField("is_included", IntegerType(), False),
    StructField("is_append_only", IntegerType(), False),
    StructField("is_active", IntegerType(), False),
    StructField("table_run_properties", IntegerType(), False),
    StructField("idp_db_name", StringType(), False),
    StructField("idp_id_columns", ArrayType(StringType()), True),
    StructField("idp_cdc_hash", StringType(), True),
    StructField("idp_created_date", TimestampType(), True),
    StructField("idp_modified_date", TimestampType(), True),
    StructField("table_row_count", LongType(), True),
    StructField("column_count", IntegerType(), True),
    StructField("source_schema", ArrayType(StringType()), True),
    StructField("idp_schema", ArrayType(StringType()), True),
    StructField("column_details", ArrayType(
        StructType([
            StructField("name", StringType(), True),
            StructField("data_type", StringType(), True),
            StructField("nullable", BooleanType(), True),
            StructField("metadata", StringType(), True)
        ])
    ), True),
    StructField("file_size_bytes", LongType(), True),
    StructField("file_last_modified", TimestampType(), True),
    StructField("sample_file_paths", ArrayType(StringType()), True),
])

# COMMAND ----------
# DBTITLE 1,Abstract Base Collector (Strategy Pattern)

class BaseMetadataCollector(ABC):
    """
    Abstract base class for metadata collectors.
    
    Implements the Template Method pattern for common processing flow
    while allowing subclasses to customize specific steps.
    
    Attributes:
        config: Data source configuration
        spark: SparkSession instance
        logger: Logger instance
    """
    
    def __init__(
        self,
        config: DataSourceConfig,
        spark: SparkSession,
        compute_row_count: bool = False
    ):
        """
        Initialize the collector.
        
        Args:
            config: Data source configuration
            spark: SparkSession instance
            compute_row_count: Whether to compute row counts
        """
        self.config = config
        self.spark = spark
        self.compute_row_count = compute_row_count
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._udfs = register_udfs(spark)
    
    @abstractmethod
    def _get_connection_url(self) -> str:
        """Build the connection URL for this data source."""
        pass
    
    @abstractmethod
    def _fetch_raw_metadata(self) -> Optional[DataFrame]:
        """
        Fetch raw metadata from the source.
        
        Returns:
            DataFrame with at least: full_table_name, table_name, id_columns, 
            partition_cols, ct_enabled
        """
        pass
    
    @abstractmethod
    def _get_include_list(self) -> List[str]:
        """Get the include list from configuration."""
        pass
    
    @abstractmethod
    def _get_exclude_list(self) -> List[str]:
        """Get the exclude list from configuration."""
        pass
    
    @abstractmethod
    def _get_append_only_list(self) -> List[str]:
        """Get the append-only list from configuration."""
        pass
    
    @abstractmethod
    def _get_configured_id_columns(self) -> Optional[List[str]]:
        """Get configured ID columns from configuration."""
        pass
    
    def _get_db_name(self) -> str:
        """Get the database name, potentially from secrets."""
        details = self.config.db_details
        db_name = details.get("db_name", "")
        if not db_name:
            # Try to get from secret if db_name key is provided
            db_name_key = details.get("db_name_key")
            if db_name_key:
                db_name = get_secret_value(db_name_key, "")
        return db_name or ""
    
    def _enrich_metadata(self, raw_df: DataFrame) -> DataFrame:
        """
        Enrich raw metadata with computed columns.
        
        This is the core transformation that adds all the required columns
        to the output schema.
        
        Args:
            raw_df: Raw metadata DataFrame
            
        Returns:
            Enriched DataFrame with all required columns
        """
        incl = self._get_include_list()
        excl = self._get_exclude_list()
        append_only = self._get_append_only_list()
        
        # Build base enrichment
        enriched = (
            raw_df
            .withColumn("source_id", F.lit(self.config.id))
            .withColumn("catalog_name", F.upper(F.lit(self.config.catalog_name)))
            .withColumn("entity_name", F.lit(self.config.table_name))
            .withColumn("db_name", F.lit(self._get_db_name()))
            .withColumn("id", F.concat_ws("_", F.col("source_id"), F.col("table_name")))
        )
        
        # Add include/exclude lists
        enriched = enriched.withColumn(
            "include_list",
            F.array(*[F.lit(x) for x in incl]) if incl else F.array().cast(ArrayType(StringType()))
        ).withColumn(
            "exclude_list",
            F.array(*[F.lit(x) for x in excl]) if excl else F.array().cast(ArrayType(StringType()))
        )
        
        # Compute is_included using SQL expression for efficiency
        enriched = enriched.withColumn(
            "is_included",
            F.expr("""
                CASE 
                    WHEN size(include_list) = 0 AND size(exclude_list) = 0 THEN 1
                    WHEN array_contains(exclude_list, table_name) THEN 0
                    WHEN size(include_list) = 0 THEN 1
                    WHEN array_contains(include_list, table_name) THEN 1
                    ELSE 0
                END
            """).cast(IntegerType())
        )
        
        # Add append-only handling
        append_only_array = F.array(*[F.lit(x) for x in append_only]) if append_only else F.array().cast(ArrayType(StringType()))
        enriched = enriched.withColumn(
            "_append_only_list", append_only_array
        ).withColumn(
            "is_append_only",
            F.when(F.array_contains(F.col("_append_only_list"), F.col("table_name")), 1).otherwise(0).cast(IntegerType())
        ).drop("_append_only_list")
        
        # Add is_active and table_run_properties
        enriched = enriched.withColumn(
            "ct_enabled", F.col("ct_enabled").cast(IntegerType())
        ).withColumn(
            "is_active", F.col("is_included").cast(IntegerType())
        ).withColumn(
            "table_run_properties",
            F.concat(
                F.col("is_included").cast(StringType()),
                F.col("ct_enabled").cast(StringType()),
                F.col("is_append_only").cast(StringType())
            ).cast(IntegerType())
        )
        
        # Add IDP columns (snake_case versions)
        enriched = enriched.withColumn(
            "idp_db_name", self._udfs["to_snake_case"](F.col("table_name"))
        ).withColumn(
            "idp_id_columns", self._udfs["to_snake_case_list"](F.col("id_columns"))
        )
        
        # Add schema columns if not already present
        if "source_schema" not in enriched.columns:
            enriched = enriched.withColumn("source_schema", F.array().cast(ArrayType(StringType())))
        
        if "idp_schema" not in enriched.columns:
            enriched = enriched.withColumn(
                "idp_schema", 
                self._udfs["to_snake_case_list"](F.col("source_schema"))
            )
        
        # Add timestamps and CDC hash
        current_ts = F.current_timestamp()
        enriched = enriched.withColumn(
            "idp_created_date", current_ts
        ).withColumn(
            "idp_modified_date", current_ts
        )
        
        # Compute CDC hash based on key columns
        enriched = enriched.withColumn(
            "idp_cdc_hash",
            F.sha2(
                F.concat_ws("|",
                    F.col("full_table_name"),
                    F.col("table_name"),
                    F.concat_ws(",", F.col("id_columns")),
                    F.concat_ws(",", F.col("source_schema")),
                    F.col("ct_enabled").cast(StringType())
                ),
                256
            )
        )
        
        # Add nullable columns with defaults if not present
        if "table_row_count" not in enriched.columns:
            enriched = enriched.withColumn("table_row_count", F.lit(None).cast(LongType()))
        
        if "column_count" not in enriched.columns:
            enriched = enriched.withColumn(
                "column_count",
                F.when(F.col("source_schema").isNotNull(), F.size(F.col("source_schema"))).otherwise(0)
            )
        
        if "column_details" not in enriched.columns:
            enriched = enriched.withColumn("column_details", F.array().cast(ArrayType(
                StructType([
                    StructField("name", StringType()),
                    StructField("data_type", StringType()),
                    StructField("nullable", BooleanType()),
                    StructField("metadata", StringType())
                ])
            )))
        
        if "file_size_bytes" not in enriched.columns:
            enriched = enriched.withColumn("file_size_bytes", F.lit(None).cast(LongType()))
        
        if "file_last_modified" not in enriched.columns:
            enriched = enriched.withColumn("file_last_modified", F.lit(None).cast(TimestampType()))
        
        if "sample_file_paths" not in enriched.columns:
            enriched = enriched.withColumn("sample_file_paths", F.array().cast(ArrayType(StringType())))
        
        return enriched
    
    def _apply_table_name_prefix(self, df: DataFrame) -> DataFrame:
        """Apply table name prefix if configured."""
        details = self.config.db_details
        prefix = details.get("table_name_prefix")
        
        if prefix:
            df = df.withColumn(
                "table_name",
                F.concat_ws("_", F.lit(prefix), F.col("table_name"))
            ).withColumn(
                "id",
                F.concat_ws("_", F.col("source_id"), F.col("table_name"))
            ).withColumn(
                "idp_db_name",
                self._udfs["to_snake_case"](F.col("table_name"))
            )
        
        return df
    
    def collect(self) -> CollectionResult:
        """
        Execute the metadata collection process.
        
        This is the template method that orchestrates the collection flow.
        
        Returns:
            CollectionResult with success status and collected data
        """
        import time
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting metadata collection for {self.config.id}")
            
            # Step 1: Fetch raw metadata
            raw_df = self._fetch_raw_metadata()
            
            if raw_df is None or raw_df.isEmpty():
                self.logger.warning(f"No metadata found for {self.config.id}")
                return CollectionResult(
                    source_id=self.config.id,
                    success=False,
                    error_message="No tables/files found",
                    duration_seconds=time.time() - start_time
                )
            
            # Step 2: Enrich metadata
            enriched_df = self._enrich_metadata(raw_df)
            
            # Step 3: Apply prefix if configured
            final_df = self._apply_table_name_prefix(enriched_df)
            
            # Step 4: Cache for counting
            final_df = final_df.cache()
            row_count = final_df.count()
            
            self.logger.info(f"Successfully collected {row_count} tables for {self.config.id}")
            
            return CollectionResult(
                source_id=self.config.id,
                success=True,
                dataframe=final_df,
                tables_collected=row_count,
                duration_seconds=time.time() - start_time
            )
            
        except Exception as e:
            self.logger.exception(f"Error collecting metadata for {self.config.id}")
            return CollectionResult(
                source_id=self.config.id,
                success=False,
                error_message=str(e)[:500],
                duration_seconds=time.time() - start_time
            )

# COMMAND ----------
# DBTITLE 1,JDBC Collectors (SQL Server, PostgreSQL, MariaDB)

class JDBCMetadataCollector(BaseMetadataCollector):
    """
    Base collector for JDBC data sources.
    
    Handles SQL Server, PostgreSQL, and MariaDB databases.
    """
    
    def _get_include_list(self) -> List[str]:
        return self.config.db_details.get("include_list", []) or []
    
    def _get_exclude_list(self) -> List[str]:
        return self.config.db_details.get("exclude_list", []) or []
    
    def _get_append_only_list(self) -> List[str]:
        return self.config.db_details.get("append_only_list", []) or []
    
    def _get_configured_id_columns(self) -> Optional[List[str]]:
        return self.config.db_details.get("id_columns")
    
    @abstractmethod
    def _get_catalog_query(self, table_schema: Optional[List[str]], include_ct: bool) -> str:
        """Get the catalog query for this database type."""
        pass
    
    @abstractmethod
    def _get_jdbc_driver(self) -> str:
        """Get the JDBC driver class name."""
        pass
    
    def _get_connection_url(self) -> str:
        """Build JDBC connection URL."""
        details = self.config.db_details
        db_host = details.get("db_host", "")
        db_port = details.get("db_port", "")
        db_name = details.get("db_name", "")
        
        # Database-specific URL format
        db_type = self.config.data_source_type
        
        if db_type == DataSourceType.SQLSERVER.value:
            return f"jdbc:sqlserver://{db_host}:{db_port};databaseName={db_name}"
        elif db_type == DataSourceType.POSTGRESQL.value:
            return f"jdbc:postgresql://{db_host}:{db_port}/{db_name}"
        elif db_type == DataSourceType.MARIADB.value:
            return f"jdbc:mariadb://{db_host}:{db_port}/{db_name}"
        else:
            return f"jdbc:{db_type.lower()}://{db_host}:{db_port}/{db_name}"
    
    def _get_jdbc_properties(self) -> Dict[str, str]:
        """Get JDBC connection properties."""
        details = self.config.db_details
        user = details.get("user_name", "")
        password_key = details.get("password_key", "")
        
        # Get password from secrets - NEVER log this!
        password = get_secret_value(password_key, "")
        
        return {
            "user": user,
            "password": password,
            "driver": self._get_jdbc_driver()
        }
    
    def _fetch_raw_metadata(self) -> Optional[DataFrame]:
        """Fetch table metadata from the JDBC source."""
        try:
            details = self.config.db_details
            table_schema = details.get("table_schema", [])
            include_ct = details.get("is_ct_enabled", False)
            
            url = self._get_connection_url()
            properties = self._get_jdbc_properties()
            query = self._get_catalog_query(table_schema, include_ct)
            
            self.logger.info(f"Fetching catalog for {self.config.id}")
            
            # Read the catalog query result
            catalog_df = (
                self.spark.read
                .jdbc(url=url, table=f"({query}) AS catalog_query", properties=properties)
                .cache()
            )
            
            if catalog_df.isEmpty():
                return None
            
            # Aggregate by table - filter out null PK columns
            aggs = [
                F.first(F.col("FULL_TABLE_NAME")).alias("full_table_name"),
                # Only collect non-null PK column names
                F.collect_set(
                    F.when(F.col("PK_COLUMN_NAME").isNotNull(), F.col("PK_COLUMN_NAME"))
                ).alias("id_columns_raw"),
                F.collect_list(F.col("COLUMN_NAME")).alias("source_schema"),
                F.first(F.when(F.col("PARTITION_COLS") == "true", F.lit("true"))
                       .otherwise(F.lit("false"))).alias("partition_flag"),
            ]
            
            if include_ct:
                aggs.append(
                    F.first(F.when(F.col("CT_ENABLED") == "true", 1).otherwise(0)).alias("ct_enabled")
                )
            
            grouped = (
                catalog_df
                .groupBy("TABLE_NAME")
                .agg(*aggs)
            )
            
            # Filter nulls from id_columns and build final result
            grouped = grouped.withColumn(
                "id_columns",
                F.expr("filter(id_columns_raw, x -> x IS NOT NULL)")
            )
            
            # Add ct_enabled column if not present
            if not include_ct:
                grouped = grouped.withColumn("ct_enabled", F.lit(0))
            
            # Build final result
            result = grouped.select(
                F.col("full_table_name"),
                F.col("TABLE_NAME").alias("table_name"),
                F.col("id_columns"),
                F.array(F.col("partition_flag")).alias("partition_cols"),
                F.col("ct_enabled").cast(IntegerType()).alias("ct_enabled"),
                F.col("source_schema"),
                self._udfs["to_snake_case_list"](F.col("source_schema")).alias("idp_schema"),
                F.size(F.col("source_schema")).alias("column_count")
            )
            
            # Use configured ID columns if provided and source has none
            configured_ids = self._get_configured_id_columns()
            if configured_ids:
                result = result.withColumn(
                    "id_columns",
                    F.when(F.size(F.col("id_columns")) == 0,
                           F.array(*[F.lit(c) for c in configured_ids]))
                    .otherwise(F.col("id_columns"))
                )
            
            return result
            
        except Exception as e:
            self.logger.exception(f"Error fetching JDBC metadata for {self.config.id}")
            raise


class SQLServerCollector(JDBCMetadataCollector):
    """Collector for SQL Server databases."""
    
    def _get_jdbc_driver(self) -> str:
        return "com.microsoft.sqlserver.jdbc.SQLServerDriver"
    
    def _get_catalog_query(self, table_schema: Optional[List[str]], include_ct: bool) -> str:
        """Build SQL Server catalog query."""
        schema_filter = ""
        if table_schema:
            schemas = ", ".join([f"'{s}'" for s in table_schema])
            schema_filter = f"AND t.TABLE_SCHEMA IN ({schemas})"
        
        ct_column = ""
        ct_join = ""
        if include_ct:
            ct_column = ", CASE WHEN ct.object_id IS NOT NULL THEN 'true' ELSE 'false' END AS CT_ENABLED"
            ct_join = """
                LEFT JOIN sys.change_tracking_tables ct 
                    ON OBJECT_ID(QUOTENAME(t.TABLE_SCHEMA) + '.' + QUOTENAME(t.TABLE_NAME)) = ct.object_id
            """
        
        return f"""
            SELECT 
                t.TABLE_SCHEMA + '.' + t.TABLE_NAME AS FULL_TABLE_NAME,
                t.TABLE_NAME,
                c.COLUMN_NAME,
                c.ORDINAL_POSITION,
                CASE WHEN pk.COLUMN_NAME IS NOT NULL THEN c.COLUMN_NAME END AS PK_COLUMN_NAME,
                CASE WHEN pk.COLUMN_NAME IS NOT NULL THEN 'true' ELSE 'false' END AS PARTITION_COLS
                {ct_column}
            FROM INFORMATION_SCHEMA.TABLES t
            INNER JOIN INFORMATION_SCHEMA.COLUMNS c 
                ON t.TABLE_NAME = c.TABLE_NAME AND t.TABLE_SCHEMA = c.TABLE_SCHEMA
            LEFT JOIN (
                SELECT ku.TABLE_NAME, ku.COLUMN_NAME, ku.TABLE_SCHEMA
                FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
                INNER JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE ku
                    ON tc.CONSTRAINT_NAME = ku.CONSTRAINT_NAME
                WHERE tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
            ) pk ON c.TABLE_NAME = pk.TABLE_NAME 
                AND c.COLUMN_NAME = pk.COLUMN_NAME 
                AND c.TABLE_SCHEMA = pk.TABLE_SCHEMA
            {ct_join}
            WHERE t.TABLE_TYPE = 'BASE TABLE'
            {schema_filter}
            ORDER BY t.TABLE_NAME, c.ORDINAL_POSITION
        """


class PostgreSQLCollector(JDBCMetadataCollector):
    """Collector for PostgreSQL databases."""
    
    def _get_jdbc_driver(self) -> str:
        return "org.postgresql.Driver"
    
    def _get_catalog_query(self, table_schema: Optional[List[str]], include_ct: bool) -> str:
        """Build PostgreSQL catalog query."""
        schema_filter = ""
        if table_schema:
            schemas = ", ".join([f"'{s}'" for s in table_schema])
            schema_filter = f"AND t.table_schema IN ({schemas})"
        
        return f"""
            SELECT 
                t.table_schema || '.' || t.table_name AS FULL_TABLE_NAME,
                t.table_name AS TABLE_NAME,
                c.column_name AS COLUMN_NAME,
                c.ordinal_position AS ORDINAL_POSITION,
                CASE WHEN pk.column_name IS NOT NULL THEN c.column_name END AS PK_COLUMN_NAME,
                CASE WHEN pk.column_name IS NOT NULL THEN 'true' ELSE 'false' END AS PARTITION_COLS,
                'false' AS CT_ENABLED
            FROM information_schema.tables t
            INNER JOIN information_schema.columns c 
                ON t.table_name = c.table_name AND t.table_schema = c.table_schema
            LEFT JOIN (
                SELECT kcu.table_name, kcu.column_name, kcu.table_schema
                FROM information_schema.table_constraints tc
                INNER JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name 
                    AND tc.table_schema = kcu.table_schema
                WHERE tc.constraint_type = 'PRIMARY KEY'
            ) pk ON c.table_name = pk.table_name 
                AND c.column_name = pk.column_name 
                AND c.table_schema = pk.table_schema
            WHERE t.table_type = 'BASE TABLE'
            {schema_filter}
            ORDER BY t.table_name, c.ordinal_position
        """


class MariaDBCollector(JDBCMetadataCollector):
    """Collector for MariaDB/MySQL databases."""
    
    def _get_jdbc_driver(self) -> str:
        return "org.mariadb.jdbc.Driver"
    
    def _get_catalog_query(self, table_schema: Optional[List[str]], include_ct: bool) -> str:
        """Build MariaDB catalog query."""
        schema_filter = ""
        if table_schema:
            schemas = ", ".join([f"'{s}'" for s in table_schema])
            schema_filter = f"AND t.TABLE_SCHEMA IN ({schemas})"
        
        return f"""
            SELECT 
                CONCAT(t.TABLE_SCHEMA, '.', t.TABLE_NAME) AS FULL_TABLE_NAME,
                t.TABLE_NAME,
                c.COLUMN_NAME,
                c.ORDINAL_POSITION,
                CASE WHEN c.COLUMN_KEY = 'PRI' THEN c.COLUMN_NAME END AS PK_COLUMN_NAME,
                CASE WHEN c.COLUMN_KEY = 'PRI' THEN 'true' ELSE 'false' END AS PARTITION_COLS,
                'false' AS CT_ENABLED
            FROM INFORMATION_SCHEMA.TABLES t
            INNER JOIN INFORMATION_SCHEMA.COLUMNS c 
                ON t.TABLE_NAME = c.TABLE_NAME AND t.TABLE_SCHEMA = c.TABLE_SCHEMA
            WHERE t.TABLE_TYPE = 'BASE TABLE'
            {schema_filter}
            ORDER BY t.TABLE_NAME, c.ORDINAL_POSITION
        """

# COMMAND ----------
# DBTITLE 1,Cassandra Collector

class CassandraCollector(BaseMetadataCollector):
    """Collector for Cassandra databases."""
    
    def _get_connection_url(self) -> str:
        """Cassandra uses secure connect bundle, not URL."""
        return self.config.db_details.get("secure_connect_bundle_path", "")
    
    def _get_include_list(self) -> List[str]:
        return self.config.db_details.get("include_list", []) or []
    
    def _get_exclude_list(self) -> List[str]:
        return self.config.db_details.get("exclude_list", []) or []
    
    def _get_append_only_list(self) -> List[str]:
        return self.config.db_details.get("append_only_list", []) or []
    
    def _get_configured_id_columns(self) -> Optional[List[str]]:
        return self.config.db_details.get("id_columns")
    
    def _fetch_raw_metadata(self) -> Optional[DataFrame]:
        """Fetch table metadata from Cassandra."""
        try:
            details = self.config.db_details
            keyspace = details.get("keyspace_name", "")
            bundle_path = details.get("secure_connect_bundle_path", "")
            
            # Get credentials from secrets
            client_id = get_secret_value(details.get("client_id_key", ""), "")
            client_secret = get_secret_value(details.get("client_secret_key", ""), "")
            
            self.logger.info(f"Connecting to Cassandra keyspace: {keyspace}")
            
            # Configure Spark Cassandra connector
            spark_conf = {
                "spark.cassandra.connection.config.cloud.path": bundle_path,
                "spark.cassandra.auth.username": client_id,
                "spark.cassandra.auth.password": client_secret
            }
            
            for key, value in spark_conf.items():
                self.spark.conf.set(key, value)
            
            # Query system schema for tables
            tables_df = (
                self.spark.read
                .format("org.apache.spark.sql.cassandra")
                .options(table="tables", keyspace="system_schema")
                .load()
                .filter(F.col("keyspace_name") == keyspace)
                .select("table_name")
            )
            
            if tables_df.isEmpty():
                return None
            
            # Get column info for each table
            columns_df = (
                self.spark.read
                .format("org.apache.spark.sql.cassandra")
                .options(table="columns", keyspace="system_schema")
                .load()
                .filter(F.col("keyspace_name") == keyspace)
            )
            
            # Join and aggregate
            result = (
                tables_df.alias("t")
                .join(columns_df.alias("c"), F.col("t.table_name") == F.col("c.table_name"))
                .groupBy(F.col("t.table_name"))
                .agg(
                    F.first(F.concat(F.lit(keyspace), F.lit("."), F.col("t.table_name"))).alias("full_table_name"),
                    # Only collect partition key columns (non-null)
                    F.collect_set(
                        F.when(F.col("c.kind") == "partition_key", F.col("c.column_name"))
                    ).alias("pk_columns_raw"),
                    F.collect_list(F.col("c.column_name")).alias("source_schema")
                )
                # Filter out nulls from pk_columns
                .withColumn(
                    "id_columns",
                    F.expr("filter(pk_columns_raw, x -> x IS NOT NULL)")
                )
                .select(
                    F.col("full_table_name"),
                    F.col("t.table_name").alias("table_name"),
                    F.col("id_columns"),
                    F.array().cast(ArrayType(StringType())).alias("partition_cols"),
                    F.lit(0).cast(IntegerType()).alias("ct_enabled"),
                    F.col("source_schema"),
                    self._udfs["to_snake_case_list"](F.col("source_schema")).alias("idp_schema"),
                    F.size(F.col("source_schema")).alias("column_count")
                )
            )
            
            return result
            
        except Exception as e:
            self.logger.exception(f"Error fetching Cassandra metadata for {self.config.id}")
            raise

# COMMAND ----------
# DBTITLE 1,Storage Collectors (ABFSS, WABS, WASBS_SAS)

class StorageMetadataCollector(BaseMetadataCollector):
    """
    Base collector for Azure Storage data sources.
    
    Handles ABFSS, WABS, and WASBS_SAS storage types.
    """
    
    def _get_include_list(self) -> List[str]:
        return self.config.db_details.get("include_list", []) or []
    
    def _get_exclude_list(self) -> List[str]:
        return self.config.db_details.get("exclude_list", []) or []
    
    def _get_append_only_list(self) -> List[str]:
        return self.config.db_details.get("append_only_list", []) or []
    
    def _get_configured_id_columns(self) -> Optional[List[str]]:
        return self.config.db_details.get("id_columns")
    
    @abstractmethod
    def _get_connection_url(self) -> str:
        """Build the storage connection URL."""
        pass
    
    def _configure_spark_for_storage(self) -> None:
        """Configure Spark for accessing the storage."""
        details = self.config.db_details
        
        if not details.get("set_spark_config", False):
            return
        
        storage_name = details.get("storage_name", "")
        storage_key = details.get("storage_access_key", "")
        
        if storage_key:
            # Get key from secrets
            actual_key = get_secret_value(storage_key, "")
            if actual_key:
                # Set appropriate config based on storage type
                source_type = self.config.data_source_type
                
                if source_type == DataSourceType.ABFSS_STORAGE.value:
                    self.spark.conf.set(
                        f"fs.azure.account.key.{storage_name}.dfs.core.windows.net",
                        actual_key
                    )
                elif source_type in [DataSourceType.WABS_STORAGE.value, DataSourceType.WASBS_SAS_STORAGE.value]:
                    self.spark.conf.set(
                        f"fs.azure.account.key.{storage_name}.blob.core.windows.net",
                        actual_key
                    )
    
    def _get_file_extension(self) -> str:
        """Get the file extension to filter for."""
        return self.config.db_details.get("file_extension", "").lower()
    
    def _get_file_options(self) -> Dict[str, str]:
        """Get file read options."""
        return self.config.db_details.get("file_options", {}) or {}
    
    def _fetch_raw_metadata(self) -> Optional[DataFrame]:
        """Fetch metadata for files in storage."""
        try:
            # Configure Spark for storage access
            self._configure_spark_for_storage()
            
            storage_path = self._get_connection_url()
            file_ext = self._get_file_extension()
            file_options = self._get_file_options()
            configured_ids = self._get_configured_id_columns() or []
            
            self.logger.info(f"Listing files at: {storage_path}")
            
            try:
                files = dbutils.fs.ls(storage_path)
            except Exception as e:
                self.logger.error(f"Cannot list storage path: {storage_path}")
                raise
            
            rows = []
            sample_paths = []
            
            for f in files:
                file_name = f.name.lower()
                
                # Check if it's a directory (ends with /)
                is_directory = f.name.endswith("/") or (hasattr(f, 'isDir') and callable(f.isDir) and f.isDir())
                
                # Filter by extension if specified
                if file_ext and not file_name.rstrip("/").endswith(f".{file_ext}"):
                    # Check if it's a directory that might contain files
                    if is_directory:
                        try:
                            sub_files = dbutils.fs.ls(f.path)
                            for sf in sub_files:
                                if sf.name.lower().endswith(f".{file_ext}"):
                                    self._process_file(
                                        sf, file_ext, file_options, configured_ids, 
                                        rows, sample_paths
                                    )
                        except Exception:
                            continue
                    continue
                
                # Skip directories
                if is_directory:
                    continue
                
                self._process_file(f, file_ext, file_options, configured_ids, rows, sample_paths)
            
            if not rows:
                return None
            
            # Create DataFrame from collected rows
            schema = StructType([
                StructField("full_table_name", StringType(), True),
                StructField("table_name", StringType(), True),
                StructField("id_columns", ArrayType(StringType()), True),
                StructField("partition_cols", ArrayType(StringType()), True),
                StructField("ct_enabled", IntegerType(), True),
                StructField("source_schema", ArrayType(StringType()), True),
                StructField("column_count", IntegerType(), True),
                StructField("file_size_bytes", LongType(), True),
                StructField("file_last_modified", TimestampType(), True),
                StructField("sample_file_paths", ArrayType(StringType()), True),
            ])
            
            result = self.spark.createDataFrame(rows, schema)
            
            # Add IDP schema
            result = result.withColumn(
                "idp_schema",
                self._udfs["to_snake_case_list"](F.col("source_schema"))
            )
            
            return result
            
        except Exception as e:
            self.logger.exception(f"Error fetching storage metadata for {self.config.id}")
            raise
    
    def _process_file(
        self, 
        file_info, 
        file_ext: str, 
        file_options: Dict[str, str],
        configured_ids: List[str],
        rows: List[Dict],
        sample_paths: List[str]
    ) -> None:
        """Process a single file and extract its metadata."""
        try:
            file_path = file_info.path
            file_name = file_info.name
            
            # Try to read schema with zero rows
            try:
                sample_df = (
                    self.spark.read
                    .format(file_ext or "parquet")
                    .options(**file_options)
                    .load(file_path)
                    .limit(0)
                )
                columns = sample_df.columns
                column_details = get_column_details(sample_df)
            except Exception as e:
                self.logger.warning(f"Cannot read schema from {file_path}: {e}")
                columns = []
                column_details = []
            
            # Match configured ID columns
            columns_lower = {c.lower(): c for c in columns}
            id_cols = []
            for id_col in configured_ids:
                if id_col.lower() in columns_lower:
                    id_cols.append(columns_lower[id_col.lower()])
            
            # Extract table name from file name (without extension)
            table_name = file_name.split(".")[0] if "." in file_name else file_name
            
            # Get file modification time if available
            mod_time = None
            try:
                if hasattr(file_info, 'modificationTime') and file_info.modificationTime:
                    mod_time = datetime.fromtimestamp(file_info.modificationTime / 1000)
            except Exception:
                pass
            
            # Add to sample paths
            if len(sample_paths) < ProcessingConfig.MAX_SAMPLE_FILES:
                sample_paths.append(file_path)
            
            # Get file size safely
            file_size = None
            try:
                if hasattr(file_info, 'size'):
                    file_size = file_info.size
            except Exception:
                pass
            
            rows.append({
                "full_table_name": file_path,
                "table_name": table_name,
                "id_columns": id_cols,
                "partition_cols": [],
                "ct_enabled": 0,
                "source_schema": columns,
                "column_count": len(columns),
                "file_size_bytes": file_size,
                "file_last_modified": mod_time,
                "sample_file_paths": list(sample_paths)
            })
            
        except Exception as e:
            self.logger.warning(f"Error processing file {file_info.path}: {e}")


class ABFSSStorageCollector(StorageMetadataCollector):
    """Collector for ABFSS (Azure Data Lake Storage Gen2) sources."""
    
    def _get_connection_url(self) -> str:
        """Build ABFSS storage URL."""
        details = self.config.db_details
        storage_name = details.get("storage_name", "")
        container = details.get("container_name", "")
        folder_path = details.get("folder_path", "")
        
        base_url = f"abfss://{container}@{storage_name}.dfs.core.windows.net"
        
        if folder_path:
            return f"{base_url}/{folder_path.strip('/')}"
        return base_url


class WABSStorageCollector(StorageMetadataCollector):
    """Collector for WABS (Azure Blob Storage) sources."""
    
    def _get_connection_url(self) -> str:
        """Build WABS storage URL."""
        details = self.config.db_details
        storage_name = details.get("storage_name", "")
        container = details.get("container_name", "")
        folder_path = details.get("folder_path", "")
        
        base_url = f"wasbs://{container}@{storage_name}.blob.core.windows.net"
        
        if folder_path:
            return f"{base_url}/{folder_path.strip('/')}"
        return base_url


class WASBSSASStorageCollector(StorageMetadataCollector):
    """Collector for WASBS with SAS token sources."""
    
    def _configure_spark_for_storage(self) -> None:
        """Configure Spark with SAS token."""
        details = self.config.db_details
        
        if not details.get("set_spark_config", False):
            return
        
        storage_name = details.get("storage_name", "")
        sas_key = details.get("storage_access_key", "")
        
        if sas_key:
            # Get SAS token from secrets
            sas_token = get_secret_value(sas_key, "")
            if sas_token:
                self.spark.conf.set(
                    f"fs.azure.sas.{details.get('container_name', '')}.{storage_name}.blob.core.windows.net",
                    sas_token
                )
    
    def _get_connection_url(self) -> str:
        """Build WASBS storage URL with SAS."""
        details = self.config.db_details
        storage_name = details.get("storage_name", "")
        container = details.get("container_name", "")
        folder_path = details.get("folder_path", "")
        
        base_url = f"wasbs://{container}@{storage_name}.blob.core.windows.net"
        
        if folder_path:
            return f"{base_url}/{folder_path.strip('/')}"
        return base_url

# COMMAND ----------
# DBTITLE 1,REST API Collector

class RESTAPICollector(BaseMetadataCollector):
    """Collector for REST API data sources."""
    
    def _get_connection_url(self) -> str:
        """Get API URL from secrets."""
        url_key = self.config.db_details.get("api_url", "")
        return get_secret_value(url_key, url_key)
    
    def _get_include_list(self) -> List[str]:
        return self.config.db_details.get("include_list", []) or []
    
    def _get_exclude_list(self) -> List[str]:
        return self.config.db_details.get("exclude_list", []) or []
    
    def _get_append_only_list(self) -> List[str]:
        return self.config.db_details.get("append_only_list", []) or []
    
    def _get_configured_id_columns(self) -> Optional[List[str]]:
        return self.config.db_details.get("id_columns")
    
    def _fetch_raw_metadata(self) -> Optional[DataFrame]:
        """Fetch metadata for REST API endpoint."""
        try:
            details = self.config.db_details
            select_exprs = details.get("select_exprs", [])
            
            # Extract column names from select expressions
            columns = []
            for expr in (select_exprs or []):
                # Parse "source_col AS alias" pattern (case-insensitive)
                expr_upper = expr.upper()
                if " AS " in expr_upper:
                    # Find position of " AS " in original string
                    as_pos = expr_upper.find(" AS ")
                    alias = expr[as_pos + 4:].strip()
                    columns.append(alias)
                else:
                    columns.append(expr.strip())
            
            # Create a single row for this API endpoint
            table_name = self.config.table_name or self.config.id
            
            row = {
                "full_table_name": f"api://{self._get_connection_url()}/{table_name}",
                "table_name": table_name,
                "id_columns": self._get_configured_id_columns() or [],
                "partition_cols": [],
                "ct_enabled": 0,
                "source_schema": columns,
                "column_count": len(columns)
            }
            
            schema = StructType([
                StructField("full_table_name", StringType(), True),
                StructField("table_name", StringType(), True),
                StructField("id_columns", ArrayType(StringType()), True),
                StructField("partition_cols", ArrayType(StringType()), True),
                StructField("ct_enabled", IntegerType(), True),
                StructField("source_schema", ArrayType(StringType()), True),
                StructField("column_count", IntegerType(), True),
            ])
            
            result = self.spark.createDataFrame([row], schema)
            
            # Add IDP schema
            result = result.withColumn(
                "idp_schema",
                self._udfs["to_snake_case_list"](F.col("source_schema"))
            )
            
            return result
            
        except Exception as e:
            self.logger.exception(f"Error fetching REST API metadata for {self.config.id}")
            raise

# COMMAND ----------
# DBTITLE 1,Collector Factory (Factory Pattern)

class CollectorFactory:
    """
    Factory for creating metadata collectors.
    
    Uses the Factory Pattern to instantiate the appropriate collector
    based on the data source type.
    """
    
    # Registry of collectors by data source type
    _collectors: Dict[str, Type[BaseMetadataCollector]] = {
        DataSourceType.SQLSERVER.value: SQLServerCollector,
        DataSourceType.POSTGRESQL.value: PostgreSQLCollector,
        DataSourceType.MARIADB.value: MariaDBCollector,
        DataSourceType.CASSANDRA.value: CassandraCollector,
        DataSourceType.ABFSS_STORAGE.value: ABFSSStorageCollector,
        DataSourceType.WABS_STORAGE.value: WABSStorageCollector,
        DataSourceType.WASBS_SAS_STORAGE.value: WASBSSASStorageCollector,
        DataSourceType.REST_API.value: RESTAPICollector,
    }
    
    @classmethod
    def register_collector(
        cls, 
        source_type: str, 
        collector_class: Type[BaseMetadataCollector]
    ) -> None:
        """
        Register a new collector for a data source type.
        
        This allows extending the framework with new data source types
        without modifying existing code (Open/Closed Principle).
        
        Args:
            source_type: The data source type identifier
            collector_class: The collector class to use
        """
        cls._collectors[source_type] = collector_class
    
    @classmethod
    def create_collector(
        cls,
        config: DataSourceConfig,
        spark: SparkSession,
        compute_row_count: bool = False
    ) -> Optional[BaseMetadataCollector]:
        """
        Create a collector for the given configuration.
        
        Args:
            config: Data source configuration
            spark: SparkSession instance
            compute_row_count: Whether to compute row counts
            
        Returns:
            Appropriate collector instance, or None if unsupported
        """
        collector_class = cls._collectors.get(config.data_source_type)
        
        if collector_class is None:
            logger.warning(f"No collector registered for type: {config.data_source_type}")
            return None
        
        return collector_class(config, spark, compute_row_count)
    
    @classmethod
    def get_supported_types(cls) -> List[str]:
        """Get list of supported data source types."""
        return list(cls._collectors.keys())

# COMMAND ----------
# DBTITLE 1,Duplicate Handler

def check_duplicate_and_update(df: DataFrame) -> DataFrame:
    """
    Handle duplicate IDs by prefixing table names with schema.
    
    When multiple rows produce identical IDs (source_id + table_name),
    this function resolves duplicates by prepending the schema/catalog
    to the table name.
    
    Args:
        df: DataFrame with potential duplicate IDs
        
    Returns:
        DataFrame with unique IDs
    """
    try:
        # Find duplicate IDs
        dup_ids = [
            row["id"]
            for row in (
                df.groupBy("id")
                .count()
                .filter(F.col("count") > 1)
                .select("id")
                .collect()
            )
        ]
        
        if not dup_ids:
            return df
        
        logger.info(f"Resolving {len(dup_ids)} duplicate IDs")
        
        # Split into non-duplicates and duplicates
        non_dup_df = df.filter(~F.col("id").isin(dup_ids))
        
        # For duplicates, prefix table_name with schema from full_table_name
        dup_df = (
            df.filter(F.col("id").isin(dup_ids))
            .withColumn(
                "table_name",
                F.concat_ws(
                    "_",
                    # Extract schema from full_table_name (second-to-last part when split by .)
                    F.element_at(F.split(F.col("full_table_name"), "\\."), -2),
                    F.col("table_name")
                )
            )
            .withColumn(
                "id",
                F.concat_ws("_", F.col("source_id"), F.col("table_name"))
            )
            .withColumn(
                "idp_db_name",
                F.lower(F.regexp_replace(
                    F.regexp_replace(F.col("table_name"), "([a-z])([A-Z])", "$1_$2"),
                    "[^a-zA-Z0-9]+", "_"
                ))
            )
        )
        
        return non_dup_df.unionByName(dup_df, allowMissingColumns=True).distinct()
        
    except Exception as e:
        logger.exception("Error in duplicate handling")
        raise

# COMMAND ----------
# DBTITLE 1,Metadata Orchestrator

class MetadataOrchestrator:
    """
    Orchestrates the metadata collection process.
    
    Handles:
    - Batch processing of data sources
    - Parallel execution with thread pool
    - Retry logic for failed collections
    - Result aggregation and deduplication
    - Summary report generation
    """
    
    def __init__(
        self,
        spark: SparkSession,
        batch_size: int = ProcessingConfig.BATCH_SIZE,
        max_workers: int = ProcessingConfig.MAX_WORKERS,
        max_retries: int = ProcessingConfig.MAX_RETRIES,
        compute_row_count: bool = ProcessingConfig.COMPUTE_ROW_COUNT
    ):
        """
        Initialize the orchestrator.
        
        Args:
            spark: SparkSession instance
            batch_size: Number of sources to process per batch
            max_workers: Maximum parallel workers
            max_retries: Maximum retry attempts per source
            compute_row_count: Whether to compute row counts
        """
        self.spark = spark
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.max_retries = max_retries
        self.compute_row_count = compute_row_count
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Results tracking
        self.results: List[DataFrame] = []
        self.summary_rows: List[Tuple[str, str, Optional[str], float]] = []
    
    def _process_single_source(
        self, 
        config: DataSourceConfig
    ) -> Tuple[str, Optional[DataFrame], Optional[str], float]:
        """
        Process a single data source with retry logic.
        
        Args:
            config: Data source configuration
            
        Returns:
            Tuple of (source_id, dataframe, error_message, duration)
        """
        import time
        first_error: Optional[str] = None
        total_duration = 0.0
        
        for attempt in range(self.max_retries):
            try:
                self.logger.info(
                    f"Processing {config.id} — attempt {attempt + 1}/{self.max_retries}"
                )
                
                # Create appropriate collector
                collector = CollectorFactory.create_collector(
                    config, self.spark, self.compute_row_count
                )
                
                if collector is None:
                    return (
                        config.id, 
                        None, 
                        f"Unsupported data source type: {config.data_source_type}",
                        0.0
                    )
                
                # Execute collection
                result = collector.collect()
                total_duration += result.duration_seconds
                
                if result.success:
                    return (config.id, result.dataframe, None, total_duration)
                else:
                    if first_error is None:
                        first_error = result.error_message
                    
            except Exception as e:
                if first_error is None:
                    first_error = str(e)[:500]
                self.logger.exception(
                    f"Attempt {attempt + 1}/{self.max_retries} failed for {config.id}"
                )
            
            # Wait before retry
            if attempt < self.max_retries - 1:
                time.sleep(ProcessingConfig.RETRY_DELAY_SECONDS * (attempt + 1))
        
        self.logger.error(f"All attempts exhausted for {config.id} — FAILED")
        return (config.id, None, first_error, total_duration)
    
    def process_sources(
        self, 
        configs: List[DataSourceConfig]
    ) -> Tuple[List[DataFrame], DataFrame]:
        """
        Process all data sources and return results.
        
        Args:
            configs: List of data source configurations
            
        Returns:
            Tuple of (list of result DataFrames, summary DataFrame)
        """
        self.results = []
        self.summary_rows = []
        
        total_sources = len(configs)
        self.logger.info(f"Starting metadata collection for {total_sources} sources")
        
        # Process in batches
        for batch_start in range(0, total_sources, self.batch_size):
            batch = configs[batch_start:batch_start + self.batch_size]
            batch_num = (batch_start // self.batch_size) + 1
            total_batches = (total_sources + self.batch_size - 1) // self.batch_size
            
            self.logger.info(
                f"Processing batch {batch_num}/{total_batches} "
                f"({len(batch)} sources)"
            )
            
            # Execute batch in parallel
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_config = {
                    executor.submit(self._process_single_source, cfg): cfg
                    for cfg in batch
                }
                
                for future in as_completed(future_to_config):
                    config = future_to_config[future]
                    source_id, df, error, duration = future.result()
                    
                    if df is not None:
                        self.results.append(df)
                        self.summary_rows.append((source_id, "Success", None, duration))
                        self.logger.info(f"✅ SUCCESS {source_id} ({duration:.2f}s)")
                    else:
                        self.summary_rows.append((source_id, "Failure", error, duration))
                        self.logger.error(f"❌ FAILED {source_id}: {error}")
        
        # Build summary DataFrame
        summary_schema = StructType([
            StructField("source_id", StringType(), False),
            StructField("status", StringType(), False),
            StructField("error_message", StringType(), True),
            StructField("duration_seconds", LongType(), True)
        ])
        
        summary_df = self.spark.createDataFrame(
            [(r[0], r[1], r[2], int(r[3])) for r in self.summary_rows],
            summary_schema
        )
        
        return self.results, summary_df
    
    def aggregate_results(self, results: List[DataFrame]) -> Optional[DataFrame]:
        """
        Aggregate all result DataFrames into one.
        
        Args:
            results: List of result DataFrames
            
        Returns:
            Combined DataFrame, or None if no results
        """
        if not results:
            return None
        
        if len(results) == 1:
            return results[0]
        
        # Union all results
        combined = results[0]
        for df in results[1:]:
            combined = combined.unionByName(df, allowMissingColumns=True)
        
        return combined
    
    def print_summary(self, summary_df: DataFrame) -> None:
        """Print collection summary statistics."""
        success_count = summary_df.filter(F.col("status") == "Success").count()
        failure_count = summary_df.filter(F.col("status") == "Failure").count()
        total_duration = summary_df.agg(F.sum("duration_seconds")).collect()[0][0] or 0
        
        print("=" * 70)
        print("METADATA COLLECTION SUMMARY")
        print("=" * 70)
        print(f"Total sources processed : {success_count + failure_count}")
        print(f"Successful              : {success_count}")
        print(f"Failed                  : {failure_count}")
        print(f"Total duration          : {total_duration}s")
        print("=" * 70)
        
        if failure_count > 0:
            print("\nFailed sources:")
            failed = summary_df.filter(F.col("status") == "Failure").collect()
            for row in failed:
                print(f"  - {row['source_id']}: {row['error_message']}")
            print()

# COMMAND ----------
# DBTITLE 1,Configuration Loader

def load_source_configurations(
    spark: SparkSession,
    config_table: str = "qa_idp.config.metadata_source_connection_details",
    source_types: Optional[List[str]] = None,
    active_only: bool = True,
    metadata_enabled_only: bool = False
) -> List[DataSourceConfig]:
    """
    Load data source configurations from the configuration table.
    
    Args:
        spark: SparkSession instance
        config_table: Fully qualified table name for configurations
        source_types: Optional list of source types to filter
        active_only: Whether to filter for active sources only
        metadata_enabled_only: Whether to filter for metadata_enabled sources only
        
    Returns:
        List of DataSourceConfig objects
    """
    import json
    
    logger.info(f"Loading configurations from {config_table}")
    
    # Read configuration table
    cfg_df = read_table(config_table)
    
    # Apply filters
    if source_types:
        cfg_df = cfg_df.filter(F.col("data_source_type").isin(source_types))
    
    if active_only:
        cfg_df = cfg_df.filter(F.col("is_active") == True)
    
    if metadata_enabled_only:
        cfg_df = cfg_df.filter(F.col("metadata_enabled") == True)
    
    # Collect and convert to DataSourceConfig objects
    configs = []
    for row in cfg_df.orderBy("id").collect():
        row_dict = row.asDict()
        
        # Parse db_details JSON string
        db_details_str = row_dict.get("db_details", "{}")
        try:
            # Handle case where db_details might already be a dict
            if isinstance(db_details_str, dict):
                db_details = db_details_str
            else:
                db_details = json.loads(db_details_str or "{}")
        except (json.JSONDecodeError, TypeError):
            logger.warning(f"Failed to parse db_details for {row_dict.get('id')}, using empty dict")
            db_details = {}
        
        config = DataSourceConfig(
            id=row_dict["id"],
            data_source_type=row_dict["data_source_type"],
            catalog_name=row_dict["catalog_name"],
            table_name=row_dict.get("table_name"),
            metadata_enabled=row_dict.get("metadata_enabled", False),
            db_details=db_details,
            is_active=row_dict.get("is_active", True),
            idp_cdc_hash=row_dict.get("idp_cdc_hash"),
            idp_created_date=row_dict.get("idp_created_date"),
            idp_modified_date=row_dict.get("idp_modified_date")
        )
        configs.append(config)
    
    logger.info(f"Loaded {len(configs)} source configurations")
    return configs

# COMMAND ----------
# DBTITLE 1,Main Execution

# Widget definitions
dbutils.widgets.text("full_load", "False", "Full Load?")
dbutils.widgets.text("job_run_id", "", "Job Run ID")
dbutils.widgets.text("compute_row_count", "False", "Compute Row Counts?")
dbutils.widgets.text("source_types", "", "Source Types (comma-separated, empty for all)")

# Parse widget values
full_load = dbutils.widgets.get("full_load").strip().capitalize() == "True"
run_id = dbutils.widgets.get("job_run_id").strip() or str(uuid4())
compute_row_count = dbutils.widgets.get("compute_row_count").strip().capitalize() == "True"
source_types_input = dbutils.widgets.get("source_types").strip()

# Parse source types
source_types = None
if source_types_input:
    source_types = [s.strip() for s in source_types_input.split(",")]

logger.info(f"Job Mode: {'FULL' if full_load else 'INCREMENTAL'}")
logger.info(f"Run ID: {run_id}")
logger.info(f"Compute Row Counts: {compute_row_count}")
logger.info(f"Source Types Filter: {source_types or 'ALL'}")

# COMMAND ----------
# DBTITLE 1,Load Configurations

try:
    # Get supported source types from factory
    supported_types = CollectorFactory.get_supported_types()
    
    # If source types specified, validate them
    if source_types:
        invalid_types = set(source_types) - set(supported_types)
        if invalid_types:
            logger.warning(f"Unsupported source types will be skipped: {invalid_types}")
        source_types = [t for t in source_types if t in supported_types]
    else:
        source_types = supported_types
    
    # Load configurations
    configs = load_source_configurations(
        spark,
        config_table="qa_idp.config.metadata_source_connection_details",
        source_types=source_types,
        active_only=True
    )
    
    if not configs:
        logger.warning("No active configurations found")
        dbutils.notebook.exit("SUCCESS - No configurations to process")
        
except Exception as e:
    logger.exception("Failed to load configurations")
    dbutils.notebook.exit("FAILED")

# COMMAND ----------
# DBTITLE 1,Execute Metadata Collection

try:
    # Create orchestrator
    orchestrator = MetadataOrchestrator(
        spark=spark,
        batch_size=ProcessingConfig.BATCH_SIZE,
        max_workers=ProcessingConfig.MAX_WORKERS,
        max_retries=ProcessingConfig.MAX_RETRIES,
        compute_row_count=compute_row_count
    )
    
    # Process all sources
    results, summary_df = orchestrator.process_sources(configs)
    
    # Display summary
    orchestrator.print_summary(summary_df)
    display(summary_df.orderBy("source_id"))
    
except Exception as e:
    logger.exception("Error during metadata collection")
    dbutils.notebook.exit("FAILED")

# COMMAND ----------
# DBTITLE 1,Aggregate and Write Results

if results:
    try:
        # Aggregate all results
        final_df = orchestrator.aggregate_results(results)
        
        if final_df is not None:
            # Handle duplicates
            final_df = check_duplicate_and_update(final_df)
            
            # Resolve target table
            config_table = resolve_table_name(
                Catalog.IDP.name, 
                Schema.CONFIG, 
                "meta_data_registry"
            )
            
            # Select columns in correct order (matching output schema)
            final_df = final_df.select(
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
            )
            
            # Write to table
            # Use "id" as merge key for incremental loads (based on original code)
            write_table(
                final_df,
                config_table,
                partition_cols=["id"] if not full_load else None,
                cdc_check=True,
                source_delete=True
            )
            
            row_count = final_df.count()
            logger.info(f"Successfully wrote {row_count} rows to {config_table}")
            
            # Display sample
            display(final_df.limit(20))
            
    except Exception as e:
        logger.exception("Failed to write results")
        dbutils.notebook.exit("FAILED")
else:
    logger.warning("No data to write")

# COMMAND ----------
# DBTITLE 1,Job Exit

try:
    success_count = summary_df.filter(F.col("status") == "Success").count()
    failure_count = summary_df.filter(F.col("status") == "Failure").count()

    if failure_count > 0:
        exit_status = f"COMPLETED_WITH_ERRORS - Success: {success_count}, Failed: {failure_count}"
    else:
        exit_status = f"SUCCESS - Processed {success_count} sources"
except NameError:
    # summary_df not defined (error occurred before processing)
    exit_status = "FAILED - Processing did not complete"

logger.info(exit_status)
dbutils.notebook.exit(exit_status)
