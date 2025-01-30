from mcp.server.fastmcp import FastMCP
import requests
from typing import List, Dict
from enum import Enum

# Create an MCP server
mcp = FastMCP("Patent Safe")

BASE_URL = "http://localhost:8080"
API_BASE_URL = f"{BASE_URL}/api/mcp"
USER_ID = "user123"


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
def list_documents(location: DocumentLocation) -> List[Dict]:
    """
    List documents from a specific location.

    Args:
        location: The location to list documents from (personal-intray, global-intray, or library)

    Returns:
        List of documents in the specified location

    Raises:
        Exception: If the documents cannot be accessed
    """
    url = f"{API_BASE_URL}/documents/list/{location}"
    headers = {"X-User-Id": USER_ID}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        if response.status_code == 401:
            raise Exception("Unauthorized - invalid user ID")
        elif response.status_code == 400:
            raise Exception(f"Invalid location: {location}")
        else:
            raise Exception(f"Failed to list documents: {str(e)}")


@mcp.tool()
def search_documents(search_text: str) -> List[Dict]:
    """
    Search for documents using full text search.

    Args:
        search_text: The text to search for

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
        response = requests.post(url, headers=headers, json=search_text)
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
