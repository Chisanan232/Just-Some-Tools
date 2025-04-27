import os
import pathlib
from dataclasses import dataclass
from typing import List

from github_label_bot.enums import Operation


@dataclass
class GitHubAction:
    config_path: str
    operation: List[Operation]

    @staticmethod
    def from_env() -> "GitHubAction":
        config_path_from_env = os.getenv("CONFIG_PATH")
        operations_env = os.getenv("OPERATIONS")
        if not config_path_from_env or not operations_env:
            raise ValueError("Miss required environment variables.")
        return GitHubAction(
            config_path=config_path_from_env, operation=[Operation.to_enum(o) for o in operations_env.split(",")]
        )
