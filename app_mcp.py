import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Streamlit page
st.set_page_config(
    page_title="Natural Language to SQL Agent (MCP Version)",
    page_icon="🤖",
    layout="wide"
)

# Main title
st.title("🤖 Natural Language to SQL Agent (MCP Version)")
st.write("Ask a question about sales or products, and the agent will generate and execute the SQL query using MCP (Model Context Protocol).")

# Sidebar with information and examples
with st.sidebar:
    st.header("🔧 Agent Version")
    agent_version = st.radio(
        "Choose agent implementation:",
        ["Original (Direct DB)", "MCP-based"],
        index=1,
        help="Original uses direct database access, MCP-based uses Model Context Protocol server"
    )
    
    st.header("ℹ️ About")
    if agent_version == "MCP-based":
        st.write("""
        This version uses **Model Context Protocol (MCP)** to communicate with a separate 
        database server. The agent sends requests to an MCP server which handles all 
        database operations securely and efficiently.
        """)
    else:
        st.write("""
        This version uses direct database access through LangChain's SQLDatabase utilities.
        """)
    
    st.header("📊 Database Schema")
    st.write("""
    **Products Table:**
    - product_id (INTEGER)
    - name (TEXT)
    - category (TEXT)
    - price (REAL)
    
    **Sales Table:**
    - sale_id (INTEGER)
    - product_id (INTEGER)
    - quantity (INTEGER)
    - sale_date (TEXT)
    - region (TEXT)
    """)
    
    st.header("💡 Example Questions")
    example_questions = [
        "What were the total sales for the 'Electronics' category?",
        "Which product is the most expensive?",
        "Show me all sales that happened in the 'North' region after '2023-10-01'.",
        "What is the average price of products in each category?",
        "Which region had the highest total sales quantity?",
        "List all products that have been sold more than 2 times.",
        "What are the total sales by month?"
    ]
    
    for i, question in enumerate(example_questions, 1):
        if st.button(f"Example {i}", key=f"example_{i}", use_container_width=True):
            st.session_state.user_question = question

# Import the appropriate agent based on selection
if agent_version == "MCP-based":
    try:
        from agent_mcp import compiled_app
        agent_type_display = "🔗 MCP-based Agent"
    except ImportError as e:
        st.error(f"❌ Error importing MCP agent: {str(e)}")
        st.error("Make sure MCP dependencies are installed: `pip install mcp pydantic`")
        st.stop()
else:
    try:
        from agent import compiled_app
        agent_type_display = "🔧 Original Agent"
    except ImportError as e:
        st.error(f"❌ Error importing original agent: {str(e)}")
        st.stop()

# Display current agent type
st.info(f"Using: {agent_type_display}")

# Main interface
user_question = st.text_input(
    "Enter your question:",
    value=st.session_state.get('user_question', ''),
    placeholder="e.g., What were the total sales for Electronics?"
)

# Update session state
if user_question:
    st.session_state.user_question = user_question

if st.button("🚀 Generate & Optimize SQL", type="primary"):
    if not user_question:
        st.error("Please enter a question first!")
    else:
        # Check if OpenAI API key is set
        if not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") == "YOUR_API_KEY_HERE":
            st.error("⚠️ Please set your OpenAI API key in the .env file!")
            st.code('OPENAI_API_KEY="your-actual-api-key-here"', language='bash')
            st.stop()
        
        # Show loading spinner
        with st.spinner(f"🔄 {agent_type_display} is processing your question..."):
            try:
                # Invoke the LangGraph agent
                initial_state = {
                    "question": user_question,
                    "db_schema": "",
                    "sql_query": "",
                    "optimized_query": "",
                    "optimization_details": "",
                    "query_analysis": "",
                    "result": "",
                    "error": ""
                }
                
                result = compiled_app.invoke(initial_state)
                
                # Display results in tabs
                tab1, tab2, tab3 = st.tabs(["🔍 Queries", "📊 Results", "🔬 Analysis"])

                with tab1:
                    st.subheader("Generated SQL Queries")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**📝 Original Query**")
                        if result.get("sql_query"):
                            st.code(result["sql_query"], language='sql')
                        else:
                            st.error("No SQL query was generated.")
                    with col2:
                        st.markdown("**⚡ Optimized Query**")
                        if result.get("optimized_query"):
                            st.code(result["optimized_query"], language='sql')
                            if result.get("optimized_query") != result.get("sql_query"):
                                st.success("✅ Query was optimized")
                            else:
                                st.info("ℹ️ No optimization needed")
                        else:
                            st.warning("No optimized query available.")

                with tab2:
                    st.subheader("Query Result")
                    if result.get("error"):
                        st.error(f"❌ Error: {result['error']}")
                    elif result.get("result"):
                        result_text = result["result"]
                        if result_text and not result_text.startswith("Error"):
                            st.code(result_text, language='text')
                        else:
                            st.warning("No results found or query returned empty result.")
                    else:
                        st.warning("No results to display.")

                with tab3:
                    st.subheader("Optimization Analysis")
                    if result.get("query_analysis"):
                        st.markdown("**🔬 Query Analysis**")
                        st.write(result["query_analysis"])
                    if result.get("optimization_details"):
                        st.markdown("**⚡ Optimization Details**")
                        st.write(result["optimization_details"])
                
                # Show the database schema used
                with st.expander("📋 Database Schema Used"):
                    if result.get("db_schema"):
                        st.code(result["db_schema"], language='text')
                
                # Show agent execution info
                with st.expander("🔍 Agent Execution Details"):
                    st.write(f"**Agent Type:** {agent_type_display}")
                    if agent_version == "MCP-based":
                        st.write("**Communication:** Agent → MCP Client → MCP Server → SQLite Database")
                        st.write("**Benefits:** Secure, scalable, protocol-standardized database access")
                    else:
                        st.write("**Communication:** Agent → LangChain SQLDatabase → SQLite Database")
                        st.write("**Benefits:** Direct, simple database access")
                
            except Exception as e:
                st.error(f"❌ An error occurred: {str(e)}")
                st.write("Please make sure:")
                st.write("1. Your OpenAI API key is correctly set in the .env file")
                st.write("2. The database file (sales.db) exists (run setup_db.py first)")
                st.write("3. All required packages are installed")
                if agent_version == "MCP-based":
                    st.write("4. MCP dependencies are installed: `pip install mcp pydantic`")

# Footer
st.markdown("---")
st.markdown(
    f"""
    <div style='text-align: center; color: gray;'>
        Built with ❤️ using LangGraph, LangChain, MCP, and Streamlit<br>
        Current Agent: {agent_type_display}
    </div>
    """, 
    unsafe_allow_html=True
)

# Instructions for first-time users
if not os.path.exists("sales.db"):
    st.warning("⚠️ Database not found! Please run `python setup_db.py` first to create the sample database.")
