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
        self._github_runner.operate_with_github(SyncUpAsRemote())

    def download_as_config(self) -> None:
        self._github_runner.operate_with_github(DownloadFromRemote())
