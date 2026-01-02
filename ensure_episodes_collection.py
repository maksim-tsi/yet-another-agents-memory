import asyncio
from src.storage.qdrant_adapter import QdrantAdapter


async def main() -> None:
    adapter = QdrantAdapter({
        "url": "http://192.168.107.187:6333",
        "collection_name": "episodes",
        "vector_size": 768,
    })
    await adapter.connect()
    created = await adapter.create_collection("episodes")
    print("Episodes collection created or refreshed:", created)
    info = await adapter.client.get_collection(collection_name="episodes")
    size = getattr(info.config.params.vectors, "size", None)
    print("Current vector size:", size)
    await adapter.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
