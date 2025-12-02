# IDP Metadata Collector Framework - Development Plan

## Executive Summary

This document outlines the architecture and implementation plan for a production-ready metadata collection framework that gathers metadata from various data sources and produces a canonical `meta_data_registry` dataset.

---

## 1. Architecture Overview

### 1.1 Design Principles (SOLID)

| Principle | Application |
|-----------|-------------|
| **Single Responsibility** | Each collector class handles one data source type only |
| **Open/Closed** | New data sources can be added via new collector classes without modifying existing code |
| **Liskov Substitution** | All collectors can be used interchangeably through the base interface |
| **Interface Segregation** | Separate interfaces for different capabilities (schema extraction, row counting, file metadata) |
| **Dependency Inversion** | High-level orchestrator depends on abstractions, not concrete implementations |

### 1.2 Design Patterns Used

| Pattern | Purpose |
|---------|---------|
| **Strategy Pattern** | Different metadata extraction strategies per source type |
| **Factory Pattern** | Creates appropriate collector based on data source type |
| **Template Method** | Common processing flow with customizable steps |
| **Registry Pattern** | Central registry of all collector implementations |
| **Builder Pattern** | Construct complex metadata result objects |

---

## 2. Component Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        MetadataOrchestrator                          │
│  (Batch processing, parallelization, retry logic, result aggregation)│
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        CollectorFactory                              │
│  (Creates appropriate collector based on data_source_type)           │
└─────────────────────────────────────────────────────────────────────┘
                                    │
            ┌───────────────────────┼───────────────────────┐
            ▼                       ▼                       ▼
┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│ AbstractCollector   │  │ AbstractCollector   │  │ AbstractCollector   │
│ (Base Interface)    │  │ (Base Interface)    │  │ (Base Interface)    │
└─────────────────────┘  └─────────────────────┘  └─────────────────────┘
            │                       │                       │
            ▼                       ▼                       ▼
┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│ JDBCCollector       │  │ StorageCollector    │  │ RESTAPICollector    │
│ (SQL databases)     │  │ (Azure Blob/ADLS)   │  │ (REST endpoints)    │
└─────────────────────┘  └─────────────────────┘  └─────────────────────┘
            │                       │
    ┌───────┴───────┐       ┌───────┴───────┐
    ▼       ▼       ▼       ▼       ▼       ▼
