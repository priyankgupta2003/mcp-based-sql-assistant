"""
MCP Client for SQL Database Operations

This module provides a client interface to communicate with the MCP SQL database server.
It handles the connection, tool calls, and response parsing.
"""

import asyncio
import json
import subprocess
import sys
from typing import Any, Dict, List, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class DatabaseMCPClient:
    """Client for communicating with the SQL database MCP server."""
    
    def __init__(self, server_script_path: str = "mcp_server.py"):
        self.server_script_path = server_script_path
        self.session: Optional[ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        # Start the MCP server as a subprocess
        server_params = StdioServerParameters(
            command=sys.executable,
            args=[self.server_script_path],
        )
        
        # Create stdio client connection
        self.stdio_client = stdio_client(server_params)
        self.read_stream, self.write_stream = await self.stdio_client.__aenter__()
        
        # Initialize the client session
        self.session = ClientSession(self.read_stream, self.write_stream)
        await self.session.initialize()
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
        await self.stdio_client.__aexit__(exc_type, exc_val, exc_tb)
    
    async def query_database(self, query: str) -> str:
        """Execute a SQL query against the database."""
        if not self.session:
            raise RuntimeError("Client session not initialized")
        
        try:
            result = await self.session.call_tool("query_database", {"query": query})
            
            # Extract text content from the result
            if result.content and len(result.content) > 0:
                return result.content[0].text
            else:
                return "No results returned from database."
                
        except Exception as e:
            return f"Error executing query: {str(e)}"
    
    async def get_schema(self) -> str:
        """Get the database schema information."""
        if not self.session:
            raise RuntimeError("Client session not initialized")
        
        try:
            result = await self.session.call_tool("get_schema", {})
            
            # Extract text content from the result
            if result.content and len(result.content) > 0:
                return result.content[0].text
            else:
                return "No schema information available."
                
        except Exception as e:
            return f"Error retrieving schema: {str(e)}"
    
    async def list_tables(self) -> str:
        """List all tables in the database."""
        if not self.session:
            raise RuntimeError("Client session not initialized")
        
        try:
            result = await self.session.call_tool("list_tables", {})
            
            # Extract text content from the result
            if result.content and len(result.content) > 0:
                return result.content[0].text
            else:
                return "No tables found."
                
        except Exception as e:
            return f"Error listing tables: {str(e)}"


class SyncDatabaseMCPClient:
    """Synchronous wrapper for the async MCP client."""
    
    def __init__(self, server_script_path: str = "mcp_server.py"):
        self.server_script_path = server_script_path
        self.loop = None
    
    def _get_event_loop(self):
        """Get or create an event loop."""
        try:
            return asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop
    
    def query_database(self, query: str) -> str:
        """Execute a SQL query against the database (sync)."""
        loop = self._get_event_loop()
        return loop.run_until_complete(self._async_query_database(query))
    
    def get_schema(self) -> str:
        """Get the database schema information (sync)."""
        loop = self._get_event_loop()
        return loop.run_until_complete(self._async_get_schema())
    
    def list_tables(self) -> str:
        """List all tables in the database (sync)."""
        loop = self._get_event_loop()
        return loop.run_until_complete(self._async_list_tables())
    
    async def _async_query_database(self, query: str) -> str:
        """Async implementation of query_database."""
        async with DatabaseMCPClient(self.server_script_path) as client:
            return await client.query_database(query)
    
    async def _async_get_schema(self) -> str:
        """Async implementation of get_schema."""
        async with DatabaseMCPClient(self.server_script_path) as client:
            return await client.get_schema()
    
    async def _async_list_tables(self) -> str:
        """Async implementation of list_tables."""
        async with DatabaseMCPClient(self.server_script_path) as client:
            return await client.list_tables()


# Example usage
if __name__ == "__main__":
    # Test the MCP client
    client = SyncDatabaseMCPClient()
    
    print("Testing MCP Database Client...")
    print("\n1. Getting schema:")
    schema = client.get_schema()
    print(schema)
    
    print("\n2. Listing tables:")
    tables = client.list_tables()
    print(tables)
    
    print("\n3. Querying database:")
    result = client.query_database("SELECT * FROM products LIMIT 3;")
    print(result)
