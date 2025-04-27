import os
import pathlib
from unittest.mock import patch

import pytest
from unittest import mock
from typing import List, Dict, Tuple

import yaml
from github.Repository import Repository
from pytest_mock import MockFixture

from github_label_bot.runner import GitHubOperationRunner
from github_label_bot.github_action import GitHubAction
from github_label_bot.model import GitHubLabelManagementConfig, Label

from ._values import SAMPLE_YAML


class TestGitHubOperationRunner:
    # Mock the config file for testing `load_label_config`
    @pytest.fixture(scope="function")
    def bot(self) -> GitHubOperationRunner:
        return GitHubOperationRunner()

    @pytest.fixture()
    def mock_yaml_file(self, tmp_path):
        file_path = tmp_path / "config.yaml"
        with open(file_path, "w") as file:
            file.write(SAMPLE_YAML)
        return str(file_path)


    # Test load_label_config
    @patch.dict(os.environ, {"GITHUB_REPOSITORY": "Chisanan232/Just-Some-Tools"}, clear=True)
    def test__load_label_config(self, bot: GitHubOperationRunner, mock_yaml_file):
        config = bot._load_label_config(mock_yaml_file)
        assert isinstance(config, GitHubLabelManagementConfig)
        assert "my-org/my-repository" in config.repositories
        assert "Bug" in config.labels
        assert config.labels["Bug"].color == "d73a4a"


    # Mocked GitHub Repository
    @pytest.fixture
    def mock_github_repo(self, mocker: MockFixture):
        mock_repo = mocker.MagicMock(spec=Repository)
        mock_label = mocker.MagicMock()
        mock_label.name = "Bug"
        mock_label.color = "d73a4a"
        mock_label.description = "A bug label"
        mock_repo.get_labels.return_value = [mock_label]
        return mock_repo


    # Test _get_github_token with a valid token
    def test__get_github_token(self, bot: GitHubOperationRunner, monkeypatch):
        monkeypatch.setenv("GITHUB_TOKEN", "mock_token")
        token = bot._get_github_token()
        assert token == "mock_token"


    # Test _get_github_token when no token is set
    def test__get_github_token_no_env_var(self, bot: GitHubOperationRunner, monkeypatch):
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        with pytest.raises(ValueError, match="GITHUB_TOKEN environment variable not set"):
            bot._get_github_token()

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
