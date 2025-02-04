from mcp.server.fastmcp import FastMCP
import requests
from typing import List, Dict
from enum import Enum

# Create an MCP server
mcp = FastMCP("Patent Safe")

BASE_URL = "https://food.morescience.com"
API_BASE_URL = f"{BASE_URL}/api/mcp"
USER_ID = "joshua"


class DocumentLocation(str, Enum):
    PERSONAL_INTRAY = "personal-intray"
    GLOBAL_INTRAY = "global-intray"
    LIBRARY = "library"


@mcp.tool()
def get_document(document_id: str) -> dict:
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
    headers = {"X-User-Id": USER_ID}

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
def search_documents(lucene_query_string: str) -> List[Dict]:
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
        "X-User-Id": USER_ID,
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, headers=headers, data=lucene_query_string)
        response.raise_for_status()
        return response.json()

    except requests.RequestException as e:
        if response.status_code == 401:
            raise Exception("Unauthorized - invalid user ID")
        elif response.status_code == 400:
            raise Exception(f"Invalid search query: {str(e)}")
        else:
            raise Exception(f"Failed to search documents: {str(e)}")


# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"


if __name__ == "__main__":
    mcp.run()
