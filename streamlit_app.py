"""Main Streamlit application for Retail Insights Assistant."""
import streamlit as st
import pandas as pd
from pathlib import Path
import uuid
import os

from app.agents.workflow import app as workflow_app
from app.services.catalog_service import catalog_service
from app.services.sql_service import sql_service
from app.services.ingestion_service import ingestion_service
from app.services.session_service import session_service
from app.core.config import settings

# Page config
st.set_page_config(
    page_title="Retail Insights Assistant",
    page_icon="📊",
    layout="wide"
)

# Initialize session state
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "uploaded_file_path" not in st.session_state:
    st.session_state.uploaded_file_path = None

if "temp_table_name" not in st.session_state:
    st.session_state.temp_table_name = None


def save_uploaded_file(uploaded_file) -> str:
    """Save uploaded file to temp directory."""
    temp_dir = Path(settings.temp_data_path)
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = temp_dir / f"{st.session_state.session_id}_{uploaded_file.name}"
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return str(file_path)


def cleanup_temp_data():
    """Clean up temporary data for current session."""
    session_service.cleanup_session(st.session_state.session_id)
    st.session_state.uploaded_file_path = None
    st.session_state.temp_table_name = None


# Main UI
st.title("📊 Retail Insights Assistant")
st.markdown("*GenAI-powered analytics for retail data*")

# Create tabs for two sections
tab1, tab2 = st.tabs(["📁 Single CSV Analysis", "🗄️ Knowledge Base Q&A"])

# ============================================================================
# SECTION 1: Single CSV Analysis
# ============================================================================
with tab1:
    st.header("Upload and Analyze CSV")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type=["csv"],
        key="csv_uploader"
    )
    
    if uploaded_file is not None:
        # Save file
        if st.session_state.uploaded_file_path is None:
            file_path = save_uploaded_file(uploaded_file)
            st.session_state.uploaded_file_path = file_path
            session_service.register_temp_file(st.session_state.session_id, file_path)
        
        # Show preview
        st.subheader("Data Preview")
        df = pd.read_csv(st.session_state.uploaded_file_path)
        st.dataframe(df.head(10), use_container_width=True)
        st.caption(f"Total rows: {len(df)} | Total columns: {len(df.columns)}")
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        
        # Button 1: Summarize
        with col1:
            if st.button("📝 Summarize", use_container_width=True):
                with st.spinner("Generating summary..."):
                    try:
                        # Run workflow
                        result = workflow_app.invoke({
                            "user_input": "Summarize this data",
                            "intent": "summarize",
                            "file_path": st.session_state.uploaded_file_path,
                            "session_id": st.session_state.session_id,
                            "use_kb": False,
                            "relevant_tables": [],
                            "table_schemas": {},
                            "sql_query": "",
                            "query_results": [],
                            "final_answer": "",
                            "error": ""
                        })
                        
                        if result.get("error"):
                            st.error(f"Error: {result['error']}")
                        else:
                            st.success("Summary Generated!")
                            st.markdown("### 📊 Insights")
                            st.markdown(result["final_answer"])
                    except Exception as e:
                        st.error(f"Error generating summary: {e}")
        
        # Button 2: Ask
        with col2:
            if st.button("💬 Ask", use_container_width=True):
                st.session_state.show_ask_input = True
        
        # Button 3: Save to KB
        with col3:
            if st.button("💾 Save to KB", use_container_width=True):
                with st.spinner("Saving to Knowledge Base..."):
                    try:
                        # Extract metadata
                        metadata = ingestion_service.extract_metadata(
                            st.session_state.uploaded_file_path
                        )
                        
                        # Add to catalog
                        catalog_service.add_to_kb(metadata)
                        
                        # Load to SQL DB
                        sql_service.load_csv_to_db(
                            st.session_state.uploaded_file_path,
                            metadata.table_name,
                            is_temp=False
                        )
                        
                        st.success(f"✅ Saved to Knowledge Base as '{metadata.table_name}'")
                        st.info(f"Description: {metadata.description}")
                    except Exception as e:
                        st.error(f"Error saving to KB: {e}")
        
        # Ask input (shown when Ask button is clicked)
        if st.session_state.get("show_ask_input", False):
            st.markdown("---")
            st.subheader("Ask a Question")
            
            question = st.text_input(
                "Enter your question about this CSV:",
                placeholder="e.g., What is the total sales amount?"
            )
            
            col_ask, col_cancel = st.columns([1, 1])
            
            with col_ask:
                if st.button("Submit Question", use_container_width=True) and question:
                    with st.spinner("Processing your question..."):
                        try:
                            # Load CSV to temp table
                            # Sanitize session_id to remove hyphens for SQL compatibility
                            safe_session_id = st.session_state.session_id.replace("-", "_")
                            temp_table = f"temp_{safe_session_id}_upload"
                            sql_service.load_csv_to_db(
                                st.session_state.uploaded_file_path,
                                temp_table,
                                is_temp=True
                            )
                            session_service.register_temp_table(
                                st.session_state.session_id,
                                temp_table
                            )
                            st.session_state.temp_table_name = temp_table
                            
                            # Run workflow
                            result = workflow_app.invoke({
                                "user_input": question,
                                "intent": "query",
                                "file_path": st.session_state.uploaded_file_path,
                                "session_id": st.session_state.session_id,
                                "use_kb": False,
                                "relevant_tables": [],
                                "table_schemas": {},
                                "sql_query": "",
                                "query_results": [],
                                "final_answer": "",
                                "error": ""
                            })
                            
                            if result.get("error"):
                                st.error(f"Error: {result['error']}")
                            else:
                                st.success("Answer Generated!")
                                st.markdown("### 💡 Answer")
                                st.markdown(result["final_answer"])
                                
                                if result.get("sql_query"):
                                    with st.expander("🔍 View SQL Query"):
                                        st.code(result["sql_query"], language="sql")
                                
                                if result.get("query_results"):
                                    with st.expander("📊 View Results"):
                                        st.dataframe(
                                            pd.DataFrame(result["query_results"]),
                                            use_container_width=True
                                        )
                        except Exception as e:
                            st.error(f"Error processing question: {e}")
            
            with col_cancel:
                if st.button("Cancel", use_container_width=True):
                    st.session_state.show_ask_input = False
                    st.rerun()
        
        # Cleanup button
        st.markdown("---")
        if st.button("🗑️ Clear Upload & Cleanup"):
            cleanup_temp_data()
            st.rerun()

