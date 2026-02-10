import json
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
from dataset_interfaces.factory import DatasetFactory
from model_interfaces.interface import ChatSession
from runner.master_log import MasterLog
from runner.run_benchmark import load_examples_from_dir
from runner.sanitizer import MetadataSanitizer

# --- Mock Classes ---


class MockChatSession(ChatSession):
    def __init__(self) -> None:
        self.run_name = "test_run"
        self.costs_usd = 0.0
        self.last_metadata: dict[str, Any] = {}
        self.history: list[tuple[str, str]] = []

    def reply(
        self, user_message: str, agent_response: str | None = None
    ) -> tuple[str, dict[str, Any]]:
        self.history.append((user_message, "response"))
        return "response", {"metadata_key": "metadata_value"}

    def reset(self) -> None:
        pass

    def save(self) -> None:
        pass

    def load(self) -> None:
        pass


@pytest.fixture
def mock_chat_session() -> MockChatSession:
    return MockChatSession()


# --- Tests ---


def test_metadata_sanitizer():
    # Test valid metadata
    valid = {"key": "value", "num": 123}
    assert MetadataSanitizer.sanitize(valid) == valid

    # Test empty
    assert MetadataSanitizer.sanitize({}) == {}

    # Test too large
    large_str = "a" * (50 * 1024 + 1)
    too_large = {"data": large_str}
    sanitized = MetadataSanitizer.sanitize(too_large)
    assert "error" in sanitized
    assert sanitized["error"] == "Metadata exceeded 50KB limit"

    # Test unserializable
    class Unserializable:
        pass

    bad_data = {"obj": Unserializable()}
    sanitized_bad = MetadataSanitizer.sanitize(bad_data)
    assert "error" in sanitized_bad
    assert sanitized_bad["error"] == "Metadata serialization failed"


def test_chat_session_metadata() -> None:
    # 1. Mock session
    class MockSession(ChatSession):
        def reply(self, user_message, agent_response=None):
            return "response", {"usage": {"total_tokens": 10}}

        def reset(self):
            pass

        def save(self):
            pass

        def load(self):
            pass

    session = MockSession(run_name="test", is_local=True)

    # 2. Send message
    _resp, _sent, _reply_ts, meta = session.message_to_agent("Hello")
    assert meta["usage"]["total_tokens"] == 10

    # Check if last_metadata is set
    assert session.last_metadata == meta


def test_master_log_metadata() -> None:
    with tempfile.NamedTemporaryFile() as tmp:
        log_path = Path(tmp.name)
        log = MasterLog(log_path)

        # Test add_response_message with metadata
        ts = datetime.now()
        meta = {"info": "test"}
        log.add_response_message("response", ts, "test_id", False, metadata=meta)

        # Verify in memory
        assert len(log.log) == 1
        event = log.log[0]
        assert event.data["metadata"] == meta

        # Verify on disk
        with open(log_path) as f:
            line = f.readline()
            saved_event = json.loads(line)
            assert saved_event["data"]["metadata"] == meta


def test_dataset_generation_and_loading() -> None:
    # 1. Create a dummy dataset config
    config: dict[str, Any] = {
        "datasets": [{"name": "name_list", "args": {"dataset_examples": 2}}],
        "args": {"memory_span": 1024},  # Universal args
    }

    # 2. Generate examples using Factory
    # We need to make sure we can instantiate NameListDataset or similar
    # This integration test depends on actual dataset classes functioning

    try:
        examples = DatasetFactory.create_examples(config["datasets"][0], config["args"], 1024)
        assert len(examples) == 2
        assert examples[0].dataset_name == "NameList"

        # 3. Save to temp dir
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            ds_dir = tmp_path / "NameList"
            ds_dir.mkdir()

            for i, ex in enumerate(examples):
                ex.example_id = str(i)
                file_path = ds_dir / f"{i}.def.json"
                with open(file_path, "w") as f:
                    json.dump(ex.to_dict(), f)

            # 4. Load back using run_benchmark loader
            loaded = load_examples_from_dir(str(tmp_path), {"datasets": config})
            assert len(loaded) == 2
            assert loaded[0].dataset_name == "NameList"

    except Exception as e:
        pytest.fail(f"Dataset generation/loading failed: {e}")
