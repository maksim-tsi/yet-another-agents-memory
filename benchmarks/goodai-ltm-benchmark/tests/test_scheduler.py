from dataclasses import dataclass
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from dataset_interfaces.interface import DatasetInterface, TestExample
from model_interfaces.interface import ChatSession
from runner.config import RunConfig
from runner.master_log import MasterLog
from runner.scheduler import SendMessageAction, TestRunner, WaitAction

# Mock Classes


@dataclass
class MockDataset(DatasetInterface):
    name: str = "MockDataset"
    description: str = "Mock Desc"
    memory_span: int = 100

    def generate_examples(self, num):
        return []

    def evaluate_correct(self, q, r, e):
        return 1.0, 1.0, []


class MockSession(ChatSession):
    @property
    def name(self):
        return "MockAgent"

    @property
    def save_name(self):
        return "mock_agent"

    @property
    def save_path(self):
        return self._save_path_mock

    def __init__(self):
        self.costs_usd = 0.0
        self.history = []
        self.token_len_val = 10
        self.last_metadata = {}
        self._save_path_mock = MagicMock()
        self._save_path_mock.mkdir = MagicMock()

    def message_to_agent(self, message: str, filler_response=None):
        return "response", datetime.now(), datetime.now(), {}

    def token_len(self, text):
        return self.token_len_val

    def reply(self, user_message, agent_response=None):
        return "response"

    def reset(self):
        pass

    def load(self):
        pass

    def save(self):
        pass


@pytest.fixture
def mock_runner():
    config = RunConfig(run_name="test_run", debug=True)
    agent = MockSession()
    dataset = MockDataset(name="MockDS", description="Desc")
    example = TestExample(
        dataset_generator=dataset,
        example_id="ex1",
        script=["Hello", "Question?"],
        is_question=[False, True],
    )

    # Mock master log
    master_log = MagicMock(spec=MasterLog)
    master_log.log = []

    with patch("runner.scheduler.make_runstats_path") as mock_make_path:
        mock_path = MagicMock()
        mock_make_path.return_value = mock_path

        runner = TestRunner(config=config, agent=agent, tests=[example], master_log=master_log)
        yield runner


def test_runner_initialization(mock_runner) -> None:
    assert mock_runner.config.run_name == "test_run"
    assert mock_runner.agent.name == "MockAgent"


def test_send_message(mock_runner) -> None:
    mock_runner._require_master_log = MagicMock(return_value=mock_runner.master_log)
    mock_runner._require_progress_dialog = MagicMock()
    mock_runner.progress_dialog = MagicMock()

    action = SendMessageAction(message="hello")
    tokens = mock_runner.send_message("ex1", action)

    assert tokens > 0
    mock_runner.master_log.add_send_message.assert_called()


def test_set_to_wait(mock_runner) -> None:
    mock_runner._require_master_log = MagicMock(return_value=mock_runner.master_log)
    dataset = MockDataset(name="MockDS", description="Desc")
    example = TestExample(
        dataset_generator=dataset,
        example_id="ex1",
        script=["Hello", "Question?"],
        is_question=[False, True],
    )
    example.start_token = 0
    dataset.memory_span = 1000

    # Mock past events for token calculation
    mock_event = MagicMock()
    mock_event.data = {"message": "response"}
    mock_runner.master_log.test_events.return_value = [mock_event]

    # Wait for 50% of memory span (500 tokens)
    # Current tokens elapsed = 500
    # Wait tokens = 500 - 500 = 0?

    action = WaitAction(percentage_finished=60.0, time=timedelta(seconds=1))
    # 60% of 1000 = 600 tokens.
    # elapsed = 500.
    # expect wait 100 tokens.

    mock_runner.set_to_wait(example, action)

    # Check wait list
    assert example.unique_id in mock_runner.wait_list
    wait_entry = mock_runner.wait_list[example.unique_id]
    # token target = current (500) + wait (100 - 10 (reply len)) = 590
    assert wait_entry["tokens"] == 590


def test_is_waiting(mock_runner) -> None:
    mock_runner.wait_list["ex1"] = {"tokens": 1000, "time": datetime.now() + timedelta(hours=1)}
    mock_runner.total_token_count = 500

    assert mock_runner.is_waiting("ex1")

    mock_runner.total_token_count = 1500
    # Still waiting on time?
    assert mock_runner.is_waiting("ex1")

    # Move time forward
    mock_runner.wait_list["ex1"]["time"] = datetime.now() - timedelta(hours=1)

    # Now both conditions met implies NOT waiting?
    # Logic in is_waiting: if tokens > current: return True. If time > now: return True.
    # So if both false, return False.
    assert not mock_runner.is_waiting("ex1")


def test_run_filler_task(mock_runner) -> None:
    mock_runner._require_master_log = MagicMock(return_value=mock_runner.master_log)
    mock_runner._require_progress_dialog = MagicMock()
    mock_runner.progress_dialog = MagicMock()

    mock_runner.send_message = MagicMock(return_value=10)

    mock_runner.run_filler_task(25)

    # Should call send_message 3 times (10, 10, 5 remaining -> 10 consumed?)
    # filler_no_response_tokens_trivia generates message.
    assert mock_runner.send_message.call_count >= 1
