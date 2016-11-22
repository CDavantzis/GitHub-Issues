import json
from collections import defaultdict
from datetime import datetime
from datetime import timedelta
import matplotlib.pyplot as plt
from os import listdir
from os.path import isfile, join
from sys import exit
from matplotlib.dates import MonthLocator, DateFormatter


def label_contains(issue, value):
    for label in issue.get("labels", []):
        if value == label["name"]:
            return True
    return False


class Issues(object):
    def __init__(self, path):
        self.fname = path.split('.')[0]
        with open(path) as data_file:
            self.json = json.load(data_file)

    def histo(self, data, fname, xaxis, title):
        plt.figure()
        plt.hist(sorted(data), bins=30)
        plt.xlabel(xaxis)
        plt.ylabel('frequency')
        plt.title(title)
        plt.savefig('graphs/' + fname + '.png')

    @property
    def number_of_comments_per_issue(self):
        issues = {"closed": [], "open": []}
        for issue in self.json:

            # ignore pull requests
            #if 'pull_request' in issue:
            #    continue

            issues[issue["state"]].append(issue["comments"])
        self.histo(issues['open'], 'open_issues', 'comments/issue', 'Open Issues')
        self.histo(issues['closed'], 'closed_issues', 'comments/issue', 'Closed Issues')
        return issues

    @property
    def number_of_issues_raised_per_contributor(self):
        contributors = defaultdict(lambda: {"open": 0, "closed": 0})
        for issue in self.json:

            # ignore pull requests
            #if 'pull_request' in issue:
            #    continue

            contributors[issue["user"]["login"]][issue["state"]] += 1
        self.histo([contributors[cont]['closed'] for cont in dict(contributors)], 'issues_raised',
                   'issue raised/contributor', 'Issue/Contributor')
        return dict(contributors)

    @property
    def number_of_issues_assigned_to_individual(self):
        assignees = defaultdict(lambda: {'name': '', "number": 0})
        for issue in self.json:

            # ignore pull requests
            #if 'pull_request' in issue:
            #    continue

            if len(issue['assignees']) > 0:
                for assignee in issue['assignees']:
                    assignees[assignee['id']]['name'] = assignee['login']
                    assignees[assignee['id']]['number'] += 1
        self.histo([assignees[assignee]['number'] for assignee in dict(assignees)], 'issues_assigned',
                   'issue assigned/Person', 'Issue/Person')
        return dict(assignees)

    @property
    def time_taken_for_closing_issue(self):
        closed_issues = {}
        for issue in self.json:

            # ignore pull requests
            #if 'pull_request' in issue:
            #    continue

            if issue['state'] == 'closed':
                closed_issues[issue['id']] = abs((datetime.strptime(issue['closed_at'],
                                                                    '%Y-%m-%dT%H:%M:%SZ') - datetime.strptime(
                    issue['created_at'], '%Y-%m-%dT%H:%M:%SZ')).days)
        self.histo([closed_issues[ids] for ids in closed_issues], 'time_for_closing', 'timetaken/issue',
                   'Time taken to Close')
        return closed_issues

    @property
    def issues_closed_per_milestone(self):
        milestones = {}
        for issue in self.json:
            if type(issue['milestone']) is dict and not issue['milestone']['id'] in milestones:
                milestones[issue['milestone']['id']] = {'name': issue['milestone']['title'],
                                                        'closed': issue['milestone']['closed_issues'],
                                                        'open': issue['milestone']['open_issues']}
        self.histo([milestones[milestone]['closed'] for milestone in milestones], 'issues_closed_milestone',
                   'issues/milestone', 'Issues/Milestone')
        return milestones

    @property
    def issues_per_tag(self):
        labels = defaultdict(lambda: {"name": "", "counter": 0})
        for issue in self.json:

            # ignore pull requests
            #if 'pull_request' in issue:
            #    continue

            if len(issue['labels']) > 0:
                for label in issue['labels']:
                    labels[label['id']]['name'] = label['name']
                    labels[label['id']]['counter'] += 1
        self.histo([labels[label]['counter'] for label in dict(labels)], 'issues_per_tag', 'issues/tags', 'Issues/Tag')
        return dict(labels)

    @property
    def date_range(self):
        date_min = datetime.max
        date_max = datetime.min
        for issue in self.json:

            # ignore pull requests
            #if 'pull_request' in issue:
            #    continue

            #if not label_contains(issue, "bug"):
            #    continue

            created_at = datetime.strptime(issue['created_at'], '%Y-%m-%dT%H:%M:%SZ')
            if created_at < date_min:
                date_min = created_at
            if created_at > date_max:
                date_max = created_at
            if issue['state'] == 'closed':
                closed_at = datetime.strptime(issue['closed_at'], '%Y-%m-%dT%H:%M:%SZ')
                if closed_at > date_max:
                    date_max = created_at
        return date_min, date_max

    @property
    def issues_overtime(self):
        date_min, date_max = self.date_range
        days = (date_max - date_min).days
        cnt_open = [0] * days
        cnt_closed = [0] * days

        for issue in self.json:

            # ignore pull requests
            #if 'pull_request' in issue:
            #    continue

            #if not label_contains(issue, "bug"):
            #    continue

            created_at = datetime.strptime(issue['created_at'], '%Y-%m-%dT%H:%M:%SZ')
            day = (created_at - date_min).days

            while day < days:
                cnt_open[day] += 1
                day += 1

            if issue['state'] == 'closed':
                closed_at = datetime.strptime(issue['closed_at'], '%Y-%m-%dT%H:%M:%SZ')
                day = (closed_at - date_min).days
                while day < days:
                    cnt_open[day] -= 1
                    cnt_closed[day] += 1
                    day += 1

        return {"dates": [date_min + timedelta(days=x) for x in range(days)],
                "open": cnt_open, "closed": cnt_closed}

    @property
    def issue_arrival_daily(self):
        a = defaultdict(lambda: 0)
        for issue in self.json:
            #if not label_contains(issue, "bug"):
            #    continue
            date = datetime.strptime(issue['created_at'], '%Y-%m-%dT%H:%M:%SZ').date()
            a[date] += 1
        return a

    @property
    def issue_arrival_monthly(self):
        a = defaultdict(lambda: 0)
        for issue in self.json:
            #if not label_contains(issue, "bug"):
            #    continue
            date = datetime.strptime(issue['created_at'], '%Y-%m-%dT%H:%M:%SZ').date()
            a[date.replace(day=1)] += 1
        return a

    @property
    def issues_overtime_plot(self):
        d = self.issues_overtime
        fig, ax = plt.subplots()
        ax.plot_date(d["dates"], d["open"], '-')
        ax.xaxis.set_major_locator(MonthLocator())
        ax.xaxis.set_major_formatter(DateFormatter('%m/%y'))
        ax.autoscale_view()
        ax.grid(True)
        fig.autofmt_xdate()
        plt.xlabel("Dates")
        plt.ylabel("Issues")
        plt.title("Issues Overtime")
        return plt

    @property
    def issue_arrival_daily_plot(self):
        d = self.issue_arrival_daily
        dates = sorted(d.keys())
        defects = [d[x] for x in dates]
        fig, ax = plt.subplots()
        ax.plot_date(dates, defects, '-')
        ax.xaxis.set_major_locator(MonthLocator())
        ax.xaxis.set_major_formatter(DateFormatter('%m/%y'))
        ax.autoscale_view()
        ax.grid(True)
        fig.autofmt_xdate()
        plt.xlabel("Dates")
        plt.ylabel("Issues")
        plt.title("Issue Arrival (Daily)")
        return plt

    @property
    def issue_arrival_monthly_plot(self):
        d = self.issue_arrival_monthly
        dates = sorted(d.keys())
        defects = [d[x] for x in dates]
        fig, ax = plt.subplots()
        ax.plot_date(dates, defects, '-')
        ax.xaxis.set_major_locator(MonthLocator())
        ax.xaxis.set_major_formatter(DateFormatter('%m/%y'))
        ax.autoscale_view()
        ax.grid(True)
        fig.autofmt_xdate()
        plt.xlabel("Dates")
        plt.ylabel("Issues")
        plt.title("Issue Arrival (Monthly)")
        return plt


def file_select():
    """ Select File To Analyze """
    file_list = [f for f in listdir("data") if isfile(join("data", f))]

    if len(file_list) == 0:
        exit("Exit - No files to analyze")

    print("Select file to analyze:")
    for num, name in enumerate(file_list):
        print(" > [{0}] - {1}".format(num + 1, name))

    sel = input("Input Number: ")
    return "data/{0}".format(file_list[sel-1])


if __name__ == '__main__':
    i = Issues(file_select())
    i.issue_arrival_monthly_plot.show()
    #print i.number_of_comments_per_issue
    #print i.number_of_issues_raised_per_contributor
    #print i.time_taken_for_closing_issue
    #print i.issues_closed_per_milestone
    #print i.issues_per_tag
    #print i.number_of_issues_assigned_to_individual
    print

