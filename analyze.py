import json
from collections import defaultdict
from datetime import datetime
from datetime import timedelta
import matplotlib.pyplot as plt
from os import listdir
from os.path import isfile, join
from sys import exit
from matplotlib.dates import MonthLocator, DateFormatter


def label_is(value):
    def check(issue):
        for label in issue.get("labels", []):
            if value == label["name"]:
                return True
        return False
    return check


def integrate(iterable):
    it = iter(iterable)
    try:
        total = next(it)
    except StopIteration:
        return
    yield total
    for element in it:
        total = total + element
        yield total


class Data(object):
    def __init__(self, path, label=None, ignore_pull_requests=False):
        self.fname = path.split('.')[0]
        with open(path) as data_file:
            self.json = json.load(data_file)

        if label is not None:
            self.json = filter(label_is(label), self.json)

        if ignore_pull_requests:
            self.json = filter(lambda x: "pull_request" not in x, self.json)

    @property
    def number_of_comments_per_issue(self):
        """ Number Of Comments Per Issue """
        issues = {"closed": [], "open": []}
        for issue in self.json:
            issues[issue["state"]].append(issue["comments"])
        return issues

    @property
    def days_to_close_issue(self):
        closed_issues = {}
        for issue in self.json:
            if issue['state'] == 'closed':
                created_at = datetime.strptime(issue['created_at'], '%Y-%m-%dT%H:%M:%SZ')
                closed_at = datetime.strptime(issue['closed_at'], '%Y-%m-%dT%H:%M:%SZ')
                closed_issues[issue['id']] = abs((closed_at - created_at).days)
        return closed_issues

    @property
    def number_of_issues_raised_per_contributor(self):
        contributors = defaultdict(lambda: {"open": 0, "closed": 0})
        for issue in self.json:
            contributors[issue["user"]["login"]][issue["state"]] += 1
        return dict(contributors)

    @property
    def number_of_issues_assigned_to_individual(self):
        assignees = defaultdict(lambda: {'name': '', "number": 0})
        for issue in self.json:
            if len(issue['assignees']) > 0:
                for assignee in issue['assignees']:
                    assignees[assignee['id']]['name'] = assignee['login']
                    assignees[assignee['id']]['number'] += 1
        return dict(assignees)

    @property
    def issues_closed_per_milestone(self):
        milestones = {}
        for issue in self.json:
            if type(issue['milestone']) is dict and not issue['milestone']['id'] in milestones:
                milestones[issue['milestone']['id']] = {'name': issue['milestone']['title'],
                                                        'closed': issue['milestone']['closed_issues'],
                                                        'open': issue['milestone']['open_issues']}
        return milestones

    @property
    def issues_per_tag(self):
        labels = defaultdict(lambda: {"name": "", "counter": 0})
        for issue in self.json:
            if len(issue['labels']) > 0:
                for label in issue['labels']:
                    labels[label['id']]['name'] = label['name']
                    labels[label['id']]['counter'] += 1
        return dict(labels)

    @property
    def issues_overtime(self):
        # get date range
        date_min = datetime.max
        date_max = datetime.min
        for issue in self.json:
            created_at = datetime.strptime(issue['created_at'], '%Y-%m-%dT%H:%M:%SZ')
            if created_at < date_min:
                date_min = created_at
            if created_at > date_max:
                date_max = created_at
            if issue['state'] == 'closed':
                closed_at = datetime.strptime(issue['closed_at'], '%Y-%m-%dT%H:%M:%SZ')
                if closed_at > date_max:
                    date_max = created_at

        days = (date_max - date_min).days
        cnt_open = [0] * days
        cnt_closed = [0] * days

        for issue in self.json:
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

    def issue_arrival(self, interval="monthly"):
        a = defaultdict(lambda: 0)

        if interval == "daily":
            for issue in self.json:
                a[datetime.strptime(issue['created_at'], '%Y-%m-%dT%H:%M:%SZ').date()] += 1

        elif interval == "monthly":
            for issue in self.json:
                a[datetime.strptime(issue['created_at'], '%Y-%m-%dT%H:%M:%SZ').date().replace(day=1)] += 1

        return a

    def issue_closure(self, interval="monthly"):
        a = defaultdict(lambda: 0)

        if interval == "daily":
            for issue in self.json:
                if issue['state'] == 'closed':
                    a[datetime.strptime(issue['closed_at'], '%Y-%m-%dT%H:%M:%SZ').date()] += 1

        elif interval == "monthly":
            for issue in self.json:
                if issue['state'] == 'closed':
                    a[datetime.strptime(issue['closed_at'], '%Y-%m-%dT%H:%M:%SZ').date().replace(day=1)] += 1

        return a


