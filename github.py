import requests  # http://docs.python-requests.org/en/master/
from requests.auth import HTTPBasicAuth
import json
import time


class GitHub(object):
    """ Class to interface with GitHub """

    def __init__(self):
        self.session = requests.Session()
        self._repositories = {}
        self._auth = None

    def authenticate(self, username, password):
        """ Authenticate session with GitHub credentials using HTTP Basic Authentication

        For requests using Basic Authentication or OAuth, you can make up to 5,000 requests per hour.
        For unauthenticated requests, the rate limit allows you to make up to 60 requests per hour.
        Unauthenticated requests are associated with your IP address, and not the user making requests.
        Note that the Search API has custom rate limit rules.

        :param username: GitHub Username
        :type username: str

        :param password: GitHub Password
        :type password: str

        :return: True if authentication was successful, False otherwise
        :rtype: Bool

        Note: this method will save the authentication information within this class to be used when making requests

        """
        self._auth = HTTPBasicAuth(username, password)
        return requests.get('https://api.github.com/user', auth=self._auth).status_code == 200

    def repository(self, owner_name, repo_name):
        """ Get Repository Object

        :param owner_name: Repository Owner
        :type owner_name: str

        :param repo_name: Repository Name
        :type repo_name: str

        :return: Repository Object

        """
        # Create new repository obj if repository obj does not yet exist for that repo
        if (owner_name, repo_name) not in self._repositories:
            self._repositories[(owner_name, repo_name)] = Repository(self, owner_name, repo_name)
        return self._repositories[(owner_name, repo_name)]


class Repository(object):
    """ Class to interface with GitHub Repository """

    def __init__(self, github, owner_name, repo_name):
        self.github = github
        self.owner_name = owner_name
        self.repo_name = repo_name
        self.path = "https://api.github.com/repos/{0}/{1}".format(owner_name, repo_name)
        self.issues = []

    def get_issues(self):
        """ Get Repository Issues Using GitHub API """
        # TODO: Re-Implement Rate-Limit Check
        r = requests.get(self.path + "/issues", params={"per_page": 100, "state": "all"}, auth=self.github._auth)
        self.issues += r.json()
        while r.links.get("next") is not None:
            r = requests.get(r.links["next"]["url"], auth=self.github._auth)
            self.issues += r.json()
        return self.issues

    def save_issues(self):
        """ Save Issues Stored In Class To JSON File """
        file_path = "data/{0.owner_name}_{0.repo_name}_issues_{1}.json".format(self, str(int(time.time())))
        with open(file_path, 'w') as outfile:
            json.dump(self.issues, outfile, sort_keys=True, indent=4, separators=(',', ': '))


if __name__ == '__main__':
    """

    EXAMPLE:
    g = GitHub()
    g.authenticate("YOUR_USERNAME", "YOUR_PASSWORD")
    g.repository("REPO_OWNER", "REPO_NAME").get_issues()
    g.repository("REPO_OWNER", "REPO_NAME").save_issues()

    IMPORTANT:
    Don't commit your username/password into github repo!

    """
    pass
