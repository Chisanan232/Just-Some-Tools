from typing import Dict

import github
from github.Label import Label as GitHubLabel
from github.Repository import Repository

from ._utils import YAML
from .model import GitHubLabelManagementConfig, Label as GitHubLabelBotLabel


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
