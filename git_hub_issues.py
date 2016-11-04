import requests  # http://docs.python-requests.org/en/master/
import json


class Repo(object):

    def __init__(self, owner_name, repo_name):
        self.owner_name = owner_name
        self.repo_name = repo_name
        self.path = {"issues": "https://api.github.com/repos/{0}/{1}/issues".format(owner_name, repo_name)}

    def get_issues(self, per_page=100):
        return requests.get(self.path["issues"], params={"per_page": per_page})


if __name__ == '__main__':
    # TODO: save data from each page for URL
    # TODO: Check for rate limit
    repo = Repo("rg3", "youtube-dl")
    r = repo.get_issues()
    print json.dumps(r.json(), sort_keys=True, indent=4, separators=(',', ': '))

    print repo.repo_name
