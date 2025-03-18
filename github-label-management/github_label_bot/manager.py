import os
from collections.abc import Callable

import yaml
from github import Github
from github.Repository import Repository

from .model import GitHubLabelManagementConfig
from .process import SyncUpAsRemote, DownloadFromRemote


class GitHubLabelBot:

    def _load_label_config(self, config_path: str) -> GitHubLabelManagementConfig:
        """Load label configuration from YAML file."""
        with open(config_path, 'r') as file:
            return GitHubLabelManagementConfig.serialize(yaml.safe_load(file))


    def syncup_as_config(self) -> None:

        def _sync_process(_repo, _config) -> None:
            SyncUpAsRemote().process(_repo, _config)

        self._operate_with_github(_sync_process)

    def _operate_with_github(self, callback: Callable[[Repository, GitHubLabelManagementConfig], None]) -> None:
        # Load GitHub token from environment variable
        print(f"[DEBUG] Get GitHub token.")
        token = self._get_github_token()

        # Initialize GitHub client
        print("[DEBUG] Connect to GitHub ...")
        github = Github(token)

        # Load configuration
        print(f"[DEBUG] Load the configuration.")
        config = self._load_label_config('./test/_data/github-labels.yaml')

        # Process each repository
        print(f"[DEBUG] Start to sync up the GitHub label setting ...")
        for repo_name in config.repositories:
            print(f"[DEBUG] Sync GtHub project {repo_name}")
            try:
                repo = github.get_repo(repo_name)
                print(f"\nProcessing repository: {repo_name}")
                callback(repo, config)
            except github.GithubException as e:
                print(f"Error processing {repo_name}: {e}")


    def _get_github_token(self):
        token = os.getenv('GITHUB_TOKEN')
        if not token:
            raise ValueError("GITHUB_TOKEN environment variable not set")
        return token


    def download_as_config(self) -> None:

        def _download_process(_repo, _config) -> None:
            DownloadFromRemote().process(_repo)

        self._operate_with_github(_download_process)
