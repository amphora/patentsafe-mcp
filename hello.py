# server.py
from mcp.server.fastmcp import FastMCP
import requests
from bs4 import BeautifulSoup
from typing import Optional

# Create an MCP server
mcp = FastMCP("Patent Safe")

BASE_URL = "http://localhost:8089"
cookies = {
    'patentsafe': 'q2ZlJlYia74L39DSYkXvqDkm2PIOxSVpAdVEq9+VGAIm69bqvhIDGv4KnLiOJlYjRaDMZ9cKzqysd/C5XyANYw=='
}


@mcp.tool()
def read_document_text(document_id: str) -> str:
    """
    Read the text content of a document by its ID.
    
    Args:
        document_id: The ID of the document to read

    Returns:
        The text content of the document
        
    Raises:
        Exception: If the document cannot be accessed or doesn't exist
    """
    url = f"{BASE_URL}/documents/text.html"
    params = {"docId": document_id}

    try:
        # Make request to the text endpoint
        response = requests.get(url, params=params, cookies=cookies)
        response.raise_for_status()

        # Parse the HTML response to extract the text content
        soup = BeautifulSoup(response.text, 'html.parser')
        text_content = soup.find('div', class_='ps-document-text')

        if text_content:
            return text_content.get_text(strip=True)
        else:
            raise Exception("Could not find document text content in the response")

    except requests.RequestException as e:
        raise Exception(f"Failed to fetch document text: {str(e)}")


@mcp.tool()
def list_global_intray() -> list[dict]:
    """
    List all documents in the global intray that are accessible to the current user.

    Returns:
        A list of documents in the global intray

    Raises:
        Exception: If the intray cannot be accessed
    """
    url = f"{BASE_URL}/in-tray/global.html"

    try:
        response = requests.get(url, cookies=cookies)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        documents_table = soup.find('table', id='documents')

        if not documents_table:
            return []

        documents = []
        for row in documents_table.find_all('tr')[1:]:  # Skip header row
            cols = row.find_all('td')
            if cols:
                doc = {
                    'id': cols[0].get_text(strip=True),
                    'title': cols[1].get_text(strip=True) if len(cols) > 1 else None,
                    'date': cols[2].get_text(strip=True) if len(cols) > 2 else None
                }
                documents.append(doc)

        return documents

    except requests.RequestException as e:
        raise Exception(f"Failed to fetch global intray: {str(e)}")


@mcp.tool()
def list_my_intray() -> list[dict]:
    """
    List all documents in the current user's personal intray.

    Returns:
        A list of documents in the user's intray

    Raises:
        Exception: If the intray cannot be accessed
    """
    url = f"{BASE_URL}/create/overview.html"

    try:
        response = requests.get(url, cookies=cookies)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        documents_table = soup.find('table', id='bits')

        if not documents_table:
            return []

        documents = []
        for row in documents_table.find_all('tr')[1:]:  # Skip header row
            cols = row.find_all('td')
            if cols:
                doc = {
                    'id': cols[0].get_text(strip=True),
                    'title': cols[1].get_text(strip=True) if len(cols) > 1 else None,
                    'date': cols[2].get_text(strip=True) if len(cols) > 2 else None
                }
                documents.append(doc)

        return documents

    except requests.RequestException as e:
        raise Exception(f"Failed to fetch personal intray: {str(e)}")


@mcp.tool()
def list_all_intrays() -> dict[str, list[dict]]:
    """
    List all documents in all users' intrays (admin only).

    Returns:
        A dictionary mapping usernames to their intray documents

    Raises:
        Exception: If the user doesn't have admin access or if the intrays cannot be accessed
    """
    url = f"{BASE_URL}/create/overview.html"

    try:
        response = requests.get(url, cookies=cookies)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        users_table = soup.find('table', id='users-overview')

        if not users_table:
            raise Exception("Could not find users overview table - you may not have admin access")

        user_documents = {}
        for row in users_table.find_all('tr')[1:]:  # Skip header row
            cols = row.find_all('td')
            if cols:
                username = cols[0].get_text(strip=True)
                documents = []
                docs_table = row.find('table', class_='user-documents')
                if docs_table:
                    for doc_row in docs_table.find_all('tr')[1:]:
                        doc_cols = doc_row.find_all('td')
                        if doc_cols:
                            doc = {
                                'id': doc_cols[0].get_text(strip=True),
                                'title': doc_cols[1].get_text(strip=True) if len(doc_cols) > 1 else None,
                                'date': doc_cols[2].get_text(strip=True) if len(doc_cols) > 2 else None
                            }
                            documents.append(doc)
                user_documents[username] = documents

        return user_documents

    except requests.RequestException as e:
        raise Exception(f"Failed to fetch all intrays: {str(e)}")


# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"
