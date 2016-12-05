import json
from collections import defaultdict, Counter
from datetime import datetime
import matplotlib.pyplot as plt
from os import listdir
import os.path
from os.path import isfile, join, abspath
from sys import exit
from matplotlib.dates import MonthLocator, DateFormatter
import operator

my_path = abspath(__file__)


def label_is(value):
    def check(issue):
        for label in issue.get("labels", []):
            if value in label["name"]:
                return True
        return False
    return check


def accumulate(iterable):
    it = iter(iterable)
    try:
        total = next(it)
    except StopIteration:
        return
    yield total
    for element in it:
        total = total + element
        yield total


def date_parser(by_month=False):
    if by_month:
        return lambda x: datetime.strptime(x, '%Y-%m-%dT%H:%M:%SZ').date().replace(day=1)
    return lambda x: datetime.strptime(x, '%Y-%m-%dT%H:%M:%SZ').date()

day_parser = date_parser()


def cachemethod(func):
    def wrapper(self, *args):
        if func.__name__ in self.cache:
            return self.cache.get(func.__name__)
        val = func(self, *args)
        self.cache[func.__name__] = val
        return val
    return wrapper


class Data(object):
    def __init__(self, path, label_contains=None, ignore_pull_requests=False):
        self.fname = path.split('.')[0]
        with open(path) as data_file:
            self.json = json.load(data_file)

        if label_contains is not None:
            self.json = filter(label_is(label_contains), self.json)

        if ignore_pull_requests:
            self.json = filter(lambda x: "pull_request" not in x, self.json)

        self.cache = {}

    @cachemethod
    def get_issue_data(self):
        """ Number Of Comments Per Issue """
        comment_count = {"closed": [], "open": []}
        assignee_count = {"closed": [], "open": []}
        days_to_close_issue = []
        labels = defaultdict(lambda: {"open": 0, "closed": 0})

        authors = defaultdict(lambda: 0)
        assignees = defaultdict(lambda: 0)

        for i in self.json:
            comment_count[i["state"]].append(i["comments"])
            assignee_count[i["state"]].append(len(i.get('assignees', [])))
            authors[i["user"]["login"]] += 1

            for label_name in map(lambda x: x.get("name"), i.get("labels", [])):
                labels[label_name][i['state']] += 1

            for assignee in i.get('assignees', []):
                assignees[assignee['login']] += 1

            if i['state'] == 'closed':
                days_to_close_issue.append((day_parser(i['closed_at']) - day_parser(i['created_at'])).days)

        return {"comment_count": comment_count,
                "assignee_count": assignee_count,
                "days_to_close_issue": days_to_close_issue,
                "issues_per_label": dict(labels),
                "issues_per_author": dict(authors),
                "issues_per_assignee": dict(assignees)}

    def get_comments_per_issue(self):
        """ Number Of Assignees Per Issue """
        return self.get_issue_data()["comment_count"]

    def get_assignees_per_issue(self):
        """ Number Of Assignees Per Issue """
        return self.get_issue_data()["assignee_count"]

    def get_days_to_close_issue(self):
        """ Number Of Days To Close Issue """
        return self.get_issue_data()["days_to_close_issue"]

    def get_issues_per_label(self):
        """ Number Of Issues Per Label """
        return self.get_issue_data()["issues_per_label"]

    def get_issues_per_author(self):
        """ Number Of Issues Per Author """
        return self.get_issue_data()["issues_per_author"]

    def get_issues_per_assignee(self):
        return self.get_issue_data()["issues_per_assignee"]

    def _get_issue_rates(self, by_month=False):
        """ Issue Rate Data """
        parse = date_parser(by_month)
        a = defaultdict(lambda: {'closed': 0, 'open': 0})
        for issue in self.json:
            a[parse(issue['created_at'])]["open"] += 1
            if issue['state'] == 'closed':
                a[parse(issue['closed_at'])]["closed"] += 1
        return a

    def get_issue_rates(self, by_month=False):
        """ Issue Rate Graph Data """
        dates, open, clsd = [], [], []
        max_open_x, max_open_y = 0, 0
        for date, val in sorted(self._get_issue_rates(by_month).iteritems()):
            dates.append(date)
            if val["open"] > max_open_y:
                max_open_y = val["open"]
                max_open_x = date
            open.append(val["open"])
            clsd.append(val["closed"])

        return {"dates": dates,
                "rates": {"open": open, "closed": clsd},
                "max": {"open": (max_open_x, max_open_y)}}


