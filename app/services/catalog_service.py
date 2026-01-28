"""Catalog service for vector database operations using ChromaDB."""
import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.models.schemas import CSVMetadata
import logging
import json

from app.core.logger import get_logger, log_execution_time

logger = get_logger(__name__)


class CatalogService:
    """Service for managing CSV metadata in vector database."""
    
    def __init__(self):
        """Initialize ChromaDB client."""
        self.client = chromadb.PersistentClient(
            path=settings.chroma_db_path,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name="csv_metadata",
            metadata={"description": "CSV file metadata for semantic search"}
        )
        logger.info(f"Connected to ChromaDB at {settings.chroma_db_path}")
    
    @log_execution_time(logger)
    def add_to_kb(self, metadata: CSVMetadata) -> None:
        """
        Add CSV metadata to knowledge base.
        
        Args:
            metadata: CSV metadata object
        """
        try:
            # Create document text for embedding
            doc_text = self._create_document_text(metadata)
            
            # Prepare metadata for storage (must be JSON serializable)
            meta_dict = {
                "file_name": metadata.file_name,
                "file_path": metadata.file_path,
                "table_name": metadata.table_name,
                "num_rows": metadata.num_rows,
                "num_columns": metadata.num_columns,
                "columns": json.dumps(metadata.columns),
                "column_types": json.dumps(metadata.column_types),
                "description": metadata.description,
            }
            
            # Add to collection
            self.collection.add(
                documents=[doc_text],
                metadatas=[meta_dict],
                ids=[metadata.table_name]
            )
            
            logger.info(f"Added metadata for '{metadata.table_name}' to KB")
        except Exception as e:
            logger.error(f"Error adding to KB: {e}")
            raise
    
    @log_execution_time(logger)
    def search_relevant_tables(self, query: str, top_k: int = None) -> List[CSVMetadata]:
        """
        Search for relevant tables based on query.
        
        Args:
            query: Search query
            top_k: Number of results to return (default from settings)
            
        Returns:
            List of CSVMetadata objects
        """
        if top_k is None:
            top_k = settings.top_k_results
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k
            )
            
            # Convert results to CSVMetadata objects
            metadata_list = []
            if results['metadatas'] and len(results['metadatas'][0]) > 0:
                for meta in results['metadatas'][0]:
                    metadata_list.append(self._dict_to_metadata(meta))
            
            logger.info(f"Found {len(metadata_list)} relevant tables for query: {query}")
            return metadata_list
        except Exception as e:
            logger.error(f"Error searching KB: {e}")
            return []
    
    def get_metadata(self, table_name: str) -> Optional[CSVMetadata]:
        """
        Get metadata for a specific table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            CSVMetadata object or None if not found
        """
        try:
            result = self.collection.get(ids=[table_name])
            if result['metadatas'] and len(result['metadatas']) > 0:
                return self._dict_to_metadata(result['metadatas'][0])
            return None
        except Exception as e:
            logger.error(f"Error getting metadata: {e}")
            return None
    
    def list_all_tables(self) -> List[str]:
        """
        List all tables in the knowledge base.
        
        Returns:
            List of table names
        """
        try:
            result = self.collection.get()
            return result['ids'] if result['ids'] else []
        except Exception as e:
            logger.error(f"Error listing tables: {e}")
            return []
    
    def remove_from_kb(self, table_name: str) -> None:
        """
        Remove table metadata from knowledge base.
        
        Args:
            table_name: Name of the table to remove
        """
        try:
            self.collection.delete(ids=[table_name])
            logger.info(f"Removed '{table_name}' from KB")
        except Exception as e:
            logger.error(f"Error removing from KB: {e}")
    
    def _create_document_text(self, metadata: CSVMetadata) -> str:
        """Create searchable document text from metadata."""
        sample_str = ", ".join([
            f"{col}: {vals}" for col, vals in list(metadata.sample_values.items())[:3]
        ])
        
        return f"""
        File: {metadata.file_name}
        Description: {metadata.description}
        Columns: {', '.join(metadata.columns)}
        Sample data: {sample_str}
        """.strip()
    
    def _dict_to_metadata(self, meta_dict: Dict[str, Any]) -> CSVMetadata:
        """Convert dictionary to CSVMetadata object."""
        return CSVMetadata(
            file_name=meta_dict['file_name'],
            file_path=meta_dict['file_path'],
            table_name=meta_dict['table_name'],
            num_rows=meta_dict['num_rows'],
            num_columns=meta_dict['num_columns'],
            columns=json.loads(meta_dict['columns']),
            column_types=json.loads(meta_dict['column_types']),
            description=meta_dict['description'],
            sample_values={}  # Not stored in vector DB
        )


# Global catalog service instance
catalog_service = CatalogService()
