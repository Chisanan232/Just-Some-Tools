import os
from collections.abc import Callable

import yaml
from github import Github
from github.Repository import Repository

from github_label_bot.enums import Operation
from github_label_bot.github_action import GitHubAction
from .model import GitHubLabelManagementConfig
from .process import SyncUpAsRemote, DownloadFromRemote
from .runner import GitHubOperationRunner


class GitHubLabelBot:

    def __init__(self):
        self._github_runner = GitHubOperationRunner()

    def sync_from_remote_repo(self) -> None:
        self._github_runner.operate_with_github(SyncUpAsRemote())

    def download_from_remote_repo(self) -> None:
        self._github_runner.operate_with_github(DownloadFromRemote())


def run_bot() -> None:
    github_action_inputs = GitHubAction.from_env()
    bot = GitHubLabelBot()
    print(f"[DEBUG] github_action_inputs.operation: {github_action_inputs.operation}")
    for opt in github_action_inputs.operation:
        if opt is Operation.Sync_UpStream:
            print(f"[DEBUG] run syncup ...")
            bot.sync_from_remote_repo()
        elif opt is Operation.Sync_Download:
            print(f"[DEBUG] run download ...")
            bot.download_from_remote_repo()
        else:
            raise ValueError(f"Unsupported operation: {opt}")


if __name__ == '__main__':
    run_bot()