# ============================================================================
# SECTION 2: Knowledge Base Q&A
# ============================================================================
with tab2:
    st.header("Query Knowledge Base")
    
    # Show available tables
    st.subheader("Available Tables in KB")
    kb_tables = catalog_service.list_all_tables()
    
    if kb_tables:
        st.info(f"📚 {len(kb_tables)} tables available")
        
        with st.expander("View All Tables"):
            for table in kb_tables:
                metadata = catalog_service.get_metadata(table)
                if metadata:
                    st.markdown(f"**{table}**")
                    st.caption(f"Description: {metadata.description}")
                    st.caption(f"Columns: {', '.join(metadata.columns[:5])}...")
                    st.markdown("---")
    else:
        st.warning("No tables in Knowledge Base. Upload and save CSVs in Section 1.")
    
    # Question input
    st.subheader("Ask a Question")
    kb_question = st.text_area(
        "Enter your question:",
        placeholder="e.g., Which region had the highest sales in Q3?",
        height=100
    )
    
    if st.button("🔍 Search & Answer", use_container_width=True) and kb_question:
        if not kb_tables:
            st.error("No tables in Knowledge Base. Please save some CSVs first.")
        else:
            with st.spinner("Searching knowledge base and generating answer..."):
                try:
                    # Run workflow
                    result = workflow_app.invoke({
                        "user_input": kb_question,
                        "intent": "query",
                        "file_path": "",
                        "session_id": st.session_state.session_id,
                        "use_kb": True,
                        "relevant_tables": [],
                        "table_schemas": {},
                        "sql_query": "",
                        "query_results": [],
                        "final_answer": "",
                        "error": ""
                    })
                    
                    if result.get("error"):
                        st.error(f"Error: {result['error']}")
                    else:
                        st.success("Answer Generated!")
                        
                        # Show relevant tables
                        if result.get("relevant_tables"):
                            st.info(f"📋 Used tables: {', '.join(result['relevant_tables'])}")
                        
                        # Show answer
                        st.markdown("### 💡 Answer")
                        st.markdown(result["final_answer"])
                        
                        # Show SQL query
                        if result.get("sql_query"):
                            with st.expander("🔍 View SQL Query"):
                                st.code(result["sql_query"], language="sql")
                        
                        # Show results
                        if result.get("query_results"):
                            with st.expander("📊 View Results"):
                                st.dataframe(
                                    pd.DataFrame(result["query_results"]),
                                    use_container_width=True
                                )
                except Exception as e:
                    st.error(f"Error processing question: {e}")

# Sidebar
with st.sidebar:
    st.header("ℹ️ About")
    st.markdown("""
    **Retail Insights Assistant** is a GenAI-powered tool for analyzing retail sales data.
    
    **Features:**
    - 📝 Summarize CSV files
    - 💬 Ask questions about your data
    - 💾 Build a persistent Knowledge Base
    - 🔍 Query across multiple tables
    
    **Powered by:**
    - Google Gemini
    - LangGraph
    - ChromaDB
    - DuckDB
    """)
    
    st.markdown("---")
    st.caption(f"Session ID: {st.session_state.session_id[:8]}...")
    
    if st.button("🔄 Reset Session"):
        cleanup_temp_data()
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()
