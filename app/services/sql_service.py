"""SQL service for DuckDB operations."""
import duckdb
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.core.config import settings
import logging

from app.core.logger import get_logger, log_execution_time

logger = get_logger(__name__)


class SQLService:
    """Service for SQL database operations using DuckDB."""
    
    def __init__(self):
        """Initialize DuckDB connection."""
        self.db_path = settings.duckdb_path
        self.conn = duckdb.connect(str(self.db_path))
        logger.info(f"Connected to DuckDB at {self.db_path}")
    
    @log_execution_time(logger)
    def load_csv_to_db(self, csv_path: str, table_name: str, is_temp: bool = False) -> None:
        """
        Load CSV file into DuckDB as a table.
        
        Args:
            csv_path: Path to CSV file
            table_name: Name for the table
            is_temp: If True, create temporary table
        """
        try:
            # Load CSV
            df = pd.read_csv(csv_path)
            
            # Heuristic: Check if first row looks like a header (e.g. contains "Particular")
            # This handles files like "Expense IIGF.csv" where Row 0 is "Particular, Amount..."
            if not df.empty:
                first_row_vals = df.iloc[0].astype(str).tolist()
                if any(x.lower() in ['particular', 'particulars'] for x in first_row_vals):
                    logger.info(f"Detected potential header in row 0 for {csv_path}, reloading...")
                    df = pd.read_csv(csv_path, header=1)
            
            # Sanitize table name (replace hyphens with underscores)
            table_name = table_name.replace("-", "_")
            
            # Create table (temp or persistent)
            if is_temp:
                self.conn.execute(f"CREATE TEMP TABLE {table_name} AS SELECT * FROM df")
            else:
                # Drop if exists and create new
                self.conn.execute(f"DROP TABLE IF EXISTS {table_name}")
                self.conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM df")
            
            logger.info(f"Loaded {len(df)} rows into table '{table_name}' (temp={is_temp})")
        except Exception as e:
            logger.error(f"Error loading CSV to DB: {e}")
            raise
    
    @log_execution_time(logger)
    def execute_query(self, sql: str) -> List[Dict[str, Any]]:
        """
        Execute SQL query and return results as list of dicts.
        
        Args:
            sql: SQL query string
            
        Returns:
            List of dictionaries representing rows
        """
        try:
            result = self.conn.execute(sql).fetchdf()
            return result.to_dict('records')
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise
    
    def get_table_schema(self, table_name: str) -> Dict[str, str]:
        """
        Get schema of a table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Dictionary mapping column names to types
        """
        try:
            result = self.conn.execute(
                f"DESCRIBE {table_name}"
            ).fetchdf()
            return dict(zip(result['column_name'], result['column_type']))
        except Exception as e:
            logger.error(f"Error getting table schema: {e}")
            raise
    
    def list_tables(self, include_temp: bool = False) -> List[str]:
        """
        List all tables in the database.
        
        Args:
            include_temp: Whether to include temporary tables
            
        Returns:
            List of table names
        """
        try:
            query = "SHOW TABLES"
            result = self.conn.execute(query).fetchdf()
            tables = result['name'].tolist()
            
            if not include_temp:
                # Filter out temp tables (they start with 'temp_')
                tables = [t for t in tables if not t.startswith('temp_')]
            
            return tables
        except Exception as e:
            logger.error(f"Error listing tables: {e}")
            return []
    
    def drop_table(self, table_name: str) -> None:
        """
        Drop a table from the database.
        
        Args:
            table_name: Name of the table to drop
        """
        try:
            self.conn.execute(f"DROP TABLE IF EXISTS {table_name}")
            logger.info(f"Dropped table '{table_name}'")
        except Exception as e:
            logger.error(f"Error dropping table: {e}")
            raise
    
    def cleanup_temp_tables(self, session_id: str) -> None:
        """
        Clean up temporary tables for a session.
        
        Args:
            session_id: Session identifier
        """
        try:
            tables = self.list_tables(include_temp=True)
            temp_tables = [t for t in tables if t.startswith(f"temp_{session_id}_")]
            
            for table in temp_tables:
                self.drop_table(table)
            
            logger.info(f"Cleaned up {len(temp_tables)} temp tables for session {session_id}")
        except Exception as e:
            logger.error(f"Error cleaning up temp tables: {e}")
    
    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Closed DuckDB connection")


# Global SQL service instance
sql_service = SQLService()
