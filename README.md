# IDP Metadata Collector Framework

A production-ready, extensible framework for collecting metadata from diverse data sources and producing a canonical `meta_data_registry` dataset for downstream pipelines and audits.

## 📋 Overview

This framework implements a metadata collection system that:
- Collects schema and configuration information from multiple data source types
- Produces standardized metadata output with both source and IDP (snake_case) representations
- Supports batch processing with parallelization for optimal performance
- Includes robust error handling with retry logic
- Follows SOLID principles and design patterns for maintainability

## 🏗 Architecture

### Design Principles (SOLID)

| Principle | Implementation |
|-----------|----------------|
| **Single Responsibility** | Each collector handles one data source type |
| **Open/Closed** | New data sources via new collector classes without modifying existing code |
| **Liskov Substitution** | All collectors interchangeable through base interface |
| **Interface Segregation** | Separate interfaces for different capabilities |
| **Dependency Inversion** | Orchestrator depends on abstractions, not implementations |

### Design Patterns

| Pattern | Purpose |
|---------|---------|
| **Strategy** | Different extraction strategies per source type |
| **Factory** | Creates appropriate collector based on source type |
| **Template Method** | Common processing flow with customizable steps |
| **Registry** | Central registry of collector implementations |

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    MetadataOrchestrator                      │
│  (Batch processing, parallelization, retry, aggregation)    │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                     CollectorFactory                         │
│         (Creates collector based on data_source_type)        │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│ JDBCCollector │  │StorageCollect │  │ APICollector  │
│ (SQL DBs)     │  │ (Azure Blob)  │  │ (REST APIs)   │
└───────┬───────┘  └───────┬───────┘  └───────────────┘
        │                  │
   ┌────┼────┐        ┌────┼────┐
   ▼    ▼    ▼        ▼    ▼    ▼
┌────┐┌────┐┌────┐ ┌────┐┌────┐┌────┐
│SQL ││Pgrs││Mari│ │ABFS││WABS││SAS │
│Srvr││QL  ││aDB │ │S   ││    ││    │
└────┘└────┘└────┘ └────┘└────┘└────┘
```

## 📁 File Structure

```
/workspace/
├── IDP_Metadata_Collector_Framework.py  # Main framework (Databricks notebook)
├── tests/
│   └── test_metadata_collector.py       # Unit tests (64 tests)
├── DEVELOPMENT_PLAN.md                   # Architecture documentation
└── README.md                             # This file
```

## 🔧 Supported Data Sources

| Type | Category | Description |
|------|----------|-------------|
| `SQLSERVER` | JDBC | Microsoft SQL Server with Change Tracking support |
| `POSTGRESQL` | JDBC | PostgreSQL databases |
| `MARIADB` | JDBC | MariaDB/MySQL databases |
| `CASSANDRA` | NoSQL | Apache Cassandra with secure connect bundle |
| `ABFSS_STORAGE` | Storage | Azure Data Lake Storage Gen2 |
| `WABS_STORAGE` | Storage | Azure Blob Storage |
| `WASBS_SAS_STORAGE` | Storage | Azure Blob Storage with SAS tokens |
| `REST_API` | API | REST API endpoints |

## 📊 Output Schema

The framework produces metadata rows with these columns:

| Column | Type | Description |
|--------|------|-------------|
| `full_table_name` | string | Fully qualified table name or file path |
| `table_name` | string | Short table name (preserved case) |
| `id_columns` | array<string> | Primary key columns (source case) |
| `partition_cols` | array<string> | Partition column names |
| `ct_enabled` | int (0/1) | Change tracking enabled |
| `source_id` | string | Configuration ID (e.g., 'AEXML-001') |
| `catalog_name` | string | Source catalog (UPPER case) |
| `entity_name` | string | Optional logical entity name |
| `db_name` | string | Database name |
| `id` | string | Unique ID: `source_id_table_name` |
| `include_list` | array<string> | Include filter from config |
| `exclude_list` | array<string> | Exclude filter from config |
| `is_included` | int (0/1) | Whether table is included |
| `is_append_only` | int (0/1) | Append-only flag |
| `is_active` | int (0/1) | Active status |
| `table_run_properties` | int | Compact flags |
| `idp_db_name` | string | Snake_case table name |
| `idp_id_columns` | array<string> | Snake_case ID columns |
| `source_schema` | array<string> | Column names (preserved case) |
| `idp_schema` | array<string> | Snake_case column names |
| `column_count` | int | Number of columns |
| `column_details` | array<struct> | Detailed column metadata |
| `table_row_count` | long | Optional row count |
| `file_size_bytes` | long | File size (storage sources) |
| `file_last_modified` | timestamp | Last modified (storage) |
| `sample_file_paths` | array<string> | Sample file paths |
| `idp_cdc_hash` | string | CDC hash for change detection |
| `idp_created_date` | timestamp | Creation timestamp |
| `idp_modified_date` | timestamp | Modified timestamp |

## 🚀 Usage

### Running the Notebook

```python
# Widget Parameters
dbutils.widgets.text("full_load", "False", "Full Load?")
dbutils.widgets.text("job_run_id", "", "Job Run ID")
dbutils.widgets.text("compute_row_count", "False", "Compute Row Counts?")
dbutils.widgets.text("source_types", "", "Source Types (comma-separated)")
```

### Programmatic Usage

```python
from IDP_Metadata_Collector_Framework import (
    MetadataOrchestrator,
    CollectorFactory,
    load_source_configurations,
    ProcessingConfig
)

