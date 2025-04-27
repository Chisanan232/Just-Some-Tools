import os
import pathlib
from collections import namedtuple
from unittest.mock import MagicMock, Mock, patch

import pytest
from github.Repository import Repository
from github_label_bot.enums import Operation
from github_label_bot.github_action import GitHubAction
from github_label_bot.manager import GitHubLabelBot, run_bot
from github_label_bot.runner import GitHubOperationRunner
from pytest_mock import MockFixture

from ._values import SAMPLE_YAML


@pytest.fixture(scope="module")
def github_action_inputs() -> GitHubAction:
    return GitHubAction(
        config_path="test-github-label-bot-config.yml",
        operation=[Operation.Sync_UpStream],
    )


class TestGitHubLabelBot:
    # Mock the config file for testing `load_label_config`
    @pytest.fixture(scope="function")
    def bot(self) -> GitHubLabelBot:
        return GitHubLabelBot()

    @pytest.fixture()
    def mock_yaml_file(self, tmp_path):
        file_path = tmp_path / "config.yaml"
        with open(file_path, "w") as file:
            file.write(SAMPLE_YAML)
        yield str(file_path)
        os.remove(str(file_path))

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

    # Test download_as_config
    @patch.dict(os.environ, {"GITHUB_REPOSITORY": "Chisanan232/Just-Some-Tools"}, clear=True)
    def test_download_from_remote_repo(
        self, bot: GitHubLabelBot, mocker: MockFixture, monkeypatch, mock_yaml_file, github_action_inputs: GitHubAction
    ):
        # Mock the token retrieval
        monkeypatch.setenv("GITHUB_TOKEN", "mock_token")

        # Mock the GitHub client and repository
        mock_github = mocker.patch("github_label_bot.runner.Github")
        mock_repo = mock_github().get_repo.return_value
        mock_download_labels = mocker.patch("github_label_bot.manager.DownloadFromRemote.process")

        # Call the function
        github_action_inputs.config_path = mock_yaml_file
        bot.download_from_remote_repo(github_action_inputs)

        # Assert that download_labels was called with the correct repository
        mock_github().get_repo.assert_called()
        config_model = GitHubOperationRunner()._load_label_config(mock_yaml_file)
        mock_download_labels.assert_called_once_with(mock_repo, config_model)

    # Test syncup_as_config
    @patch.dict(os.environ, {"GITHUB_REPOSITORY": "Chisanan232/Just-Some-Tools"}, clear=True)
    def test_sync_from_remote_repo(
        self,
        bot: GitHubLabelBot,
        mocker: MockFixture,
        monkeypatch,
        mock_github_repo,
        mock_yaml_file,
        github_action_inputs: GitHubAction,
    ):
        # Mock the token retrieval
        monkeypatch.setenv("GITHUB_TOKEN", "mock_token")

        # Mock the GitHub client
        mock_github = mocker.patch("github_label_bot.runner.Github")
        mock_repo = mock_github().get_repo.return_value
        mock_repo.get_labels.return_value = []

        # Call the function
        github_action_inputs.config_path = mock_yaml_file
        bot.sync_from_remote_repo(github_action_inputs)

        # Assert that repository was fetched and labels were synced
        mock_github().get_repo.assert_called()
        mock_repo.create_label.assert_called()


ExpectBotCalls = namedtuple("ExpectBotCalls", ("syncup", "download"))


@pytest.mark.parametrize(
    ("operations", "expect_calls"),
    [
        ("sync_upstream", ExpectBotCalls(syncup=True, download=False)),
        ("sync_download", ExpectBotCalls(syncup=False, download=True)),
        ("sync_download,sync_upstream", ExpectBotCalls(syncup=True, download=True)),
    ],
)
def test_run_bot(operations: str, expect_calls: ExpectBotCalls):
    config = pathlib.Path("./test-github-labels.yaml")
    config.touch()
    try:
        # Mock the under test functions
        github_label_bot = MagicMock()
        github_label_bot.sync_from_remote_repo = Mock()
        github_label_bot.download_from_remote_repo = Mock()
        with patch("github_label_bot.manager.GitHubLabelBot", return_value=github_label_bot) as mock_bot_instance:
            with patch.dict(os.environ, {"CONFIG_PATH": str(config), "OPERATIONS": operations}, clear=True):
                run_bot()

                mock_bot_instance.assert_called_once()

                # Check sync_from_remote_repo calls
                if expect_calls.syncup:
                    github_label_bot.sync_from_remote_repo.assert_called_once()
                else:
                    github_label_bot.sync_from_remote_repo.assert_not_called()

                # Check download_from_remote_repo calls
                if expect_calls.download:
                    github_label_bot.download_from_remote_repo.assert_called_once()
                else:
                    github_label_bot.download_from_remote_repo.assert_not_called()
    finally:
        os.remove(config)
