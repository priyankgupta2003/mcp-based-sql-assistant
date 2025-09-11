import os
from typing import TypedDict
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv
from mcp_client import SyncDatabaseMCPClient
from sql_optimizer import SQLOptimizer

# Load environment variables
load_dotenv()

# MCP Client setup
mcp_client = SyncDatabaseMCPClient()

# Optimizer
sql_optimizer = SQLOptimizer()

# LLM setup
llm = ChatOpenAI(model="gpt-4-turbo", temperature=0)

# Agent State
class AgentState(TypedDict):
    question: str
    db_schema: str
    sql_query: str
    optimized_query: str
    optimization_details: str
    query_analysis: str
    result: str
    error: str

def get_schema_node(state: AgentState) -> AgentState:
    """Get the database schema using MCP client."""
    try:
        schema = mcp_client.get_schema()
        state["db_schema"] = schema
        print("✅ Schema retrieved successfully via MCP")
    except Exception as e:
        state["error"] = f"Error getting schema via MCP: {str(e)}"
        print(f"❌ Error getting schema via MCP: {str(e)}")
    
    return state

def generate_sql_node(state: AgentState) -> AgentState:
    """Generate SQL query based on the question and schema."""
    try:
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are a SQL expert. Given a database schema and a user question, 
            generate a single, syntactically correct SQLite query that answers the question.
            
            Rules:
            1. Only use tables and columns that exist in the schema
            2. Use proper SQLite syntax
            3. Return only the SQL query, no explanations
            4. Use appropriate JOINs when needed
            5. Handle aggregations properly
            
            Database Schema:
            {db_schema}"""),
            ("human", "Question: {question}")
        ])
        
        chain = prompt_template | llm
        response = chain.invoke({
            "db_schema": state["db_schema"],
            "question": state["question"]
        })
        
        # Extract the SQL query from the response
        sql_query = response.content.strip()
        
        # Clean up the query (remove markdown formatting if present)
        if sql_query.startswith("```sql"):
            sql_query = sql_query[6:]
        if sql_query.startswith("```"):
            sql_query = sql_query[3:]
        if sql_query.endswith("```"):
            sql_query = sql_query[:-3]
        
        state["sql_query"] = sql_query.strip()
        print(f"✅ SQL query generated: {sql_query.strip()}")
        
    except Exception as e:
        state["error"] = f"Error generating SQL: {str(e)}"
        print(f"❌ Error generating SQL: {str(e)}")
    
    return state

def optimize_sql_node(state: AgentState) -> AgentState:
    """Optimize the generated SQL query using LLM-based optimizer."""
    try:
        if state.get("error") or not state.get("sql_query"):
            return state

        optimization_result = sql_optimizer.optimize_query(
            state["sql_query"],
            state.get("db_schema", "")
        )
        analysis_result = sql_optimizer.analyze_query(
            state["sql_query"],
            state.get("db_schema", "")
        )

        state["optimized_query"] = optimization_result.get("optimized_query", state["sql_query"])
        state["optimization_details"] = optimization_result.get("optimization_details", "")
        state["query_analysis"] = analysis_result.get("analysis", "")

    except Exception as e:
        state["optimized_query"] = state.get("sql_query", "")
        state["optimization_details"] = f"Error optimizing: {str(e)}"
    
    return state

def execute_sql_node(state: AgentState) -> AgentState:
    """Execute the SQL query using MCP client."""
    try:
        if state.get("error"):
            return state
        
        # Use optimized query if available and different
        query_to_run = state.get("optimized_query") or state.get("sql_query", "")
        result = mcp_client.query_database(query_to_run)
        state["result"] = result
        print(f"✅ Query executed successfully via MCP")
        
    except Exception as e:
        state["error"] = f"Error executing SQL via MCP: {str(e)}"
        print(f"❌ Error executing SQL via MCP: {str(e)}")
    
    return state

# Build the graph
def create_graph():
    """Create and compile the LangGraph agent with MCP integration."""
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("get_schema", get_schema_node)
    workflow.add_node("generate_sql", generate_sql_node)
    workflow.add_node("optimize_sql", optimize_sql_node)
    workflow.add_node("execute_sql", execute_sql_node)
    
    # Define edges
    workflow.set_entry_point("get_schema")
    workflow.add_edge("get_schema", "generate_sql")
    workflow.add_edge("generate_sql", "optimize_sql")
    workflow.add_edge("optimize_sql", "execute_sql")
    workflow.add_edge("execute_sql", END)
    
    # Compile the graph
    app = workflow.compile()
    return app

# Create the compiled app
compiled_app = create_graph()
