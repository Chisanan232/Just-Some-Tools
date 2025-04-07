import os

from github import Github

token = os.getenv('GITHUB_TOKEN')
github = Github(token)
repo = github.get_repo("Chisanan232/Just-Some-Tools")
labels = repo.get_labels()
e2e_test_label = list(filter(lambda e: e.name == "🤖 e2e test", labels))
assert len(e2e_test_label) == 1
assert e2e_test_label[0].color == "FBCA04"
assert e2e_test_label[0].description == "This label be created by e2e test"
