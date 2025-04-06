import os

from github import Github

from github_label_bot._utils import YAML
from github_label_bot.model import GitHubLabelManagementConfig

github_management_config = GitHubLabelManagementConfig.serialize(YAML().read("./github-label-management/test/_data/e2e-test.yaml"))

token = os.getenv('GITHUB_TOKEN')
github = Github(token)
repo = github.get_repo("Chisanan232/Just-Some-Tools")
labels = repo.get_labels()
for label_name, label_config in github_management_config.labels.items():
    exist_label = list(filter(lambda l: l.name == label_name, labels))
    assert exist_label
    assert label_name == exist_label[0].name
    assert label_config.color == exist_label[0].color
    assert label_config.description == exist_label[0].description
