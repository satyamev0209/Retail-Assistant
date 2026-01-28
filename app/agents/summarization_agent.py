"""Summarization agent for generating CSV insights."""
import pandas as pd
from app.core.prompts import SUMMARIZATION_PROMPT
from app.core.config import settings
import google.generativeai as genai
import logging

from app.core.logger import get_logger, log_execution_time

logger = get_logger(__name__)

# Configure Gemini
genai.configure(api_key=settings.google_api_key)


class SummarizationAgent:
    """Agent for summarizing CSV data."""
    
    def __init__(self):
        """Initialize the summarization agent."""
        self.model = genai.GenerativeModel(settings.model_name)
    
    @log_execution_time(logger)
    def summarize(self, csv_path: str) -> str:
        """
        Generate a summary of the CSV file.
        
        Args:
            csv_path: Path to CSV file
            
        Returns:
            Summary text
        """
        try:
            # Read CSV
            df = pd.read_csv(csv_path)
            
            # Get basic info
            file_name = csv_path.split('/')[-1]
            num_rows = len(df)
            columns = df.columns.tolist()
            
            # Get sample data (first 5 rows)
            sample_data = df.head(5).to_string()
            
            # Generate prompt
            prompt = SUMMARIZATION_PROMPT.format(
                file_name=file_name,
                num_rows=num_rows,
                columns=", ".join(columns),
                sample_data=sample_data
            )
            
            # Generate summary
            response = self.model.generate_content(prompt)
            summary = response.text.strip()
            
            logger.info(f"Generated summary for '{file_name}'")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            raise


# Global summarization agent instance
summarization_agent = SummarizationAgent()
