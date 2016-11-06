import json
from collections import defaultdict


class Issues(object):
    def __init__(self, path):
        with open(path) as data_file:
            self.json = json.load(data_file)

    @property
    def number_of_comments_per_issue(self):
        issues = {"closed": [], "open": []}
        for issue in self.json:
            issues[issue["state"]].append(issue["comments"])
        return issues

    @property
    def number_of_issues_raised_per_contributor(self):
        contributors = defaultdict(lambda: {"open": 0, "closed": 0})
        for issue in self.json:
            contributors[issue["user"]["login"]][issue["state"]] += 1
        return dict(contributors)


if __name__ == '__main__':
    i = Issues('data/rg3_youtube-dl_issues_1478409904.json')
    print i.number_of_comments_per_issue
    print i.number_of_issues_raised_per_contributor
