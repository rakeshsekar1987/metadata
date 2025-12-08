# MSSQL to Databricks Parallel Table Loader

A production-ready PySpark notebook for loading 100+ tables from Microsoft SQL Server into Databricks Delta Lake with parallelism, cost efficiency, and SOLID principles.

## Features

- **Parallel Loading**: Load multiple tables concurrently using ThreadPoolExecutor
- **Adaptive Partitioning**: Automatically calculates optimal partitions based on table size
- **Cost Efficient**: Query pushdown, optimized batch sizes, and Delta OPTIMIZE
- **SOLID Architecture**: Clean, maintainable, and extensible code design
- **Auto-Discovery**: Automatically discovers tables from source schema
- **Multiple Load Modes**: Overwrite, Append, or Merge with primary keys
- **Audit Logging**: Tracks all load operations with detailed metrics

## SOLID Principles Implementation

| Principle | Implementation |
|-----------|----------------|
| **Single Responsibility** | Each class has one job: `JDBCConfig` (connection), `TableConfig` (metadata), `JDBCDataReader` (reading), `DeltaDataWriter` (writing) |
| **Open/Closed** | `PartitionStrategy` base class allows new strategies without modifying existing code |
| **Liskov Substitution** | All loaders implement `ITableLoader` protocol and are interchangeable |
| **Interface Segregation** | Separate protocols: `IConnectionProvider`, `IDataReader`, `IDataWriter`, `ITableMetadataProvider` |
| **Dependency Inversion** | High-level `TableLoader` depends on abstract interfaces, not concrete implementations |

## Prerequisites

### 1. Databricks Secret Scope
Create a secret scope with MSSQL credentials:

```bash
# Using Databricks CLI
databricks secrets create-scope mssql-secrets
databricks secrets put --scope mssql-secrets --key username
databricks secrets put --scope mssql-secrets --key password
```

### 2. JDBC Driver
Ensure the MSSQL JDBC driver is available on your cluster:
- Install from Maven: `com.microsoft.sqlserver:mssql-jdbc:12.4.2.jre11`

### 3. Network Connectivity
- Ensure your Databricks workspace can reach your MSSQL server
- Configure firewall rules or use Private Link for Azure SQL

## Usage

### Quick Start

1. Import the notebook into Databricks
2. Configure the widgets at the top:
   - `mssql_host`: Your MSSQL server hostname
   - `mssql_port`: Port (default: 1433)
   - `mssql_database`: Source database name
   - `mssql_schema`: Source schema (default: dbo)
   - `target_catalog`: Databricks Unity Catalog name
   - `target_schema`: Target schema (e.g., bronze)
   - `load_mode`: overwrite, append, or merge
   - `max_parallel_tables`: Number of concurrent table loads
   - `partition_size_mb`: Target partition size for large tables

3. Run all cells

### Manual Table Configuration

For specific table configurations, use Cell 17:

```python
manual_table_configs = [
    TableConfig(
        source_schema="dbo",
        source_table="LargeTable",
        target_catalog="my_catalog",
        target_schema="bronze",
        partition_column="ID",  # Numeric column for parallel reads
        primary_keys=["ID"]     # For merge operations
    ),
    # Add more tables...
]
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    ParallelTableOrchestrator                    │
│                  (Manages concurrent execution)                 │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         TableLoader                             │
│              (Combines Reader + Writer per table)               │
└──────────────┬─────────────────────────────────┬────────────────┘
               │                                 │
               ▼                                 ▼
┌──────────────────────────┐       ┌──────────────────────────────┐
│      JDBCDataReader      │       │      DeltaDataWriter         │
│  - Adaptive partitioning │       │  - Overwrite/Append/Merge    │
│  - Query pushdown        │       │  - Auto OPTIMIZE             │
│  - Audit columns         │       │  - Schema evolution          │
└──────────────────────────┘       └──────────────────────────────┘
               │
               ▼
┌──────────────────────────┐
│   PartitionStrategy      │
│  - AdaptivePartition     │
│  - FixedPartition        │
└──────────────────────────┘
```

## Cost Optimization

### Cluster Configuration

```
Node type: Standard_DS3_v2 (or equivalent)
Min workers: 2
Max workers: 10-20 (scale with table count)
Autoscaling: Enabled
Photon: Enabled (for Delta optimizations)

Spark Config:
  spark.sql.shuffle.partitions: 200
  spark.databricks.delta.optimizeWrite.enabled: true
  spark.databricks.delta.autoCompact.enabled: true
```

### Tuning Parameters

| Parameter | Recommendation | Impact |
|-----------|----------------|--------|
| `max_parallel_tables` | 5-15 | Higher = faster but more memory |
| `partition_size_mb` | 128-256 | Larger = fewer tasks, less overhead |
| `fetch_size` | 10000 | Rows per JDBC fetch |
| `batch_size` | 100000 | Rows per write batch |

### Memory Management

For 100+ tables, use batched loading:

```python
results = orchestrator.load_tables_in_batches(
    table_configs=table_configs,
    batch_size=25  # Process 25 tables, then free memory
)
```

## Monitoring

### Audit Log

All load operations are logged to `{target_catalog}.{target_schema}._load_audit_log`:

| Column | Description |
|--------|-------------|
| source_table | Full source table name |
| target_table | Full target table name |
| status | success/failed |
| row_count | Rows loaded |
| duration_seconds | Load time |
| start_time | Load start timestamp |
| end_time | Load end timestamp |
| error | Error message (if failed) |

### Query Audit Log

```sql
-- Recent load summary
SELECT 
  DATE(start_time) as load_date,
  COUNT(*) as tables_loaded,
  SUM(row_count) as total_rows,
  AVG(duration_seconds) as avg_duration,
  SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count
FROM your_catalog.bronze._load_audit_log
GROUP BY DATE(start_time)
ORDER BY load_date DESC;
```

## Extending the Framework

### Custom Partition Strategy

```python
class DatePartitionStrategy(PartitionStrategy):
    """Partition by date ranges for time-series data."""
    
    def calculate_partitions(self, table_config: TableConfig, row_count: int) -> Dict[str, Any]:
        # Custom logic for date-based partitioning
        pass
```

### Custom Writer

```python
class IcebergDataWriter:
    """Write to Apache Iceberg instead of Delta."""
    
    def write(self, df: DataFrame, table_config: TableConfig, mode: str) -> Dict[str, Any]:
        # Iceberg write logic
        pass
```

## Troubleshooting

### Common Issues

1. **Connection Timeout**
   - Increase `loginTimeout` in JDBC URL
   - Check network connectivity

2. **Out of Memory**
   - Reduce `max_parallel_tables`
   - Increase `partition_size_mb`
   - Use `load_tables_in_batches()`

3. **Slow Large Tables**
   - Ensure `partition_column` is set (ideally indexed integer)
   - Increase `num_partitions`

4. **Merge Failures**
   - Verify primary keys are correctly identified
   - Check for null values in key columns

## License

MIT License - Free to use and modify.