┌───────┐┌───────┐┌───────┐┌───────┐┌───────┐┌───────┐
│SQLSvr ││Postgrs││MariaDB││ABFSS  ││WABS   ││Cassand│
│Collect││Collect││Collect││Collect││Collect││Collect│
└───────┘└───────┘└───────┘└───────┘└───────┘└───────┘
```

---

## 3. Supported Data Source Types

| Type | Category | Implementation |
|------|----------|----------------|
| SQLSERVER | JDBC | SQLServerCollector |
| POSTGRESQL | JDBC | PostgreSQLCollector |
| MARIADB | JDBC | MariaDBCollector |
| CASSANDRA | NoSQL | CassandraCollector |
| ABFSS_STORAGE | Azure Storage | ABFSSStorageCollector |
| WABS_STORAGE | Azure Storage | WABSStorageCollector |
| WASBS_SAS_STORAGE | Azure Storage | WASBSSASStorageCollector |
| REST_API | API | RESTAPICollector |

---

## 4. Output Schema

All metadata rows must contain these columns:

| Column | Type | Description |
|--------|------|-------------|
| full_table_name | string | Fully qualified table name or file path |
| table_name | string | Short table name or filename |
| id_columns | array<string> | Source ID columns (preserve case) |
| partition_cols | array<string> | Partition column names |
| ct_enabled | int (0/1) | Change tracking/CDC enabled |
| source_id | string | Source config ID |
| catalog_name | string | Source catalog name (UPPER) |
| entity_name | string | Optional logical entity name |
| db_name | string | Database name from config |
| id | string | Unique ID (source_id_table) |
| include_list | array<string> | Include list from config |
| exclude_list | array<string> | Exclude list from config |
| is_included | int (0/1) | Resolved using include/exclude |
| is_append_only | int (0/1) | From append-only list |
| is_active | int (0/1) | Usually same as is_included |
| table_run_properties | int | Compact flags |
| idp_db_name | string | Snake_case table name |
| idp_id_columns | array<string> | Snake_case ID columns |
| idp_cdc_hash | string | CDC hash for metadata |
| idp_created_date | timestamp | Creation timestamp |
| idp_modified_date | timestamp | Modified timestamp |
| table_row_count | long (nullable) | Optional row count |
| column_count | int | Number of columns |
| source_schema | array<string> | Column names, preserved case |
| idp_schema | array<string> | Snake_case column names |
| column_details | array<struct> | [{name, data_type, nullable, metadata}] |
| file_size_bytes | long (nullable) | Only for files |
| file_last_modified | timestamp (nullable) | Only for files |
| sample_file_paths | array<string> | For file-based sources |

---

## 5. Key Business Rules

### 5.1 Schema Handling
- `source_schema`: Preserve exact source column names (case and spelling)
- `idp_schema`: Convert all columns to snake_case for canonical representation

### 5.2 ID Column Resolution
1. Use configured `db_details.id_columns` if present
2. If missing, attempt to discover primary keys from source
3. Generate `idp_id_columns` as snake_case version

### 5.3 Unique ID Generation
- Format: `source_id + '_' + table_name`
- Deduplication: If duplicates exist, prepend schema/catalog to table_name

### 5.4 Include/Exclude Logic
```
is_included = (
    (size(include_list)==0 AND size(exclude_list)==0) OR
    (table_name IN include_list AND table_name NOT IN exclude_list) OR
    (size(include_list)==0 AND table_name NOT IN exclude_list)
)
```

### 5.5 Row Count (Optional)
- Controlled by `compute_row_count` config flag (default: False)
- Skip expensive COUNT(*) on large tables

---

## 6. Implementation Components

### 6.1 Configuration Models
- `DataSourceConfig`: Main configuration model
- `DBDetails`: Database-specific details
- `StorageDetails`: Storage-specific details
- `APIDetails`: REST API-specific details

### 6.2 Collector Classes
- `BaseMetadataCollector`: Abstract base with template method
- `JDBCMetadataCollector`: Base for SQL databases
- `StorageMetadataCollector`: Base for Azure storage
- `CassandraMetadataCollector`: Cassandra-specific
- `RESTAPIMetadataCollector`: REST API-specific

### 6.3 Helper Functions
- `to_snake_case(s)`: Convert string to snake_case
- `to_snake_case_list(lst)`: Convert list to snake_case
- `compute_cdc_hash(row)`: Generate CDC hash
- `check_duplicate_and_update(df)`: Handle duplicate IDs

### 6.4 Orchestration
- `CollectorFactory`: Factory for creating collectors
- `MetadataOrchestrator`: Batch processing with parallelization

---

## 7. Performance Optimizations

1. **Batch Processing**: Process sources in batches of 25
2. **Parallelization**: ThreadPoolExecutor with 5 workers
3. **Caching**: Cache catalog queries to avoid redundant reads
4. **Lazy Evaluation**: Use Spark lazy evaluation efficiently
5. **Limit(0) for Schema**: Read zero rows for file schema extraction
6. **Optional Row Counts**: Skip expensive COUNT(*) by default

---

## 8. Error Handling

1. **Retry Logic**: 3 retries per source with exponential backoff
2. **Graceful Degradation**: Continue processing other sources on failure
3. **Error Tracking**: Record failures in summary table with error messages
4. **No Secret Logging**: Never log credentials or secrets

---

## 9. Testing Strategy

### 9.1 Unit Tests
- `test_to_snake_case`: Various input cases
- `test_to_snake_case_list`: List conversion
- `test_include_exclude_logic`: Business rule validation
- `test_duplicate_handling`: Deduplication logic
- `test_id_generation`: Unique ID format

### 9.2 Integration Tests
- Test each collector type with mock data
- Test orchestrator batch processing
- Test result aggregation

---

## 10. File Structure

```
/workspace/
├── IDP_Metadata_Collector_Framework.py  # Main framework file
├── tests/
│   └── test_metadata_collector.py       # Unit tests
├── DEVELOPMENT_PLAN.md                   # This document
└── README.md                             # Usage documentation
```

---

## 11. Scenarios Covered

| Scenario | Status |
|----------|--------|
| SQLSERVER with CT enabled | ✅ |
| POSTGRESQL standard | ✅ |
| MARIADB standard | ✅ |
| CASSANDRA with keyspace | ✅ |
| ABFSS_STORAGE with parquet | ✅ |
| ABFSS_STORAGE with CSV | ✅ |
| WABS_STORAGE | ✅ |
| WASBS_SAS_STORAGE | ✅ |
| REST_API endpoints | ✅ |
| Include/Exclude filtering | ✅ |
| Append-only tables | ✅ |
| Duplicate ID handling | ✅ |
| Missing ID columns discovery | ✅ |
| Optional row count | ✅ |
| File metadata (size, modified) | ✅ |
| Schema extraction (source & IDP) | ✅ |
| Retry on failure | ✅ |
| Batch parallelization | ✅ |
| Summary report generation | ✅ |

---

## 12. Next Steps

1. ✅ Create development plan
2. 🔄 Implement core data models
3. 🔄 Implement abstract collector interfaces
4. 🔄 Implement concrete collectors
5. 🔄 Implement helper functions
6. 🔄 Implement orchestrator
7. 🔄 Create unit tests
8. 🔄 Final integration and validation
