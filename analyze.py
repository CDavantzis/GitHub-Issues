import json
from collections import defaultdict
from datetime import datetime
from itertools import groupby
import numpy as np
import matplotlib.pyplot as plt


class Issues(object):
    def __init__(self, path):
        self.fname=path.split('.')[0]
        with open(path) as data_file:
            self.json = json.load(data_file)

    def histo(self,data,fname,xaxis,title):
        plt.figure()
        plt.hist(sorted(data))
        plt.xlabel(xaxis)
        plt.ylabel('frequency')
        plt.title(title)
        plt.savefig('graphs/'+fname+'.png')

    @property
    def number_of_comments_per_issue(self): 
        issues = {"closed": [], "open": []}
        for issue in self.json:
            issues[issue["state"]].append(issue["comments"])
        self.histo(issues['open'],'open_issues','comments/issue','Open Issues')
        self.histo(issues['closed'],'closed_issues','comments/issue','Closed Issues')
        return issues

    @property
    def number_of_issues_raised_per_contributor(self):
        contributors = defaultdict(lambda: {"open": 0, "closed": 0})
        for issue in self.json:
            contributors[issue["user"]["login"]][issue["state"]] += 1
        return dict(contributors)

    @property
    def number_of_issues_assigned_to_individual(self):
        assingees=defaultdict(lambda:{'name':'',"number":0})
        for issue in self.json:
            if len(issue['assignees'])>0:
                for assignee in issue['assignees']:
                    assignees[assignee['id']]['name']=assignee['login']
                    assignees[assignee['id']]['number']+=1
        return dict(assignees)

    @property 
    def time_taken_for_closing_issue(self):
        closed_issues={}
        for issue in self.json:
            if issue['state']=='closed':
                closed_issues[issue['id']]=abs((datetime.strptime(issue['closed_at'],'%Y-%m-%dT%H:%M:%SZ')-datetime.strptime(issue['created_at'],'%Y-%m-%dT%H:%M:%SZ')).days)
        return closed_issues

    @property
    def issues_closed_per_milestone(self):
        milestones={}
        for issue in self.json:
            if type(issue['milestone']) is dict and not issue['milestone']['id'] in milestones:
                milestones[issue['milestone']['id']]={'name':issue['milestone']['title'],'closed':issue['milestone']['closed_issues'],'open':issue['milestone']['open_issues']}
        return milestones


    @property
    def issues_per_tag(self):
        labels=defaultdict(lambda:{"name":"","counter":0})
        for issue in self.json:
             if len(issue['labels'])>0:
                for label in issue['labels']:
                    labels[label['id']]['name']=label['name']
                    labels[label['id']]['counter']+=1
        self.histo([labels[label]['counter'] for label in dict(labels)],'issues_per_tag','issues/tags','Issues/Tag')
        return dict(labels)


if __name__ == '__main__':
    i = Issues('data/angular_angular_issues_1478462251.json')
    i.number_of_comments_per_issue
    # print i.number_of_issues_raised_per_contributor
    # print i.time_taken_for_closing_issue
    # print i.issues_closed_per_milestone
    i.issues_per_tag
    # print i.number_of_issues_assigned_to_individual