import json

with open('data/rg3_youtube-dl_issues.json') as data_file:
    data = json.load(data_file)

users = {}

for x in data:
    if x["user"]["login"] not in users:
        users[x["user"]["login"]] = {"state_count":{}}
    if x["state"] in users[x["user"]["login"]]["state_count"]:
        users[x["user"]["login"]]["state_count"][x["state"]] += 1
    else:
        users[x["user"]["login"]]["state_count"][x["state"]] = 1


for user, value in users.iteritems():
    print user, value


