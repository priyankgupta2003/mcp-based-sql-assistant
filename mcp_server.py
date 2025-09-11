#!/usr/bin/env python3
"""
MCP Server for SQL Database Operations

This server provides database query capabilities through the Model Context Protocol (MCP).
It exposes tools for querying a SQLite database and retrieving schema information.
"""

import asyncio
import json
import sqlite3
import sys
from typing import Any, Dict, List, Optional

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types
from pydantic import AnyUrl


class DatabaseMCPServer:
    """MCP Server for database operations."""
    
    def __init__(self, db_path: str = "sales.db"):
        self.db_path = db_path
        self.server = Server("sql-database-server")
        self.setup_handlers()
    
    def setup_handlers(self):
        """Set up MCP server handlers."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """List available tools."""
            return [
                types.Tool(
                    name="query_database",
                    description="Execute a SQL query against the database and return results",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The SQL query to execute"
                            }
                        },
                        "required": ["query"]
                    }
                ),
                types.Tool(
                    name="get_schema",
                    description="Get the database schema information including all tables and columns",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                types.Tool(
                    name="list_tables",
                    description="List all tables in the database",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: dict[str, Any]
        ) -> list[types.TextContent]:
            """Handle tool calls."""
            
            if name == "query_database":
                return await self._query_database(arguments.get("query", ""))
            elif name == "get_schema":
                return await self._get_schema()
            elif name == "list_tables":
                return await self._list_tables()
            else:
                raise ValueError(f"Unknown tool: {name}")
    
    async def _query_database(self, query: str) -> list[types.TextContent]:
        """Execute a SQL query against the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Execute the query
            cursor.execute(query)
            
            # Get column names
            columns = [description[0] for description in cursor.description] if cursor.description else []
            
            # Fetch results
            rows = cursor.fetchall()
            
            conn.close()
            
            # Format results
            if not rows:
                result = "No results found."
            else:
                # Create a formatted table
                result_lines = []
                if columns:
                    result_lines.append(" | ".join(columns))
                    result_lines.append("-" * len(" | ".join(columns)))
                
                for row in rows:
                    result_lines.append(" | ".join(str(cell) for cell in row))
                
                result = "\n".join(result_lines)
            
            return [types.TextContent(type="text", text=result)]
            
        except Exception as e:
            error_msg = f"Database query error: {str(e)}"
            return [types.TextContent(type="text", text=error_msg)]
    
    async def _get_schema(self) -> list[types.TextContent]:
        """Get the database schema information."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            schema_info = []
            
            for table in tables:
                table_name = table[0]
                schema_info.append(f"\nTable: {table_name}")
                
                # Get column information
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = cursor.fetchall()
                
                for column in columns:
                    col_name = column[1]
                    col_type = column[2]
                    is_nullable = "NOT NULL" if column[3] else "NULL"
                    is_pk = "PRIMARY KEY" if column[5] else ""
                    
                    col_info = f"  - {col_name} ({col_type}) {is_nullable} {is_pk}".strip()
                    schema_info.append(col_info)
            
            conn.close()
            
            result = "\n".join(schema_info)
            return [types.TextContent(type="text", text=result)]
            
        except Exception as e:
            error_msg = f"Schema retrieval error: {str(e)}"
            return [types.TextContent(type="text", text=error_msg)]
    
    async def _list_tables(self) -> list[types.TextContent]:
        """List all tables in the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            conn.close()
            
            if tables:
                table_list = "\n".join([f"- {table[0]}" for table in tables])
                result = f"Tables in database:\n{table_list}"
            else:
                result = "No tables found in database."
            
            return [types.TextContent(type="text", text=result)]
            
        except Exception as e:
            error_msg = f"Table listing error: {str(e)}"
            return [types.TextContent(type="text", text=error_msg)]


async def main():
    """Main function to run the MCP server."""
    # Initialize the database MCP server
    db_server = DatabaseMCPServer()
    
    # Run the server using stdio transport
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await db_server.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="sql-database-server",
                server_version="0.1.0",
                capabilities=db_server.server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