# Load configurations
configs = load_source_configurations(
    spark,
    config_table="qa_idp.config.metadata_source_connection_details",
    source_types=["SQLSERVER", "POSTGRESQL"],
    active_only=True
)

# Create orchestrator
orchestrator = MetadataOrchestrator(
    spark=spark,
    batch_size=25,
    max_workers=5,
    max_retries=3
)

# Process sources
results, summary_df = orchestrator.process_sources(configs)

# Aggregate and write
final_df = orchestrator.aggregate_results(results)
```

### Adding a New Data Source Type

```python
from IDP_Metadata_Collector_Framework import (
    BaseMetadataCollector,
    CollectorFactory
)

class MyCustomCollector(BaseMetadataCollector):
    """Collector for custom data source."""
    
    def _get_connection_url(self) -> str:
        return "custom://..."
    
    def _fetch_raw_metadata(self) -> Optional[DataFrame]:
        # Implement metadata fetching
        pass
    
    def _get_include_list(self) -> List[str]:
        return self.config.db_details.get("include_list", [])
    
    def _get_exclude_list(self) -> List[str]:
        return self.config.db_details.get("exclude_list", [])
    
    def _get_append_only_list(self) -> List[str]:
        return self.config.db_details.get("append_only_list", [])
    
    def _get_configured_id_columns(self) -> Optional[List[str]]:
        return self.config.db_details.get("id_columns")

# Register the new collector
CollectorFactory.register_collector("MY_CUSTOM_TYPE", MyCustomCollector)
```

## ⚙️ Configuration

### Processing Configuration

```python
class ProcessingConfig:
    BATCH_SIZE: int = 25          # Sources per batch
    MAX_RETRIES: int = 3          # Retry attempts
    MAX_WORKERS: int = 5          # Parallel workers
    RETRY_DELAY_SECONDS: float = 1.0
    COMPUTE_ROW_COUNT: bool = False  # Skip expensive COUNT(*)
    MAX_SAMPLE_FILES: int = 5     # Sample paths to include
```

### Source Configuration Table

The framework reads from `qa_idp.config.metadata_source_connection_details`:

```sql
CREATE TABLE metadata_source_connection_details (
    id STRING,
    data_source_type STRING,
    catalog_name STRING,
    table_name STRING,
    metadata_enabled BOOLEAN,
    db_details STRING,  -- JSON
    is_active BOOLEAN,
    idp_cdc_hash STRING,
    idp_created_date TIMESTAMP,
    idp_modified_date TIMESTAMP
);
```

### db_details JSON Examples

**JDBC (SQL Server):**
```json
{
    "db_host": "server.database.windows.net",
    "db_name": "database",
    "user_name": "user",
    "password_key": "SECRET-KEY",
    "db_port": "1433",
    "table_schema": ["dbo"],
    "exclude_list": [],
    "is_ct_enabled": true
}
```

**Azure Storage:**
```json
{
    "storage_name": "storageaccount",
    "container_name": "container",
    "storage_access_key": "SECRET-KEY",
    "folder_path": "path/to/files",
    "file_extension": "parquet",
    "id_columns": ["id", "code"],
    "set_spark_config": true
}
```

## 🧪 Testing

Run the unit tests:

```bash
cd /workspace
python3 -m pytest tests/test_metadata_collector.py -v
```

**Test Coverage:**
- 64 tests covering all helper functions
- Snake_case conversion
- Include/exclude logic
- Duplicate handling
- Schema conversion
- Configuration parsing
- Edge cases

## 📈 Performance Optimizations

1. **Batch Processing**: Sources processed in batches of 25
2. **Parallelization**: ThreadPoolExecutor with 5 workers
3. **Lazy Evaluation**: Efficient Spark transformations
4. **Zero-Row Schema**: Files read with limit(0) for schema only
5. **Optional Row Counts**: Skip COUNT(*) for large tables
6. **Caching**: Strategic caching of intermediate results

## 🔒 Security

- **No Secret Logging**: Credentials never logged
- **Secrets Integration**: Uses `get_secret_value()` for all secrets
- **Key-based Access**: Password keys reference Databricks secrets

## 📝 Business Rules

### Include/Exclude Logic
```
is_included = (
    (size(include_list)==0 AND size(exclude_list)==0) OR
    (table_name IN include_list AND table_name NOT IN exclude_list) OR
    (size(include_list)==0 AND table_name NOT IN exclude_list)
)
```

### Duplicate ID Resolution
When multiple tables produce identical IDs:
1. Detect duplicates by grouping on `id`
2. For duplicates, prefix table_name with schema: `schema_table`
3. Regenerate ID: `source_id_schema_table`

### Schema Preservation
- `source_schema`: Exact column names as returned by source
- `idp_schema`: Snake_case conversion for IDP standardization

## 📊 Sample Output

| full_table_name | table_name | id_columns | source_id | is_included | idp_db_name |
|-----------------|------------|------------|-----------|-------------|-------------|
| dbo.FontReplacement | FontReplacement | ["Id"] | AEXML-004 | 1 | font_replacement |
| public.users | users | ["user_id"] | PRINTERSPEC-001 | 1 | users |

## 🤝 Contributing

1. Follow SOLID principles
2. Add unit tests for new functionality
3. Update documentation
4. Maintain backward compatibility

## 📜 License

Internal use only.
