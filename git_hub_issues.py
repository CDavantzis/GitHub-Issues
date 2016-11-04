import requests  # http://docs.python-requests.org/en/master/
import json


def get_repository_issues(owner, repo, per_page=100):
    path = "https://api.github.com/repos/{0}/{1}/issues".format(owner, repo)
    return requests.get(path, params={"per_page": per_page})


# TODO: save data from each page for URL
# TODO: Check for rate limit
r = get_repository_issues("rg3", "youtube-dl")
