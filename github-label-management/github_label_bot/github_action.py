import pathlib
from dataclasses import dataclass

import os
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

        config_path = pathlib.Path(config_path_from_env)
        if not config_path.exists():
            config_path.touch()
        return GitHubAction(config_path=str(config_path), operation=[Operation.to_enum(o) for o in operations_env.split(",")])
