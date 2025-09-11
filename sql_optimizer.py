"""
SQL Optimization Agent

This module provides SQL query optimization capabilities using LLM-powered analysis.
It analyzes generated SQL queries and suggests optimizations for better performance.
"""

import re
import time
from typing import Dict, List, Tuple, Optional
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()

class SQLOptimizer:
    """SQL query optimization agent."""
    
    def __init__(self, model_name: str = "gpt-4-turbo"):
        self.llm = ChatOpenAI(model=model_name, temperature=0)
        self.optimization_prompt = self._create_optimization_prompt()
        self.analysis_prompt = self._create_analysis_prompt()
    
    def _create_optimization_prompt(self) -> ChatPromptTemplate:
        """Create the optimization prompt template."""
        return ChatPromptTemplate.from_messages([
            ("system", """You are a SQL optimization expert. Your task is to analyze and optimize SQL queries for better performance.

Given a SQL query and database schema, provide:
1. An optimized version of the query
2. Specific optimizations applied
3. Performance impact assessment
4. Explanation of changes

Optimization techniques to consider:
- Index usage optimization
- JOIN order optimization
- WHERE clause optimization
- SELECT clause optimization (avoid SELECT *)
- Subquery to JOIN conversion
- LIMIT usage for large result sets
- Proper use of DISTINCT
- Date/time filtering optimization

Rules:
- Maintain the same query logic and results
- Only suggest realistic optimizations for SQLite
- Explain each optimization clearly
- If no optimization is needed, say so

Database Schema:
{schema}

Original Query:
{query}"""),
            ("human", "Please optimize this SQL query and explain your optimizations.")
        ])
    
    def _create_analysis_prompt(self) -> ChatPromptTemplate:
        """Create the query analysis prompt template."""
        return ChatPromptTemplate.from_messages([
            ("system", """You are a SQL performance analyst. Analyze the given SQL query and provide insights.

Provide analysis on:
1. Query complexity (Simple/Medium/Complex)
2. Potential performance bottlenecks
3. Resource usage estimation
4. Scalability concerns
5. Best practices compliance

Database Schema:
{schema}

Query to analyze:
{query}"""),
            ("human", "Please analyze this SQL query for performance characteristics.")
        ])
    
    def optimize_query(self, query: str, schema: str) -> Dict[str, str]:
        """
        Optimize a SQL query and return optimization details.
        
        Args:
            query: The SQL query to optimize
            schema: Database schema information
            
        Returns:
            Dictionary with optimization results
        """
        try:
            # Get optimization suggestions
            optimization_chain = self.optimization_prompt | self.llm
            optimization_result = optimization_chain.invoke({
                "query": query,
                "schema": schema
            })
            
            # Parse the optimization response
            optimization_text = optimization_result.content
            
            # Extract optimized query (look for SQL code blocks)
            optimized_query = self._extract_sql_from_response(optimization_text)
            if not optimized_query:
                optimized_query = query  # Fallback to original if extraction fails
            
            return {
                "original_query": query,
                "optimized_query": optimized_query,
                "optimization_details": optimization_text,
                "status": "success"
            }
            
        except Exception as e:
            return {
                "original_query": query,
                "optimized_query": query,
                "optimization_details": f"Error during optimization: {str(e)}",
                "status": "error"
            }
    
    def analyze_query(self, query: str, schema: str) -> Dict[str, str]:
        """
        Analyze a SQL query for performance characteristics.
        
        Args:
            query: The SQL query to analyze
            schema: Database schema information
            
        Returns:
            Dictionary with analysis results
        """
        try:
            analysis_chain = self.analysis_prompt | self.llm
            analysis_result = analysis_chain.invoke({
                "query": query,
                "schema": schema
            })
            
            return {
                "query": query,
                "analysis": analysis_result.content,
                "status": "success"
            }
            
        except Exception as e:
            return {
                "query": query,
                "analysis": f"Error during analysis: {str(e)}",
                "status": "error"
            }
    
    def _extract_sql_from_response(self, response_text: str) -> Optional[str]:
        """Extract SQL query from LLM response."""
        # Look for SQL code blocks
        sql_pattern = r'```sql\n(.*?)\n```'
        matches = re.findall(sql_pattern, response_text, re.DOTALL | re.IGNORECASE)
        
        if matches:
            return matches[0].strip()
        
        # Look for SQL code blocks without language specification
        code_pattern = r'```\n(.*?)\n```'
        matches = re.findall(code_pattern, response_text, re.DOTALL)
        
        if matches:
            # Check if it looks like SQL
            potential_sql = matches[0].strip()
            if any(keyword in potential_sql.upper() for keyword in ['SELECT', 'FROM', 'WHERE', 'JOIN']):
                return potential_sql
        
        return None
    
    def compare_queries(self, original: str, optimized: str) -> Dict[str, any]:
        """
        Compare two queries and provide metrics.
        
        Args:
            original: Original SQL query
            optimized: Optimized SQL query
            
        Returns:
            Dictionary with comparison metrics
        """
        return {
            "original_length": len(original),
            "optimized_length": len(optimized),
            "complexity_reduction": self._estimate_complexity_reduction(original, optimized),
            "estimated_improvement": self._estimate_performance_improvement(original, optimized)
        }
    
    def _estimate_complexity_reduction(self, original: str, optimized: str) -> str:
        """Estimate complexity reduction between queries."""
        original_upper = original.upper()
        optimized_upper = optimized.upper()
        
        # Count various SQL elements
        original_joins = original_upper.count('JOIN')
        optimized_joins = optimized_upper.count('JOIN')
        
        original_subqueries = original_upper.count('SELECT') - 1  # Subtract main SELECT
        optimized_subqueries = optimized_upper.count('SELECT') - 1
        
        if optimized_joins < original_joins or optimized_subqueries < original_subqueries:
            return "Reduced"
        elif optimized_joins > original_joins or optimized_subqueries > original_subqueries:
            return "Increased"
        else:
            return "Similar"
    
    def _estimate_performance_improvement(self, original: str, optimized: str) -> str:
        """Estimate performance improvement."""
        # This is a simplified heuristic - in practice, you'd want actual execution plans
        improvements = []
        
        original_upper = original.upper()
        optimized_upper = optimized.upper()
        
        # Check for SELECT * removal
        if 'SELECT *' in original_upper and 'SELECT *' not in optimized_upper:
            improvements.append("Column selection optimization")
        
        # Check for LIMIT addition
        if 'LIMIT' not in original_upper and 'LIMIT' in optimized_upper:
            improvements.append("Result set limitation")
        
        # Check for WHERE clause improvements
        if original_upper.count('WHERE') < optimized_upper.count('WHERE'):
            improvements.append("Additional filtering")
        
        # Check for index hints or optimizations
        if 'INDEX' in optimized_upper and 'INDEX' not in original_upper:
            improvements.append("Index utilization")
        
        if improvements:
            return f"Potential improvements: {', '.join(improvements)}"
        else:
            return "Minimal expected improvement"


# Example usage and testing
if __name__ == "__main__":
    optimizer = SQLOptimizer()
    
    # Sample query and schema for testing
    test_query = """
    SELECT * FROM products p, sales s 
    WHERE p.product_id = s.product_id 
    AND p.category = 'Electronics'
    """
    
    test_schema = """
    Table: products
      - product_id (INTEGER) PRIMARY KEY
      - name (TEXT)
      - category (TEXT)
      - price (REAL)

    Table: sales
      - sale_id (INTEGER) PRIMARY KEY
      - product_id (INTEGER)
      - quantity (INTEGER)
      - sale_date (TEXT)
      - region (TEXT)
    """
    
    print("Testing SQL Optimizer...")
    print("\nOriginal Query:")
    print(test_query)
    
    # Test optimization
    result = optimizer.optimize_query(test_query, test_schema)
    print(f"\nOptimization Status: {result['status']}")
    print(f"\nOptimized Query:")
    print(result['optimized_query'])
    print(f"\nOptimization Details:")
    print(result['optimization_details'])
    
    # Test analysis
    analysis = optimizer.analyze_query(test_query, test_schema)
    print(f"\nQuery Analysis:")
    print(analysis['analysis'])
