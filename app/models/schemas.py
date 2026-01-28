"""Pydantic models for data validation."""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class CSVMetadata(BaseModel):
    """Metadata for a CSV file."""
    file_name: str
    file_path: str
    table_name: str
    num_rows: int
    num_columns: int
    columns: List[str]
    column_types: Dict[str, str]
    description: str
    sample_values: Dict[str, List[Any]]
    created_at: datetime = Field(default_factory=datetime.now)


class QueryRequest(BaseModel):
    """Request for querying data."""
    question: str
    session_id: Optional[str] = None
    use_kb: bool = False


class QueryResponse(BaseModel):
    """Response from a query."""
    answer: str
    sql_query: Optional[str] = None
    results: Optional[List[Dict[str, Any]]] = None
    sources: Optional[List[str]] = None


class SummaryRequest(BaseModel):
    """Request for summarizing data."""
    file_path: str
    session_id: Optional[str] = None


class SummaryResponse(BaseModel):
    """Response from summarization."""
    summary: str
    metadata: CSVMetadata


class AgentState(BaseModel):
    """State for LangGraph agents."""
    user_input: str
    intent: Optional[str] = None
    file_path: Optional[str] = None
    session_id: Optional[str] = None
    use_kb: bool = False
    relevant_tables: Optional[List[str]] = None
    table_schemas: Optional[Dict[str, CSVMetadata]] = None
    sql_query: Optional[str] = None
    query_results: Optional[List[Dict[str, Any]]] = None
    final_answer: Optional[str] = None
    error: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True
