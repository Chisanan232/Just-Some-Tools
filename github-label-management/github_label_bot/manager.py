from github_label_bot.enums import Operation
from github_label_bot.github_action import GitHubAction

from .process import DownloadFromRemote, SyncUpAsRemote
from .runner import GitHubOperationRunner


class GitHubLabelBot:

    def __init__(self):
        self._github_runner = GitHubOperationRunner()

    def sync_from_remote_repo(self, action_inputs: GitHubAction) -> None:
        self._github_runner.operate_with_github(action_inputs, SyncUpAsRemote())

    def download_from_remote_repo(self, action_inputs: GitHubAction) -> None:
        self._github_runner.operate_with_github(action_inputs, DownloadFromRemote())


def run_bot() -> None:
    github_action_inputs = GitHubAction.from_env()
    bot = GitHubLabelBot()
    print(f"[DEBUG] github_action_inputs.operation: {github_action_inputs.operation}")
    for opt in github_action_inputs.operation:
        if opt is Operation.Sync_UpStream:
            print(f"[DEBUG] run syncup ...")
            bot.sync_from_remote_repo(github_action_inputs)
        elif opt is Operation.Sync_Download:
            print(f"[DEBUG] run download ...")
            bot.download_from_remote_repo(github_action_inputs)
        else:
            raise ValueError(f"Unsupported operation: {opt}")


if __name__ == "__main__":
    run_bot()
