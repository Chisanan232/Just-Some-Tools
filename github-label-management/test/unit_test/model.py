import re
from abc import ABCMeta, abstractmethod
from typing import Dict, cast, Any

import pytest

from github_label_bot.model import _BaseConfig, Label, GitHubLabelManagementConfig


class _BaseConfigTestSuite(metaclass=ABCMeta):
    @abstractmethod
    @pytest.fixture(scope="function")
    def model(self) -> _BaseConfig:
        pass

    def test_deserialize(self, model: _BaseConfig):
        result = model.deserialize()
        self._verify_deserialized_data(result)

    @abstractmethod
    def _verify_deserialized_data(self, model: Dict[str, str]) -> None:
        pass

    def test_serialize(self, model: _BaseConfig):
        result = model.serialize(data=self._test_data_for_serialize())
        self._verify_serialized_data(result)

    @abstractmethod
    def _test_data_for_serialize(self) -> dict:
        pass

    @abstractmethod
    def _verify_serialized_data(self, model: _BaseConfig) -> None:
        pass


class TestLabel(_BaseConfigTestSuite):
    @pytest.fixture(scope="function")
    def model(self) -> Label:
        data = self._test_data_for_serialize()
        return Label(
            color=data["color"],
            description=data["description"],
        )

    def _verify_deserialized_data(self, model: Dict[str, str]) -> None:
        assert len(model.keys()) == 2
        data = self._test_data_for_serialize()
        assert model["color"] == data["color"]
        assert model["description"] == data["description"]

    def _test_data_for_serialize(self) -> dict:
        return {
            "color": "d73a4a",
            "description": "New feature or request",
        }

    def _verify_serialized_data(self, model: Label) -> None:
        data = self._test_data_for_serialize()
        assert model.color == data["color"]
        assert model.description == data["description"]

    @pytest.mark.parametrize(
        "data",
        [
            {"color": "", "description": ""},
            {"color": None, "description": ""},
            {"color": "", "description": None},
            {"color": None, "description": None},
            {"color": "d73a4a", "description": ""},
            {"color": "", "description": "Bug"},
        ],
    )
    def test_invalid_serialize(self, data: dict):
        with pytest.raises(ValueError) as exc_info:
            Label.serialize(data)
        assert re.search(r"cannot be empty", str(exc_info.value), re.IGNORECASE)


class TestGitHubLabelManagementConfig(_BaseConfigTestSuite):
    @pytest.fixture(scope="function")
    def model(self) -> GitHubLabelManagementConfig:
        data = self._test_data_for_serialize()
        label_models = {}
        for label_k, label_v in data["labels"].items():
            label_models[label_k] = Label.serialize(label_v)
        return GitHubLabelManagementConfig(
            repositories=data["repositories"],
            delete_unused=data["delete_unused"],
            labels=label_models,
        )

    def _verify_deserialized_data(self, model: Dict[str, Any]) -> None:
        assert len(model.keys()) == 3
        data = self._test_data_for_serialize()
        assert model["repositories"] == data["repositories"]
        assert model["delete_unused"] == data["delete_unused"]
        for lk, lv in model["labels"].items():
            assert isinstance(lv, dict)

    def _test_data_for_serialize(self) -> dict:
        return {
            "repositories": ["Chisanan232/repo", "Tester/repo"],
            "delete_unused": False,
            "labels": {
                "new feature": {
                    "color": "a2eeef",
                    "description": "New feature or request",
                },
                "🪲 bug": {
                    "color": "d73a4a",
                    "description": "Bug",
                },
            },
        }

    def _verify_serialized_data(self, model: GitHubLabelManagementConfig) -> None:
        data = self._test_data_for_serialize()
        assert model.repositories == data["repositories"]
        assert model.delete_unused == data["delete_unused"]
        assert model.labels
        for label_name, label_content in model.labels.items():
            filter_labels = list(filter(lambda l: l == label_name, data["labels"].keys()))
            assert len(filter_labels) == 1
            label_setting = data["labels"][filter_labels[0]]
            assert label_content.color == label_setting["color"]
            assert label_content.description == label_setting["description"]

    @pytest.mark.parametrize(
        "data",
        [
            {"repositories": [], "delete_unused": False, "labels": {}},
            {"repositories": None, "delete_unused": False, "labels": {}},
            {"repositories": [], "delete_unused": False, "labels": None},
            {"repositories": [], "delete_unused": False, "labels": {"new feature": {"color": "a2eeef", "description": "New feature or request"}}},
            {"repositories": ["Chisanan232/repo"], "delete_unused": False, "labels": {}},
        ],
    )
    def test_invalid_serialize(self, data: dict):
        with pytest.raises(ValueError) as exc_info:
            Label.serialize(data)
        assert re.search(r"cannot be empty", str(exc_info.value), re.IGNORECASE)
