import json
from typing import Any


class MetadataSanitizer:
    MAX_BYTES = 50 * 1024  # 50KB

    @staticmethod
    def sanitize(metadata: dict[str, Any]) -> dict[str, Any]:
        if not metadata:
            return {}

        try:
            # Check size by serializing
            payload = json.dumps(metadata)
            if len(payload) <= MetadataSanitizer.MAX_BYTES:
                return metadata

            return {
                "error": "Metadata exceeded 50KB limit",
                "truncated_keys": list(metadata.keys()),
                "info": f"Original size: {len(payload)} bytes",
            }
        except (TypeError, ValueError):
            return {"error": "Metadata serialization failed", "keys": list(metadata.keys())}
