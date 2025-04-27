from unittest.mock import Mock

import pytest
from github.Repository import Repository
from github_label_bot.model import GitHubLabelManagementConfig
from github_label_bot.model import Label as GitHubLabelBotLabel
from github_label_bot.process import DownloadFromRemote, SyncUpAsRemote
from pytest_mock import MockFixture


class TestSyncUpAsRemote:
    @pytest.fixture(scope="function")
    def process(self) -> SyncUpAsRemote:
        return SyncUpAsRemote()

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

    # Test sync_labels
    def test_sync_labels_update(self, process: SyncUpAsRemote, mocker: MockFixture, mock_github_repo):
        mock_repo = mock_github_repo

        # Mock configuration for testing
        label_config = GitHubLabelManagementConfig(
            repositories=["mock/repository"],
            labels={
                "Bug": GitHubLabelBotLabel(color="ffffff", description="New description"),
            },
            delete_unused=False,
        )

        # Call the function
        process.process(mock_repo, label_config)

        # Assert that label.edit was called with the updated properties
        mock_repo.get_labels.assert_called_once()
        mock_repo.get_labels.return_value[0].edit.assert_called_with(
            name="Bug", color="ffffff", description="New description"
        )

    # Test sync_labels with creating new labels
    def test_sync_labels_create(self, process: SyncUpAsRemote, mocker: MockFixture, mock_github_repo):
        mock_repo = mock_github_repo

        # Empty existing labels
        mock_repo.get_labels.return_value = []

        # Mock configuration for testing
        label_config = GitHubLabelManagementConfig(
            repositories=["mock/repository"],
            labels={
                "NewLabel": GitHubLabelBotLabel(color="000000", description="A new label"),
            },
            delete_unused=False,
        )

        # Call the function
        process.process(mock_repo, label_config)

        # Assert that create_label was called for the new label
        mock_repo.create_label.assert_called_once_with(name="NewLabel", color="000000", description="A new label")


class TestDownloadFromRemote:
    @pytest.fixture(scope="function")
    def bot(self) -> DownloadFromRemote:
        return DownloadFromRemote()

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

    # Test download_labels
    def test_download_labels(self, bot: DownloadFromRemote, mocker: MockFixture, mock_github_repo):
        mock_repo = mock_github_repo
        mock_yaml = mocker.patch("github_label_bot.process.YAML")

        # Call the function
        bot.process(mock_repo, Mock())

        # Assert that YAML().write() was called with appropriate arguments
        mock_yaml().write.assert_called_once()
        written_config = mock_yaml().write.call_args[1]["config"]
        print(f"[DEBUG] written_config: {written_config}")
        assert "Bug" in written_config["labels"].keys()
        assert written_config["labels"]["Bug"]["color"] == "d73a4a"
