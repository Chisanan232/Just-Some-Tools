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
        config_path = os.getenv("CONFIG_PATH")
        operations_env = os.getenv("OPERATIONS")
        if not operations_env:
            raise ValueError("Environment variable 'OPERATIONS' is not set or empty.")
        return GitHubAction(config_path=config_path, operation=[Operation.to_enum(o) for o in operations_env.split(",")])
