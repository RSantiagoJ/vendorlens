import sys
import os
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(__file__))


@pytest.fixture(autouse=True)
def _mock_llm_construction():
    """Mock LLM factory calls so agents can be constructed without an API key.

    All four agents call make_claude_llm / make_haiku_llm in __init__, which
    requires ANTHROPIC_API_KEY. Since invoke_llm_cached is always mocked in
    individual tests, the returned LLM object itself is never used for real calls.
    """
    mock_llm = MagicMock()
    with (
        patch("agents.extraction_agent.make_claude_llm", return_value=mock_llm),
        patch("agents.risk_agent.make_claude_llm", return_value=mock_llm),
        patch("agents.memo_agent.make_claude_llm", return_value=mock_llm),
        patch("agents.scoring_agent.make_haiku_llm", return_value=mock_llm),
    ):
        yield
