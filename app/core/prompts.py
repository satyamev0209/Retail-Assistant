"""LLM prompts for different agents."""

SUMMARIZATION_PROMPT = """You are a data analyst expert. Analyze the provided CSV data and generate a comprehensive summary.

CSV Information:
- File name: {file_name}
- Number of rows: {num_rows}
- Columns: {columns}
- Sample data:
{sample_data}

Provide a concise summary including:
1. Overview of the dataset
2. Key insights and patterns
3. Notable statistics (totals, averages, trends)
4. Any anomalies or interesting findings

Keep the summary clear, actionable, and business-focused.
"""

QUERY_GENERATION_PROMPT = """You are a SQL expert. Generate a DuckDB SQL query to answer the user's question.

Available Tables:
{table_schemas}

User Question: {user_question}

Generate ONLY the SQL query without any explanation. The query should:
1. Be syntactically correct for DuckDB
2. Answer the user's question accurately
3. Use appropriate aggregations and filters
4. Return results in a clear format

SQL Query:"""

VALIDATION_PROMPT = """You are a data validation expert. Review the SQL query results and determine if they correctly answer the user's question.

User Question: {user_question}
SQL Query: {sql_query}
Query Results:
{results}

Evaluate:
1. Does the result answer the question?
2. Is the data format appropriate?
3. Are there any errors or anomalies?

If valid, respond with: VALID
If invalid, respond with: INVALID - [brief reason]
"""

ROUTER_PROMPT = """You are a routing agent. Classify the user's intent.

User Input: {user_input}

Classify as one of:
- SUMMARIZE: User wants a summary or overview of data
- QUERY: User has a specific question about the data

Respond with only: SUMMARIZE or QUERY
"""

METADATA_DESCRIPTION_PROMPT = """Generate a concise description of this CSV file for semantic search.

File name: {file_name}
Columns: {columns}
Sample values:
{sample_values}

Description (1-2 sentences):"""
