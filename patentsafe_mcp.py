from mcp.server.fastmcp import FastMCP
import requests
from typing import List, Dict, Set, Optional
from pydantic import BaseModel
from datetime import datetime, date
import argparse
import sys

# Create an MCP server
mcp = FastMCP("Patent Safe")


class ServerInfoResponse(BaseModel):
    """Response from the /connect endpoint containing server information"""
    server_version: str
    user_id: str
    context_header: str
    metadata_fields: List[str]


def initialize_server(base_url: str, auth_token: str) -> ServerInfoResponse:
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

        return ServerInfoResponse.model_validate(response.json())

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
    metadataValues: Dict[str, Set[str | date | int]]


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
def search_documents(lucene_query_string: str,
                     author_id: Optional[str] = None,
                     submission_date_range_start: Optional[datetime] = None,
                     submission_date_range_end: Optional[datetime] = None) -> List[PSDocument]:
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
        response = requests.post(url, headers=headers, json={
            "luceneQuery": lucene_query_string,
            "authorId": author_id,
            "submissionDateRangeStart": submission_date_range_start.isoformat() if submission_date_range_start else None,
            "submissionDateRangeEnd": submission_date_range_end.isoformat() if submission_date_range_end else None,
        })
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
    parser.add_argument("--prefix", required=False, help="Prefix for tool names")
    args = parser.parse_args()

    # Initialize connection and gather server metadata
    server_info = initialize_server(args.base_url, args.auth_token)
    print(f"Connected to PatentSafe at {BASE_URL}")
    print(f"Available metadata fields: {', '.join(sorted(server_info.metadata_fields))}")

    # Manually add the tools so we can do name prefixing and add some additional stuff to the descriptions based on the
    # server.
    mcp.add_tool(
        fn=get_document,
        name=f"{args.tool_prefix}_get_document",
        description=get_document.__doc__
    )

    mcp.add_tool(
        fn=search_documents,
        name=f"{args.tool_prefix}_search_documents",
        description=get_document.__doc__
    )

    mcp.run()


if __name__ == "__main__":
    main()