class Plot(object):
    def __init__(self, path, label=None, ignore_pull_requests=False):
        self.data = Data(path, label=label, ignore_pull_requests=ignore_pull_requests)

    @staticmethod
    def __plot_histogram(data, xaxis, title):
        plt.figure()
        plt.hist(sorted(data), bins=30)
        plt.xlabel(xaxis)
        plt.ylabel('frequency')
        plt.title(title)
        return plt

    @staticmethod
    def show():
        plt.show()

    def comments_per_issues(self, n_bins=40):
        plt.figure("comments_per_issues")
        plt.title("Comments Per Issue (Histogram)")
        plt.xlabel("# Of Comments")
        plt.ylabel('Issue Frequency')
        d = self.data.number_of_comments_per_issue
        plt.hist([sorted(d['closed']), sorted(d['open'])], bins=n_bins, histtype='barstacked', color=["green", "red"],
                 stacked=True, label=['closed', 'open'])
        plt.legend()

    def days_to_close_issue(self, n_bins=40):
        plt.figure("days_to_close_issue")
        plt.title("Days To Close Issue (Histogram)")
        plt.xlabel("# Of Days")
        plt.ylabel('Issue Frequency')
        d = self.data.days_to_close_issue
        plt.hist(list(d.itervalues()), bins=n_bins, color="green")

    def open_issues_raised_per_contributor(self):
        d = self.data.number_of_issues_raised_per_contributor
        return self.__plot_histogram(map(lambda x: x["open"], d.itervalues()), 'issue raised/contributor', 'Open Issue/Contributor')

    def closed_issues_raised_per_contributor(self):
        d = self.data.number_of_issues_raised_per_contributor
        return self.__plot_histogram(map(lambda x: x["closed"], d.itervalues()), 'issue raised/contributor', 'Closed Issue/Contributor')

    def number_of_issues_assigned_to_individual(self):
        d = self.data.number_of_issues_assigned_to_individual
        return self.__plot_histogram([d[assignee]['number'] for assignee in d], 'issue assigned/Person', 'Issue/Person')

    def issues_closed_per_milestone(self):
        d = self.data.issues_closed_per_milestone
        return self.__plot_histogram([d[milestone]['closed'] for milestone in d], 'issues/milestone', 'Issues/Milestone')

    def issues_per_tag(self):
        d = self.data.issues_per_tag
        return self.__plot_histogram([d[label]['counter'] for label in d], 'issues/tags', 'Issues/Tag')

    def issues_overtime(self):
        d = self.data.issues_overtime
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

    def issue_arrival(self, interval="monthly", show_cumulative=False):
        d = self.data.issue_arrival(interval=interval)
        dates = sorted(d.keys())
        dates = sorted(d.keys())

        defects = [d[x] for x in dates]
        fig, ax = plt.subplots()
        ax.plot_date(dates, defects, '-')
        ax.xaxis.set_major_locator(MonthLocator())
        ax.xaxis.set_major_formatter(DateFormatter('%m/%y'))

        if show_cumulative:
            ax.plot_date(dates, list(integrate(defects)), '-')

        ax.autoscale_view()
        ax.grid(True)
        fig.autofmt_xdate()
        plt.xlabel("Dates")
        plt.ylabel("Issues")
        plt.title("Issue Arrival ({0})".format(interval))
        return plt

    def issue_closure(self, interval="monthly", show_cumulative=False):
        d = self.data.issue_closure(interval=interval)
        dates = sorted(d.keys())
        defects = [d[x] for x in dates]
        fig, ax = plt.subplots()
        ax.plot_date(dates, defects, '-')
        ax.xaxis.set_major_locator(MonthLocator())
        ax.xaxis.set_major_formatter(DateFormatter('%m/%y'))

        if show_cumulative:
            ax.plot_date(dates, list(integrate(defects)), '-')

        ax.autoscale_view()
        ax.grid(True)
        fig.autofmt_xdate()
        plt.xlabel("Dates")
        plt.ylabel("Issues")
        plt.title("Issue Closure ({0})".format(interval))
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
    data_plots = Plot(file_select())
    data_plots.comments_per_issues()
    data_plots.days_to_close_issue()
    data_plots.show()

    #data_plots.open_issues_raised_per_contributor().show()
    #data_plots.closed_issues_raised_per_contributor().show()
    #data_plots.number_of_issues_assigned_to_individual().show()
    #data_plots.time_taken_for_closing_issue().show()
    #data_plots.issues_closed_per_milestone().show()
    #data_plots.issues_per_tag().show()
    #data_plots.issue_arrival(show_cumulative=True).show()

    print


def comments_per_open_issues(self):
    d = self.data.number_of_comments_per_issue
    return self.__plot_histogram(d['open'], 'comments/issue', 'Open Issues')


def comments_per_closed_issues(self):
    d = self.data.number_of_comments_per_issue
    return self.__plot_histogram(d['closed'], 'comments/issue', 'Closed Issues')

