"""Query agent for generating and executing SQL queries."""
from typing import List, Dict, Any
from app.core.prompts import QUERY_GENERATION_PROMPT
from app.core.config import settings
from app.models.schemas import CSVMetadata
from app.services.sql_service import sql_service
import google.generativeai as genai
import logging

from app.core.logger import get_logger, log_execution_time

logger = get_logger(__name__)

# Configure Gemini
genai.configure(api_key=settings.google_api_key)


class QueryAgent:
    """Agent for generating and executing SQL queries."""
    
    def __init__(self):
        """Initialize the query agent."""
        self.model = genai.GenerativeModel(settings.model_name)
    
    @log_execution_time(logger)
    def generate_and_execute_query(
        self, 
        user_question: str, 
        table_schemas: Dict[str, CSVMetadata],
        error_context: str = None
    ) -> tuple[str, List[Dict[str, Any]]]:
        """
        Generate SQL query and execute it with self-correction.
        """
        last_error = None
        
        # Max retries for self-correction
        for attempt in range(3):
            try:
                # Combine external error context with internal retry error
                current_error = last_error if last_error else error_context
                
                # Generate SQL query (pass error context if retrying)
                sql_query = self._generate_sql(user_question, table_schemas, error_context=current_error)
                
                # Execute query
                results = sql_service.execute_query(sql_query)
                
                logger.info(f"Executed query (Attempt {attempt+1}): {sql_query}")
                return sql_query, results
                
            except Exception as e:
                # Capture error for next iteration
                last_error = str(e)
                logger.warning(f"Query attempt {attempt+1} failed: {last_error}")
                
                # On last attempt, raise the error
                if attempt == 2:
                    logger.error(f"All query attempts failed. Last error: {last_error}")
                    raise
    
    def _generate_sql(
        self, 
        user_question: str, 
        table_schemas: Dict[str, CSVMetadata],
        error_context: str = None
    ) -> str:
        """Generate SQL query using LLM."""
        try:
            # Format table schemas
            schema_text = self._format_schemas(table_schemas)
            
            # Generate prompt
            prompt = QUERY_GENERATION_PROMPT.format(
                table_schemas=schema_text,
                user_question=user_question
            )
            
            # Add error context if retrying
            if error_context:
                prompt += f"\n\nIMPORTANT: The previous query failed with this error:\n{error_context}\nPlease correct the SQL to fix this error. Ensure accurate column names and data types."
            
            # Generate SQL
            response = self.model.generate_content(prompt)
            sql_query = response.text.strip()
            
            # Clean up the SQL (remove markdown code blocks if present)
            if sql_query.startswith("```"):
                lines = sql_query.split("\n")
                if lines[0].strip().startswith("```"):
                     lines = lines[1:]
                if lines[-1].strip() == "```":
                    lines = lines[:-1]
                sql_query = "\n".join(lines).strip()
            
            return sql_query
            
        except Exception as e:
            logger.error(f"Error generating SQL: {e}")
            raise
    
    def _format_schemas(self, table_schemas: Dict[str, CSVMetadata]) -> str:
        """Format table schemas for the prompt."""
        schema_parts = []
        for table_name, metadata in table_schemas.items():
            columns_str = ", ".join([
                f"{col} ({dtype})" 
                for col, dtype in metadata.column_types.items()
            ])
            schema_parts.append(
                f"Table: {table_name}\n"
                f"Description: {metadata.description}\n"
                f"Columns: {columns_str}\n"
                f"Row count: {metadata.num_rows}"
            )
        return "\n\n".join(schema_parts)
    
    def synthesize_answer(
        self, 
        user_question: str, 
        sql_query: str, 
        results: List[Dict[str, Any]]
    ) -> str:
        """
        Synthesize a natural language answer from query results.
        
        Args:
            user_question: Original question
            sql_query: SQL query that was executed
            results: Query results
            
        Returns:
            Natural language answer
        """
        try:
            if not results:
                return "No results found for your query."
            
            # Format results
            results_str = str(results[:10])  # Limit to first 10 rows
            
            prompt = f"""Based on the following query results, provide a clear and concise answer to the user's question.

User Question: {user_question}

SQL Query: {sql_query}

Results:
{results_str}

Provide a natural language answer that directly addresses the question. Include specific numbers and insights from the results."""
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error synthesizing answer: {e}")
            # Fallback to showing raw results
            return f"Query executed successfully. Results: {results[:5]}"


# Global query agent instance
query_agent = QueryAgent()
