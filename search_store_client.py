# file: search_store_client.py

import meilisearch
from typing import List, Dict, Any, Optional


class MeilisearchStore:
    def __init__(self, host_url: str, api_key: str, index_name: str):
        """
        Initializes the connection to Meilisearch.

        Args:
            host_url: The URL where Meilisearch server is running.
            api_key: The API key for authentication.
            index_name: The name of the index to use.
        """
        self.client = meilisearch.Client(host_url, api_key)
        self.index_name = index_name

        try:
            self.index = self.client.get_index(index_name)
        except meilisearch.errors.MeiliSearchApiError:
            task = self.client.create_index(index_name)
            self.client.wait_for_task(task.task_uid)
            self.index = self.client.get_index(index_name)

    def configure_index(self, settings: Dict[str, Any]):
        """
        Configure index settings for better search experience.

        Args:
            settings: A dictionary of Meilisearch settings.
                      e.g., {'filterableAttributes': ['category']}
        """
        task = self.index.update_settings(settings)
        self.client.wait_for_task(task.task_uid)

    def add_documents(self, documents: List[Dict[str, Any]], primary_key: str = "id"):
        """
        Adds or updates documents in the Meilisearch index.

        Args:
            documents: List of document dictionaries to add.
            primary_key: The field to use as the primary key.
        """
        task = self.index.add_documents(documents, primary_key=primary_key)
        self.client.wait_for_task(task.task_uid)

    def search(
        self, query: str, top_k: int = 5, filters: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Performs a full-text search.

        Args:
            query: The search query string.
            top_k: Maximum number of results to return.
            filters: Optional filter expression (e.g., "category = 'supply'").

        Returns:
            A list of matching documents.
        """
        search_params = {"limit": top_k}
        if filters:
            search_params["filter"] = filters

        search_results = self.index.search(query, search_params)
        return search_results["hits"]

    def delete_documents(self, document_ids: List[str]):
        """Delete documents from the index by their IDs."""
        task = self.index.delete_documents(document_ids)
        self.client.wait_for_task(task.task_uid)

    def get_document(self, document_id: str) -> Dict[str, Any]:
        """Retrieve a single document by its ID."""
        return self.index.get_document(document_id)
