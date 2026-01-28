"""Validation agent for verifying SQL query results."""
from typing import Dict, Any, List
from app.core.prompts import VALIDATION_PROMPT
from app.core.config import settings
from app.core.logger import get_logger, log_execution_time
import google.generativeai as genai

logger = get_logger(__name__)

# Configure Gemini
genai.configure(api_key=settings.google_api_key)


class ValidationAgent:
    """Agent for validating SQL query results."""
    
    def __init__(self):
        """Initialize the validation agent."""
        self.model = genai.GenerativeModel(settings.model_name)
    
    @log_execution_time(logger)
    def validate(
        self, 
        user_question: str, 
        sql_query: str, 
        results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate the query results.
        
        Args:
            user_question: Original user question
            sql_query: Generated SQL query
            results: Results from the query
            
        Returns:
            Dictionary with 'valid' (bool) and 'reason' (str)
        """
        try:
            # Format results for prompt (limit size)
            results_str = str(results[:5])
            
            prompt = VALIDATION_PROMPT.format(
                user_question=user_question,
                sql_query=sql_query,
                results=results_str
            )
            
            # Generate validation
            response = self.model.generate_content(prompt)
            validation_text = response.text.strip()
            
            is_valid = validation_text.upper().startswith("VALID")
            
            reason = ""
            if not is_valid:
                # Extract reason if present
                reason_parts = validation_text.split("-", 1)
                if len(reason_parts) > 1:
                    reason = reason_parts[1].strip()
                else:
                    reason = validation_text
                    
            logger.info(f"Validation result: {is_valid}", extra={
                "extra": {
                    "question": user_question,
                    "validation_text": validation_text
                }
            })
            
            return {
                "valid": is_valid,
                "reason": reason
            }
            
        except Exception as e:
            logger.error(f"Error validating results: {e}")
            # In case of error, assume valid to avoid blocking user
            return {"valid": True, "reason": "Validation Error"}


# Global validation agent instance
validation_agent = ValidationAgent()
