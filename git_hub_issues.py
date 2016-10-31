import requests 


def get_repository_issues(owner, repo):
	path = "https://api.github.com/repos/{0}/{1}/issues".format(owner, repo)
	return requests.get(path)


print get_repository_issues("rg3", "youtube-dl").headers