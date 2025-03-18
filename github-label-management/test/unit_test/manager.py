from pytest_mock import MockFixture
import pytest
from github_label_bot.manager import GitHubLabelBot
from github_label_bot.model import GitHubLabelManagementConfig
from github.Repository import Repository

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


    # Test load_label_config
    def test__load_label_config(self, bot: GitHubLabelBot, mock_yaml_file):
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
    def test__get_github_token(self, bot: GitHubLabelBot, monkeypatch):
        monkeypatch.setenv("GITHUB_TOKEN", "mock_token")
        token = bot._get_github_token()
        assert token == "mock_token"


    # Test _get_github_token when no token is set
    def test__get_github_token_no_env_var(self, bot: GitHubLabelBot, monkeypatch):
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        with pytest.raises(ValueError, match="GITHUB_TOKEN environment variable not set"):
            bot._get_github_token()


    # Test download_as_config
    def test_download_as_config(self, bot: GitHubLabelBot, mocker: MockFixture, monkeypatch, mock_yaml_file):
        # Mock the token retrieval
        monkeypatch.setenv("GITHUB_TOKEN", "mock_token")

        # Mock the GitHub client and repository
        mock_github = mocker.patch("github_label_bot.manager.Github")
        mock_repo = mock_github().get_repo.return_value
        mock_download_labels = mocker.patch("github_label_bot.manager.DownloadFromRemote.process")

        # Mock configuration loading
        mocker.patch("github_label_bot.manager.GitHubLabelBot._load_label_config", return_value=bot._load_label_config(mock_yaml_file))

        # Call the function
        bot.download_as_config()

        # Assert that download_labels was called with the correct repository
        mock_github().get_repo.assert_called()
        mock_download_labels.assert_called_once_with(mock_repo)


    # Test syncup_as_config
    def test_syncup_as_config(self, bot: GitHubLabelBot, mocker: MockFixture, monkeypatch, mock_github_repo, mock_yaml_file):
        # Mock the token retrieval
        monkeypatch.setenv("GITHUB_TOKEN", "mock_token")

        # Mock the GitHub client
        mock_github = mocker.patch("github_label_bot.manager.Github")
        mock_repo = mock_github().get_repo.return_value
        mock_repo.get_labels.return_value = []

        # Mock configuration loading
        mocker.patch("github_label_bot.manager.GitHubLabelBot._load_label_config", return_value=bot._load_label_config(mock_yaml_file))

        # Call the function
        bot.syncup_as_config()

        # Assert that repository was fetched and labels were synced
        mock_github().get_repo.assert_called()
        mock_repo.create_label.assert_called()
