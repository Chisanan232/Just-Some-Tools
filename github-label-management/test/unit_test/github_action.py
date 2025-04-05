import os
from typing import List, Dict
from unittest.mock import patch

import pytest

from github_label_bot.enums import Operation
from github_label_bot.github_action import GitHubAction


class TestGitHubAction:

    @pytest.mark.parametrize(
        ("mock_env", "expect"),
        [
            ({"OPERATIONS": "sync_download"}, [Operation.Sync_Download]),
            ({"OPERATIONS": "sync_download,sync_upstream"}, [Operation.Sync_Download, Operation.Sync_UpStream]),
            ({"OPERATIONS": "sync_upstream"}, [Operation.Sync_UpStream]),
        ],
    )
    def test_from_env_valid_env_vars(self, mock_env: Dict[str, str], expect: List[Operation]):
        with patch.dict(os.environ, mock_env, clear=True):
            action = GitHubAction.from_env()
            assert action.operation == expect

    def test_from_env_missing_env_vars(self):
        with pytest.raises(ValueError, match=r"OPERATIONS.{0,64}not set.{0,64}empty."):
            GitHubAction.from_env()