class Plot(object):
    def __init__(self, path, label_contains=None, ignore_pull_requests=False):
        self.data = Data(path, label_contains=label_contains, ignore_pull_requests=ignore_pull_requests)

    @staticmethod
    def show_plots():
        """ Show Plots """
        plt.show()

    def plot_comments_per_issues(self, n_bins=40):
        """ Plot Number Of Comments Per Issue
        Graph Type: Histogram
        """
        plt.figure("comments_per_issues_histogram")
        plt.title("Comments Per Issues (Histogram)")
        plt.xlabel("# Of Comments")
        plt.ylabel('# Of Issues')

        data = self.data.get_comments_per_issue()

        plt.hist([data['closed'], data['open']],
                 bins=n_bins,
                 stacked=True,
                 histtype='barstacked',
                 color=["green", "red"],
                 label=['closed', 'open'])

        plt.legend()

    def plot_days_to_close_issue(self, n_bins=40):
        """ Plot Days To Close Issue
        Graph Type: Histogram
        """
        plt.figure("days_to_close_issue")
        plt.title("Days To Close Issue (Histogram)")
        plt.xlabel("# Of Days")
        plt.ylabel('# Of Issues')
        plt.hist(self.data.get_days_to_close_issue(), bins=n_bins, color="green")

    def plot_assignees_per_issues(self):
        """ Plot Assignees Per Issue
        Graph Type: Bar
        """
        plt.figure("assignees_per_issues_bar")
        plt.title("Assignees Per Issue (Bar)")
        plt.xlabel("# Of Assignees")
        plt.ylabel('# Of Issues')

        d = self.data.get_assignees_per_issue()
        c = Counter(d['closed'])
        o = Counter(d['open'])

        x_max = max(c.keys()) if c.keys() else 0
        if o.keys():
            x_max = max(x_max, max(o.keys()))

        x = range(x_max)
        c_y = map(lambda m: c.get(m, 0), x)
        o_y = map(lambda m: o.get(m, 0), x)

        plt.bar(x, c_y, width=.5, align='center', color='g', label='closed')
        plt.bar(x, o_y, width=.5, align='center', color='r', label='open', bottom=c_y)
        plt.xticks(x)
        plt.legend()

    def plot_issues_assigned_to_contributor(self, n_bins=40):
        """ Plot Number of Issues Assigned To Contributor
        Graph Type: Histogram
        """
        plt.figure("issues_assigned_to_contributor_histogram")
        plt.title("Issues Assigned To Contributor (Histogram)")
        plt.xlabel("# Of Issues")
        plt.ylabel('# Of Contributors')
        data = list(self.data.get_issues_per_assignee().itervalues())
        plt.hist(data, bins=n_bins, color="green")

    def plot_issues_raised_by_contributor(self, n_bins=40):
        """ Plot Number of Issues Raised By Contributor
        Graph Type: Histogram
        :param n_bins:

        """
        plt.figure("issues_raised_by_contributor_histogram")
        plt.title("Issues Raised By Contributor (Histogram)")
        plt.xlabel("# Of Issues")
        plt.ylabel('# Of Contributors')
        data = list(self.data.get_issues_per_author().itervalues())
        plt.hist(data, bins=n_bins, color="red")

    def plot_issues_per_label(self):
        """ Plot Issues Per Label

        Graph Type: Horizontal Bar Graph

        """
        labels = []
        open_counts = []
        closed_counts = []

        for label, count in sorted(self.data.get_issues_per_label().iteritems(), reverse=True):
            labels.append(label)
            open_counts.append(count["open"])
            closed_counts.append(count["closed"])

        pos = [x + .5 for x in range(len(labels))]

        plt.figure("open_issues_per_label")
        plt.title("Open Issues Per Label")
        plt.xlabel("# Of Issues")
        plt.barh(pos, open_counts, align='center', color="red", label="open")
        plt.yticks(pos, labels)
        plt.axis('tight')

        plt.figure("closed_issues_per_label")
        plt.title("Closed Issues Per Label")
        plt.xlabel("# Of Issues")
        plt.barh(pos, closed_counts, align='center', color="green", label="closed")
        plt.yticks(pos, labels)
        plt.axis('tight')

    def plot_issue_rates(self, by_month=True, show_cumulative=False, show_count=False, show_tm=False):
        d = self.data.get_issue_rates(by_month)
        fig, ax = plt.subplots()

        ax.plot_date(d["dates"], d["rates"]["open"], '-', color="red", label="Arrival")
        ax.plot_date(d["dates"], d["rates"]["closed"], '-', color="green", label="Removal")

        cm_open = list(accumulate(d["rates"]["open"]))
        cm_clsd = list(accumulate(d["rates"]["closed"]))
        cm_diff = map(operator.sub, cm_open, cm_clsd)

        if show_cumulative:
            ax.plot_date(d["dates"], cm_open, '--', color="red", label="Arrival (cumulative)")
            ax.plot_date(d["dates"], cm_clsd, '--', color="green", label="Removal (cumulative)")

        if show_count:
            ax.plot_date(d["dates"], cm_diff, '-', color="blue", label="Count")

        if show_tm:
            ax.annotate("Tm", xy=d["max"]["open"], xycoords='data', xytext=(-15, 15), textcoords='offset points',
                        arrowprops=dict(arrowstyle="-"))

        ax.xaxis.set_major_locator(MonthLocator())
        ax.xaxis.set_major_formatter(DateFormatter('%m/%y'))
        ax.autoscale_view()
        ax.grid(True)
        fig.autofmt_xdate()
        plt.xlabel("Dates")
        plt.ylabel("Issues")

        if by_month:
            plt.title("Issues Rates (Monthly)")
        else:
            plt.title("Issues Rates (Daily)")

        plt.legend(loc='upper center', bbox_to_anchor=(0.5, -.1), fancybox=True, shadow=True, ncol=5)

        #print " ".join(map(str, d["dates"]))
        #print " ".join(map(str, d["rates"]["open"]))
        #print " ".join(map(str, d["rates"]["closed"]))
        #print " ".join(map(str, cm_open))
        #print " ".join(map(str, cm_clsd))
        #print " ".join(map(str, cm_diff))


