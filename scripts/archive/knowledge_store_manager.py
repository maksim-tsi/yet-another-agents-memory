# file: knowledge_store_manager.py

from typing import Any, Literal

from graph_store_client import Neo4jGraphStore
from qdrant_client import models as qdrant_models
from search_store_client import MeilisearchStore
from vector_store_client import QdrantVectorStore


class KnowledgeStoreManager:
    def __init__(
        self,
        vector_store: QdrantVectorStore,
        graph_store: Neo4jGraphStore,
        search_store: MeilisearchStore,
    ):
        """Initializes with instances of all specialized store clients."""
        self.vector_store = vector_store
        self.graph_store = graph_store
        self.search_store = search_store

    def add(self, store_type: Literal["vector", "search"], documents: list[dict[str, Any]]) -> Any:
        """
        Adds documents to the specified store.
        Note: Graph store additions are typically done via query.
        """
        if store_type == "vector":
            return self.vector_store.add_documents(documents)
        elif store_type == "search":
            return self.search_store.add_documents(documents)
        else:
            raise ValueError(
                f"Adding documents to '{store_type}' is not supported via this method."
            )

    def query(
        self,
        store_type: Literal["vector", "graph", "search"],
        query_text: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Routes a query to the appropriate knowledge store with a unified interface.

        Args:
            store_type: The type of store to query ('vector', 'graph', or 'search').
            query_text: The primary query content (e.g., text for semantic/full-text search, or a Cypher query for graph).
            top_k: The number of results to return.
            filters: A structured dictionary for filtering results, which will be translated.

        Returns:
            A list of result dictionaries.
        """
        if store_type == "vector":
            qdrant_filter = self._build_qdrant_filter(filters) if filters else None
            return self.vector_store.query_similar(
                query_text=query_text, top_k=top_k, filters=qdrant_filter
            )

        elif store_type == "graph":
            return self.graph_store.query(cypher_query=query_text, params=filters)

        elif store_type == "search":
            meili_filter_string = self._build_meili_filter(filters) if filters else None
            return self.search_store.search(
                query=query_text, top_k=top_k, filters=meili_filter_string
            )

        else:
            raise ValueError(f"Unknown store_type: {store_type}")

    def _build_qdrant_filter(self, filters: dict[str, Any]) -> qdrant_models.Filter:
        """Helper to convert a simple dict to a Qdrant filter."""
        return qdrant_models.Filter(
            must=[
                qdrant_models.FieldCondition(key=key, match=qdrant_models.MatchValue(value=value))
                for key, value in filters.items()
            ]
        )

    def _build_meili_filter(self, filters: dict[str, Any]) -> str:
        """Helper to convert a simple dict to a Meilisearch filter string."""
        return " AND ".join([f"{key} = '{value}'" for key, value in filters.items()])
