# Retail Insights Assistant 

A GenAI-powered Retail Insights Assistant built with **Streamlit**, **LangGraph**, **ChromaDB**, and **DuckDB** for analyzing large-scale retail sales data.

## Features

### Section 1: Single CSV Analysis
- **Summarize**: Generate AI-powered insights and summaries
- ** Ask**: Query specific CSV files with natural language
- **Save to KB**: Store CSV metadata and data in persistent Knowledge Base

### Section 2: Knowledge Base Q&A
- ** Query**: Ask questions across multiple saved CSVs
- ** Multi-Agent**: LangGraph orchestrates intelligent query routing and execution
- **Validation**: Automated `ValidationAgent` ensures SQL results are accurate and non-empty
- **Scalable**: Two-stage retrieval (Vector Search + LLM Filtering) for high precision

## Architecture

- **Frontend**: Streamlit UI with two sections
- **Agents**: LangGraph workflow with:
    - `Router`: Determines intent (Summary vs Query)
    - `QueryAgent`: Generates DuckDB SQL with self-correction
    - `ValidationAgent`: Verifies query results against business logic
    - `SummarizationAgent`: Generates qualitative insights
- **Vector DB**: ChromaDB for semantic search of table metadata
- **SQL DB**: DuckDB for efficient CSV querying (Compute-Storage Separation)
- **LLM**: Google Gemini for natural language understanding and SQL generation
- **Monitoring**: Structured JSON logging for observability

## Setup

### Prerequisites
- Python 3.9+
- Google Gemini API key

### Installation

1. **Clone the repository**
```bash
cd /Users/krishna/Downloads/retail_assistant
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment**
```bash
cp .env.example .env
```

Edit `.env` and add your Google API key:
```
GOOGLE_API_KEY=your_actual_api_key_here
```

### Running the Application

```bash
# Option 1: Startup script
./run.sh

# Option 2: Manual
streamlit run streamlit_app.py
```

The app will open in your browser at `http://localhost:8501`

## Project Structure

```
retail_assistant/
├── streamlit_app.py              # Main Streamlit UI
├── app/
│   ├── agents/
│   │   ├── workflow.py           # LangGraph workflow (Orchestrator)
│   │   ├── query_agent.py        # SQL generation & execution
│   │   ├── validation_agent.py   # [NEW] Result verification
│   │   └── summarization_agent.py
│   ├── services/
│   │   ├── catalog_service.py    # ChromaDB operations
│   │   ├── sql_service.py        # DuckDB operations
│   │   ├── ingestion_service.py  # Metadata extraction
│   │   └── session_service.py    # Temporary data management
│   ├── core/
│   │   ├── config.py             # Configuration
│   │   ├── logger.py             # [NEW] Structured logging
│   │   └── prompts.py            # LLM prompts
│   └── models/
│       └── schemas.py            # Pydantic models
├── data/
│   ├── kb/                       # Persistent storage
│   └── temp/                     # Temporary uploads
├── docs/                         # Documentation & Architecture
└── requirements.txt
```

## Logs & Monitoring

The application now uses structured JSON logging. Logs are printed to stdout and can be ingested by any log aggregation tool.

Example Log:
```json
{"timestamp": "2024-01-28...", "level": "INFO", "logger": "app.agents.workflow", "message": "Executed query_node", "duration_seconds": 1.2, "status": "success"}
```

## Scalability

The architecture is designed to handle **100GB+ datasets**:

- **Metadata Catalog**: Only table schemas/descriptions are indexed in ChromaDB
- **On-Demand Loading**: DuckDB loads only relevant tables for each query
- **Vector Search**: Semantic search finds top-10 relevant tables
- **LLM Filtering**: A second pass filters these 10 candidates to the exact matches, reducing context window usage.