def file_select():
    """ Select File To Analyze """
    file_list = [f for f in listdir("data") if isfile(join("data", f))]

    if len(file_list) == 0:
        exit("Exit - No files to analyze")

    print("Select file to analyze:")
    for num, name in enumerate(file_list):
        print(" > [{0}] - {1}".format(num + 1, name))

    sel = input("Input Number: ")
    return "data/{0}".format(file_list[sel-1]), "figures/{0}".format(file_list[sel-1])

if __name__ == '__main__':
    file_path, figure_path = file_select()

    if not os.path.exists(figure_path):
        os.makedirs(figure_path)

    plotter = Plot(file_path, label_contains="bug")

    plotter.plot_comments_per_issues()
    plotter.plot_assignees_per_issues()
    plotter.plot_days_to_close_issue()
    plotter.plot_issues_assigned_to_contributor()
    plotter.plot_issues_raised_by_contributor()
    plotter.plot_issues_per_label()

    # Issue Rate Line Graphs
    plotter.plot_issue_rates(show_tm=True, show_count=True, by_month=False)
    plotter.plot_issue_rates(show_tm=True, show_count=True, by_month=False, show_cumulative=True)
    plotter.plot_issue_rates(show_tm=True, show_count=True, by_month=True)
    plotter.plot_issue_rates(show_tm=True, show_count=True, by_month=True, show_cumulative=True)

    for n in plt.get_fignums():
        f = plt.figure(n)
        f.savefig(join(figure_path, "fig_sm_{0:02d}".format(n)), dpi=199)
        f.set_size_inches(32, 18)
        f.savefig(join(figure_path, "fig_lg_{0:02d}".format(n)), dpi=199)

    plotter.show_plots()
