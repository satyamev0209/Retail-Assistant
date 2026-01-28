"""Ingestion service for CSV metadata extraction."""
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any
from app.models.schemas import CSVMetadata
from app.core.config import settings
from app.core.prompts import METADATA_DESCRIPTION_PROMPT
import google.generativeai as genai
import logging

from app.core.logger import get_logger, log_execution_time

logger = get_logger(__name__)

# Configure Gemini
genai.configure(api_key=settings.google_api_key)


class IngestionService:
    """Service for extracting metadata from CSV files."""
    
    def __init__(self):
        """Initialize the ingestion service."""
        self.model = genai.GenerativeModel(settings.model_name)
    
    @log_execution_time(logger)
    def extract_metadata(self, csv_path: str, table_name: str = None) -> CSVMetadata:
        """
        Extract metadata from a CSV file.
        
        Args:
            csv_path: Path to CSV file
            table_name: Optional custom table name
            
        Returns:
            CSVMetadata object
        """
        try:
            # Read CSV
            df = pd.read_csv(csv_path)
            
            # Generate table name if not provided
            if table_name is None:
                file_name = Path(csv_path).stem
                # Clean table name (remove spaces, special chars)
                table_name = "kb_" + file_name.replace(" ", "_").replace("-", "_").lower()
            else:
                # Sanitize provided table name
                table_name = table_name.replace("-", "_")
            
            # Extract basic metadata
            columns = df.columns.tolist()
            column_types = {col: str(dtype) for col, dtype in df.dtypes.items()}
            num_rows = len(df)
            num_columns = len(columns)
            
            # Get sample values (first 3 unique values per column)
            sample_values = {}
            for col in columns:
                unique_vals = df[col].dropna().unique()[:3].tolist()
                sample_values[col] = [str(v) for v in unique_vals]
            
            # Generate description using LLM
            description = self._generate_description(
                file_name=Path(csv_path).name,
                columns=columns,
                sample_values=sample_values
            )
            
            metadata = CSVMetadata(
                file_name=Path(csv_path).name,
                file_path=csv_path,
                table_name=table_name,
                num_rows=num_rows,
                num_columns=num_columns,
                columns=columns,
                column_types=column_types,
                description=description,
                sample_values=sample_values
            )
            
            logger.info(f"Extracted metadata for '{Path(csv_path).name}'")
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            raise
    
    def _generate_description(
        self, 
        file_name: str, 
        columns: List[str], 
        sample_values: Dict[str, List[Any]]
    ) -> str:
        """Generate a description of the CSV using LLM."""
        try:
            # Format sample values
            sample_str = "\n".join([
                f"- {col}: {vals}" for col, vals in list(sample_values.items())[:5]
            ])
            
            prompt = METADATA_DESCRIPTION_PROMPT.format(
                file_name=file_name,
                columns=", ".join(columns),
                sample_values=sample_str
            )
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.warning(f"Error generating description with LLM: {e}")
            # Fallback to simple description
            return f"CSV file with {len(columns)} columns: {', '.join(columns[:5])}"


# Global ingestion service instance
ingestion_service = IngestionService()
