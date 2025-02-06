from mcp.server.fastmcp import FastMCP
import requests
from typing import List, Dict, Set
from enum import Enum
from pydantic import BaseModel
from datetime import datetime, date
import argparse
import sys

# Create an MCP server
mcp = FastMCP("Patent Safe")


class DocumentLocation(str, Enum):
    PERSONAL_INTRAY = "personal-intray"
    GLOBAL_INTRAY = "global-intray"
    LIBRARY = "library"


class ServerInfoResponse(BaseModel):
    """Response from the /connect endpoint containing server information"""
    server_version: str
    user_id: str
    context_header: str
    metadata_fields: List[str]


class ServerInfo(BaseModel):
    """Information about the PatentSafe server connection"""
    status: str
    base_url: str
    api_version: str = "1.0"  # Current MCP API version
    authenticated: bool
    available_metadata_fields: Set[str] = set()


def initialize_server(base_url: str, auth_token: str) -> ServerInfo:
    """
    Initialize the connection to PatentSafe and gather server metadata.
    This is called at server startup to verify connection and cache server information.

    Returns:
        ServerInfo object containing status and server metadata
    """
    global BASE_URL, API_BASE_URL, AUTH_TOKEN
    BASE_URL = base_url
    API_BASE_URL = f"{BASE_URL}/api/mcp"
    AUTH_TOKEN = auth_token

    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        # Get server information from the connect endpoint
        response = requests.get(
            f"{API_BASE_URL}/connect",
            headers=headers
        )
        response.raise_for_status()
        
        server_data = ServerInfoResponse.model_validate(response.json())
        return ServerInfo(
            status="connected",
            base_url=BASE_URL,
            authenticated=True,
            available_metadata_fields=set(server_data.metadata_fields)
        )

    except requests.RequestException as e:
        error_msg = f"Failed to initialize PatentSafe connection: {str(e)}"
        if hasattr(e, 'response') and e.response is not None:
            if e.response.status_code == 401:
                error_msg = "Authentication failed - invalid token"
            elif e.response.status_code == 404:
                error_msg = "Invalid PatentSafe URL"
        
        print(f"Error: {error_msg}", file=sys.stderr)
        sys.exit(1)


class PSDocument(BaseModel):
    """Represents a PatentSafe document with its metadata"""
    id: str
    title: str
    type: str
    text: str
    createdDate: datetime
    modifiedDate: datetime
    location: str
    authorId: str
    metadataValues: Dict[str, Set[str | date | int]] = {}


@mcp.tool()
def get_document(document_id: str) -> PSDocument:
    """
    Get a document by its ID.

    Args:
        document_id: The ID of the document to get

    Returns:
        Document details including metadata and text content

    Raises:
        Exception: If the document cannot be accessed or doesn't exist
    """
    url = f"{API_BASE_URL}/documents/{document_id}"
    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

    except requests.RequestException as e:
        if response.status_code == 404:
            raise Exception("Document not found or access denied")
        elif response.status_code == 401:
            raise Exception("Unauthorized - invalid user ID")
        elif response.status_code == 403:
            raise Exception("Access denied")
        else:
            raise Exception(f"Failed to fetch document: {str(e)}")


@mcp.tool()
def search_documents(lucene_query_string: str) -> List[PSDocument]:
    """
    Search for documents using full text search using a Lucene query string.

    Args:
        query_string: The lucene query string to use for full text search. The simplest query is simply the text you want
        to search for, for example `red cabbage`. To combine queries join them with `AND` to search for documents
        containing both terms (for example `red cabbage AND green beans`), or use `OR` to search for documents containing
        either term (for example `red cabbage OR green beans`).

    Returns:
        List of matching documents

    Raises:
        Exception: If the search fails or returns an error
    """
    url = f"{API_BASE_URL}/documents/search"
    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, headers=headers, json={"luceneQuery": lucene_query_string})
        response.raise_for_status()
        return response.json()

    except requests.RequestException as e:
        if response.status_code == 401:
            raise Exception("Unauthorized - invalid user ID")
        elif response.status_code == 400:
            raise Exception(f"Invalid search query: {str(e)}")
        else:
            raise Exception(f"Failed to search documents: {str(e)}")


def main():
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description="Patent Safe MCP Server")
    parser.add_argument("base_url", help="PatentSafe base URL")
    parser.add_argument("auth_token", help="Personal authentication token")
    parser.add_argument("tool_prefix", help="Prefix for tool names")
    args = parser.parse_args()

    # Initialize connection and gather server metadata
    server_info = initialize_server(args.base_url, args.auth_token)
    print(f"Connected to PatentSafe at {server_info.base_url}")
    print(f"Available metadata fields: {', '.join(sorted(server_info.available_metadata_fields))}")

    # Update tool names with prefix
    mcp.tool_name_prefix = args.tool_prefix
    mcp.run()

if __name__ == "__main__":
    main()
