import requests  # http://docs.python-requests.org/en/master/


def get_repository_issues(owner, repo):
    path = "https://api.github.com/repos/{0}/{1}/issues".format(owner, repo)
    return requests.get(path)


# TODO: save data from each page for URL
# TODO: Check for rate limit
print get_repository_issues("rg3", "youtube-dl").headers
