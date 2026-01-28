"""LangGraph workflow for orchestrating agents."""
from typing import TypedDict, Annotated, Literal, List, Dict
from langgraph.graph import StateGraph, END
from app.agents.summarization_agent import summarization_agent
from app.agents.query_agent import query_agent
from app.agents.validation_agent import validation_agent
from app.services.catalog_service import catalog_service
from app.services.sql_service import sql_service
from app.services.ingestion_service import ingestion_service
from app.models.schemas import CSVMetadata
from app.core.logger import get_logger, log_execution_time
import google.generativeai as genai
from app.core.config import settings

logger = get_logger(__name__)

# Configure Gemini for Schema Selection
genai.configure(api_key=settings.google_api_key)
model = genai.GenerativeModel(settings.model_name)


class WorkflowState(TypedDict):
    """State for the workflow."""
    user_input: str
    intent: str  # "summarize" or "query"
    file_path: str
    session_id: str
    use_kb: bool
    relevant_tables: list[str]
    table_schemas: dict[str, CSVMetadata]
    sql_query: str
    query_results: list[dict]
    final_answer: str
    error: str
    # Validation fields
    validation_error: str
    retry_count: int


@log_execution_time(logger)
def summarize_node(state: WorkflowState) -> WorkflowState:
    """Node for summarization."""
    try:
        summary = summarization_agent.summarize(state["file_path"])
        state["final_answer"] = summary
    except Exception as e:
        logger.error(f"Error in summarize node: {e}")
        state["error"] = str(e)
    return state


@log_execution_time(logger)
def query_node(state: WorkflowState) -> WorkflowState:
    """Node for query processing."""
    try:
        # Get table schemas
        table_schemas = state.get("table_schemas", {})
        
        if not table_schemas:
            state["error"] = "No tables available for querying"
            return state
        
        # Pass validation error as context if retrying
        error_context = state.get("validation_error")
        if error_context:
            logger.info(f"Retrying query generation with error context: {error_context}")

        # Generate and execute query
        # Note: We modifying query_agent locally to accept error_context in generate_and_execute_query would be ideal
        # But for now, we rely on the agent's internal retry or just regeneration
        # Ideally query_agent.generate_and_execute_query should take error_context
        
        # HACK: Temporarily injecting error into prompt via question if needed, 
        # or we update query_agent to accept it. 
        # Plan: I will update query_agent.py next to accept error_context publically.
        
        sql_query, results = query_agent.generate_and_execute_query(
            state["user_input"],
            table_schemas,
            error_context=error_context
        )
        
        state["sql_query"] = sql_query
        state["query_results"] = results
        
    except Exception as e:
        logger.error(f"Error in query node: {e}")
        state["error"] = str(e)
    
    return state


@log_execution_time(logger)
def validate_node(state: WorkflowState) -> WorkflowState:
    """Node for validating query results."""
    try:
        if state.get("error"):
            return state
            
        validation = validation_agent.validate(
            state["user_input"],
            state["sql_query"],
            state["query_results"]
        )
        
        if validation["valid"]:
            # Valid result, clear error
            state["validation_error"] = None
        else:
            # Invalid, set error and increment retry
            state["validation_error"] = validation["reason"]
            state["retry_count"] = state.get("retry_count", 0) + 1
            logger.warning(f"Validation failed: {validation['reason']} (Retry {state['retry_count']})")
            
    except Exception as e:
        logger.error(f"Error in validation node: {e}")
        # Continue if validation errors out
        state["validation_error"] = None
        
    return state


@log_execution_time(logger)
def retrieve_tables_node(state: WorkflowState) -> WorkflowState:
    """Node for retrieving relevant tables from KB."""
    try:
        if state["use_kb"]:
            # 1. Search KB for candidates (fetch more for filtering)
            candidates = catalog_service.search_relevant_tables(
                state["user_input"], 
                top_k=10
            )
            
            if not candidates:
                state["error"] = "No relevant tables found in knowledge base"
                return state
                
            # 2. LLM Comparison / Selection Step
            # Create a prompt to select the best tables
            candidate_str = "\n".join([
                f"- Table: {c.table_name}, Columns: {', '.join(c.columns)}, Desc: {c.description}" 
                for c in candidates
            ])
            
            selection_prompt = f"""You are a database expert. Select the most relevant tables for the user's question.
            
            User Question: {state["user_input"]}
            
            Candidate Tables:
            {candidate_str}
            
            Return ONLY the names of the relevant tables, separated by commas. If none are relevant, return nothing."""
            
            response = model.generate_content(selection_prompt)
            selected_names = [n.strip() for n in response.text.split(",") if n.strip()]
            
            # Filter candidates
            final_selection = [c for c in candidates if c.table_name in selected_names]
            
            # Fallback if LLM selects nothing but we have candidates (be safe)
            if not final_selection and candidates:
                final_selection = candidates[:3] # default top 3
            
            # Build table schemas dict
            table_schemas = {meta.table_name: meta for meta in final_selection}
            state["table_schemas"] = table_schemas
            state["relevant_tables"] = list(table_schemas.keys())
            
            logger.info(f"Selected {len(final_selection)} tables after LLM filtering")
            
        else:
            # Use the uploaded file (already loaded as temp table)
            # Sanitize session_id to match what was created in DB
            safe_session_id = state["session_id"].replace("-", "_")
            table_name = f"temp_{safe_session_id}_upload"
            
            # Extract metadata
            metadata = ingestion_service.extract_metadata(
                state["file_path"],
                table_name=table_name
            )
            state["table_schemas"] = {metadata.table_name: metadata}
            state["relevant_tables"] = [metadata.table_name]
        
    except Exception as e:
        logger.error(f"Error in retrieve tables node: {e}")
        state["error"] = str(e)
    
    return state


@log_execution_time(logger)
def synthesize_node(state: WorkflowState) -> WorkflowState:
    """Node for synthesizing final answer."""
    try:
        if state.get("error"):
            return state
            
        answer = query_agent.synthesize_answer(
            state["user_input"],
            state["sql_query"],
            state["query_results"]
        )
        state["final_answer"] = answer
    except Exception as e:
        logger.error(f"Error in synthesize node: {e}")
        state["error"] = str(e)
    return state


def route_intent(state: WorkflowState) -> Literal["summarize", "query"]:
    """Route based on intent."""
    if state["intent"] == "summarize":
        return "summarize"
    else:
        return "query"


def check_validation(state: WorkflowState) -> Literal["retry", "end"]:
    """Check validation status."""
    if state.get("validation_error") and state.get("retry_count", 0) < 3:
        return "retry"
    return "end"


# Build the graph
workflow = StateGraph(WorkflowState)

# Add nodes
workflow.add_node("summarize", summarize_node)
workflow.add_node("retrieve_tables", retrieve_tables_node)
workflow.add_node("query", query_node)
workflow.add_node("validate", validate_node)
workflow.add_node("synthesize", synthesize_node)

# Add edges
workflow.set_conditional_entry_point(
    route_intent,
    {
        "summarize": "summarize",
        "query": "retrieve_tables"
    }
)

workflow.add_edge("summarize", END)
workflow.add_edge("retrieve_tables", "query")
workflow.add_edge("query", "validate")

workflow.add_conditional_edges(
    "validate",
    check_validation,
    {
        "retry": "query",
        "end": "synthesize"
    }
)

workflow.add_edge("synthesize", END)

# Compile the graph
app = workflow.compile()
