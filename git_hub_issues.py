import requests  # http://docs.python-requests.org/en/master/
import json


class Repo(object):

    def __init__(self, owner_name, repo_name):
        self.owner_name = owner_name
        self.repo_name = repo_name
        self.path = {"issues": "https://api.github.com/repos/{0}/{1}/issues".format(owner_name, repo_name)}
        self.issues = []

    def update_issues(self, starting_page=1):
        r = requests.get(self.path["issues"], params={"per_page": 100, "page": starting_page})

        if r.headers.get("X-RateLimit-Remaining") == "0":
            print "WARNING: Rate Limit Exceeded"
            return self.issues

        self.issues += r.json()
        while r.links.get("next") is not None:
            r = requests.get(r.links["next"]["url"])
            self.issues += r.json()

        if r.headers.get("X-RateLimit-Remaining") == "0":
            print "WARNING: Rate Limit Exceeded"
            return self.issues

        self.issues += r.json()
        return self.issues


if __name__ == '__main__':
    # TODO: save data from each page for URL
    # TODO: Check for rate limit
    repo = Repo("rg3", "youtube-dl")
    r = repo.update_issues()
    print r

