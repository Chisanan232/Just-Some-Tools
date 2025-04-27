import os
import pathlib
import pytest
from unittest import mock
from typing import List, Dict, Tuple

import yaml

from github_label_bot.runner import GitHubOperationRunner
from github_label_bot.github_action import GitHubAction
from github_label_bot.model import GitHubLabelManagementConfig, Label


class TestGitHubOperationRunner:
    
    @pytest.mark.parametrize(
        "config_exists, config_content, expected_repositories, env_repository",
        [
            # Case 1: Config file exists with repositories
            (
                True, 
                {"repositories": ["owner/repo1", "owner/repo2"], "delete_unused": False, "labels": {}}, 
                ["owner/repo1", "owner/repo2"],
                "owner/default-repo",
            ),
            # Case 2: Config file exists with empty repositories
            (
                True, 
                {"repositories": [], "delete_unused": True, "labels": {"label1": {"color": "ff0000", "description": "desc"}}}, 
                [],
                "owner/default-repo",
            ),
            # Case 3: Config file exists without repositories key
            (
                True, 
                {"delete_unused": False, "labels": {"label1": {"color": "ff0000", "description": "desc"}}}, 
                ["owner/default-repo"],
                "owner/default-repo",
            ),
            # Case 4: Config file doesn't exist
            (
                False, 
                None, 
                ["owner/default-repo"],
                "owner/default-repo",
            ),
        ]
    )
    def test_force_load_config(
        self, 
        config_exists: bool, 
        config_content: Dict, 
        expected_repositories: List[str],
        env_repository: str,
        tmp_path,
    ):
        # Setup
        runner = GitHubOperationRunner()
        config_path = tmp_path / "test_config.yaml"

        # Create mock action input
        action_inputs = GitHubAction(config_path=str(config_path), operation=[])

        # Setup environment and file system based on test parameters
        with mock.patch.dict(os.environ, {"GITHUB_REPOSITORY": env_repository}):
            if config_exists:
                # Create and write to config file
                with open(config_path, 'w') as f:
                    yaml.dump(config_content, f)

            # Call the method under test
            config, repositories = runner._force_load_config(action_inputs)

            # Assertions
            assert isinstance(config, GitHubLabelManagementConfig)
            assert repositories == expected_repositories

            # Additional assertions based on the scenario
            if config_exists:
                # Verify config was loaded correctly
                if "repositories" in config_content:
                    assert config.repositories == config_content["repositories"]
                if "delete_unused" in config_content:
                    assert config.delete_unused == config_content["delete_unused"]
                if "labels" in config_content and config_content["labels"]:
                    # Check that labels were properly loaded
                    for label_name in config_content["labels"]:
                        assert label_name in config.labels
            else:
                # Verify default config was created
                assert config.repositories == []
                assert config.delete_unused is False
                assert config.labels == {}
