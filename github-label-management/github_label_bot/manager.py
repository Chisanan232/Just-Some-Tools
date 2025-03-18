import os
from collections.abc import Callable

import yaml
from github import Github
from github.Repository import Repository

from .model import GitHubLabelManagementConfig
from .process import SyncUpAsRemote, DownloadFromRemote
from .runner import GitHubOperationRunner


class GitHubLabelBot:

    def __init__(self):
        self._github_runner = GitHubOperationRunner()

    def syncup_as_config(self) -> None:

        def _sync_process(_repo, _config) -> None:
            SyncUpAsRemote().process(_repo, _config)

        self._github_runner.operate_with_github(_sync_process)

    def download_as_config(self) -> None:

        def _download_process(_repo, _config) -> None:
            DownloadFromRemote().process(_repo)

        self._github_runner.operate_with_github(_download_process)
