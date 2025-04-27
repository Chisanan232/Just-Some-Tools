import os
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class _BaseConfig(metaclass=ABCMeta):

    @abstractmethod
    def deserialize(self) -> Dict:
        pass

    @staticmethod
    @abstractmethod
    def serialize(data: Dict) -> "_BaseConfig":
        pass


@dataclass
class Label(_BaseConfig):
    color: str
    description: str

    def deserialize(self) -> Dict:
        return {
            "color": self.color,
            "description": self.description,
        }

    @staticmethod
    def serialize(data: Dict[str, str]) -> "Label":
        color = data.get("color", "")
        description = data.get("description", "")
        if not color:
            raise ValueError("Property *color* or *description* cannot be empty.")
        return Label(
            color=color,
            description=description,
        )


@dataclass
class GitHubLabelManagementConfig(_BaseConfig):
    repositories: List[str] = field(default_factory=list)
    delete_unused: bool = False
    labels: Dict[str, Label] = field(default_factory=dict)

    # inner usage
    config_path: str = field(default_factory=str)

    def __post_init__(self):
        if self.labels:
            labels = {}
            for lk, lv in self.labels.items():
                if isinstance(lv, Label):
                    labels[lk] = lv.deserialize()
                else:
                    labels[lk] = lv

    def deserialize(self) -> Dict:
        labels_config = {}
        for label_name, label_config in self.labels.items():
            labels_config[label_name] = label_config.deserialize()
        return {
            "repositories": self.repositories or [],
            "delete_unused": self.delete_unused,
            "labels": labels_config or {},
        }

    @staticmethod
    def serialize(data: Dict) -> "GitHubLabelManagementConfig":
        repositories = data.get("repositories", [os.environ["GITHUB_REPOSITORY"]])
        delete_unused = data.get("delete_unused", False)
        labels = data.get("labels", {})
        if not (repositories or labels):
            raise ValueError("Property *repositories* or *labels* cannot be empty.")
        labels_models = {}
        for k, v in labels.items():
            labels_models[k] = Label.serialize(v)
        return GitHubLabelManagementConfig(
            repositories=repositories,
            delete_unused=delete_unused,
            labels=labels_models,
        )
