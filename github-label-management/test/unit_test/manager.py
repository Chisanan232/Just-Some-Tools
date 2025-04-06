import os
import pathlib
from collections import namedtuple
from unittest.mock import patch, Mock, MagicMock

from pytest_mock import MockFixture
import pytest

from github_label_bot.enums import Operation
from github_label_bot.github_action import GitHubAction
from github_label_bot.manager import GitHubLabelBot, run_bot
from github_label_bot.model import GitHubLabelManagementConfig
from github.Repository import Repository

from github_label_bot.runner import GitHubOperationRunner

# A sample YAML configuration
SAMPLE_YAML = """
repositories:
  - my-org/my-repository
labels:
  Bug:
    color: d73a4a
    description: Something went wrong.
  Enhancement:
    color: 005cc5
    description: New feature or improvement.
delete_unused: true
"""


@pytest.fixture(scope="module")
def github_action_inputs() -> GitHubAction:
    return GitHubAction(
        config_path="test-github-label-bot-config.yml",
        operation=[Operation.Sync_UpStream],
    )


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
        return str(file_path)

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
    def test_download_from_remote_repo(self, bot: GitHubLabelBot, mocker: MockFixture, monkeypatch, mock_yaml_file, github_action_inputs: GitHubAction):
        # Mock the token retrieval
        monkeypatch.setenv("GITHUB_TOKEN", "mock_token")

        # Mock the GitHub client and repository
        mock_github = mocker.patch("github_label_bot.runner.Github")
        mock_repo = mock_github().get_repo.return_value
        mock_download_labels = mocker.patch("github_label_bot.manager.DownloadFromRemote.process")

        # Mock configuration loading
        config_model = GitHubOperationRunner()._load_label_config(mock_yaml_file)
        mocker.patch("github_label_bot.manager.GitHubOperationRunner._load_label_config", return_value=config_model)

        # Call the function
        bot.download_from_remote_repo(github_action_inputs)

        # Assert that download_labels was called with the correct repository
        mock_github().get_repo.assert_called()
        mock_download_labels.assert_called_once_with(mock_repo, config_model)


    # Test syncup_as_config
    def test_sync_from_remote_repo(self, bot: GitHubLabelBot, mocker: MockFixture, monkeypatch, mock_github_repo, mock_yaml_file, github_action_inputs: GitHubAction):
        # Mock the token retrieval
        monkeypatch.setenv("GITHUB_TOKEN", "mock_token")

        # Mock the GitHub client
        mock_github = mocker.patch("github_label_bot.runner.Github")
        mock_repo = mock_github().get_repo.return_value
        mock_repo.get_labels.return_value = []

        # Mock configuration loading
        config_model = GitHubOperationRunner()._load_label_config(mock_yaml_file)
        mocker.patch("github_label_bot.manager.GitHubOperationRunner._load_label_config", return_value=config_model)

        # Call the function
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
