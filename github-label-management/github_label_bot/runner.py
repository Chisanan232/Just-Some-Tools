import os
import pathlib
from typing import Tuple

import yaml
from github import Github, GithubException

from .github_action import GitHubAction
from .model import GitHubLabelManagementConfig
from .process import BaseProcess


class GitHubOperationRunner:
    def operate_with_github(self, action_inputs: GitHubAction, processor: BaseProcess) -> None:
        # Load GitHub token from environment variable
        print(f"[DEBUG] Get GitHub token.")
        token = self._get_github_token()

        # Initialize GitHub client
        print("[DEBUG] Connect to GitHub ...")
        github = Github(token)

        # Load configuration
        print(f"[DEBUG] Load the configuration.")
        config, repositories = self._force_load_config(action_inputs)

        # Process each repository
        print(f"[DEBUG] Start to sync up the GitHub label setting ...")
        for repo_name in repositories:
            print(f"[DEBUG] Sync GtHub project {repo_name}")
            try:
                repo = github.get_repo(repo_name)
                print(f"\nProcessing repository: {repo_name}")
                processor.process(repo, config)
            except GithubException as e:
                print(f"Error processing {repo_name}: {e}")

    def _get_github_token(self):
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            raise ValueError("GITHUB_TOKEN environment variable not set")
        return token

    def _force_load_config(self, action_inputs: GitHubAction) -> Tuple[GitHubLabelManagementConfig, list[str]]:
        config_path = pathlib.Path(action_inputs.config_path)
        print(f"[DEBUG] action_inputs.config_path: {action_inputs.config_path}")
        if config_path.exists():
            print(f"[DEBUG] Found configuration! Load its settings ...")
            config = self._load_label_config(action_inputs.config_path)
            config.config_path = action_inputs.config_path
            repositories = config.repositories
        else:
            print(f"[DEBUG] Cannot find configuration. Initial empty one ...")
            config = GitHubLabelManagementConfig()
            config.config_path = action_inputs.config_path
            repositories = [os.environ["GITHUB_REPOSITORY"]]
        print(f"[DEBUG] config: {config}")
        return config, repositories

    def _load_label_config(self, config_path: str) -> GitHubLabelManagementConfig:
        """Load label configuration from YAML file."""
        with open(config_path, "r") as file:
            return GitHubLabelManagementConfig.serialize(yaml.safe_load(file))
