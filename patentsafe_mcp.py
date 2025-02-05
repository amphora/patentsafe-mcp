from mcp.server.fastmcp import FastMCP
import requests
from typing import List, Dict, Set
from enum import Enum
from pydantic import BaseModel
from datetime import datetime, date
import argparse

# Create an MCP server
mcp = FastMCP("Patent Safe")


class DocumentLocation(str, Enum):
    PERSONAL_INTRAY = "personal-intray"
    GLOBAL_INTRAY = "global-intray"
    LIBRARY = "library"


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
    args = parser.parse_args()

    global BASE_URL, API_BASE_URL, AUTH_TOKEN
    BASE_URL = args.base_url
    API_BASE_URL = f"{BASE_URL}/api/mcp"
    AUTH_TOKEN = args.auth_token

    mcp.run()

if __name__ == "__main__":
    main()
