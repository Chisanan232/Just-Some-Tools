import os
from collections.abc import Callable
from typing import Mapping, Dict, Tuple

import yaml
import github
from github import Github
from github.Label import Label as GitHubLabel
from github.Repository import Repository

from .model import GitHubLabelManagementConfig, Label as GitHubLabelBotLabel
from ._utils.file.operation import YAML


class SyncProcess:

    def sync_labels(self, repo: Repository, label_config: GitHubLabelManagementConfig) -> None:
        """Synchronize repository labels with configuration."""
        # Get existing labels
        existing_labels: Dict[str, GitHubLabel] = {label.name: label for label in repo.get_labels()}

        # Update or create labels
        for name, props in label_config.labels.items():
            if name in existing_labels:
                label = existing_labels[name]
                if (label.color != props.color or
                    label.description != props.description):
                    label.edit(
                        name=name,
                        color=props.color,
                        description=props.description
                    )
                    print(f"Updated label: {name}")
            else:
                repo.create_label(
                    name=name,
                    color=props.color,
                    description=props.description
                )
                print(f"Created label: {name}")

        # Delete labels not in config if specified
        if label_config.delete_unused:
            for name, label in existing_labels.items():
                if name not in label_config.labels:
                    label.delete()
                    print(f"Deleted label: {name}")


class DownloadProcess:

    def download_labels(self, repo: github.Repository) -> None:
        existing_labels: Dict[str, GitHubLabel] = {label.name: label for label in repo.get_labels()}
        labels_config: Dict[str, GitHubLabelBotLabel] = {}
        for label_name, label_info in existing_labels.items():
            print(f"[DEBUG] Sync label {label_name}!")
            labels_config[label_name] = GitHubLabelBotLabel(
                color=label_info.color,
                description=label_info.description,
            )
        config = GitHubLabelManagementConfig(
            repositories=[repo.full_name],
            labels=labels_config,
        )
        print("[DEBUG] All labels has been sync!")
        print(f"[DEBUG] Config: {config}")
        YAML().write(path="./test/_data/github-labels.yaml", mode="w+", config=config.deserialize())
        print("[DEBUG] Download GitHub label config finish!")


class GitHubLabelBot:

    def _load_label_config(self, config_path: str) -> GitHubLabelManagementConfig:
        """Load label configuration from YAML file."""
        with open(config_path, 'r') as file:
            return GitHubLabelManagementConfig.serialize(yaml.safe_load(file))


    def syncup_as_config(self) -> None:

        def _sync_process(_repo, _config) -> None:
            SyncProcess().sync_labels(_repo, _config)

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
            DownloadProcess().download_labels(_repo)

        self._operate_with_github(_download_process)
