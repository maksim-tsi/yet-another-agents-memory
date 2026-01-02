import asyncio
from datetime import datetime, timezone, timedelta

from src.storage.qdrant_adapter import QdrantAdapter
from src.storage.neo4j_adapter import Neo4jAdapter
from src.memory.tiers.episodic_memory_tier import EpisodicMemoryTier
from src.memory.models import Episode


async def main() -> None:
    session_id = "manual-session"
    q = QdrantAdapter({
        "url": "http://192.168.107.187:6333",
        "collection_name": "episodes",
        "vector_size": EpisodicMemoryTier.VECTOR_SIZE,
    })
    await q.connect()

    n = Neo4jAdapter({
        "uri": "bolt://192.168.107.187:7687",
        "user": "neo4j",
        "password": "password",
    })
    await n.connect()
    tier = EpisodicMemoryTier(q, n)

    now = datetime.now(timezone.utc)
    episode = Episode(
        episode_id="manual-episode",
        session_id=session_id,
        summary="Manual test episode",
        narrative="Manual narrative",
        source_fact_ids=["f1", "f2"],
        fact_count=2,
        time_window_start=now - timedelta(hours=1),
        time_window_end=now,
        duration_seconds=3600,
        fact_valid_from=now - timedelta(hours=1),
        fact_valid_to=None,
        source_observation_timestamp=now,
        embedding_model="test",
        topics=[],
        importance_score=0.5,
    )

    # simple deterministic embedding of correct size
    embedding = [0.01] * tier.vector_size

    await tier.store({
        "episode": episode,
        "embedding": embedding,
        "entities": [],
        "relationships": [],
    })

    results = await q.search({
        "vector": embedding,
        "filter": {"session_id": session_id},
        "limit": 5,
        "collection_name": "episodes",
    })
    print("Stored and queried results count:", len(results))
    if results:
        print("First payload keys:", list(results[0].keys()))

    await q.disconnect()
    await n.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
