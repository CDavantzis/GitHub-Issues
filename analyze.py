import json
from collections import defaultdict, Counter
from datetime import datetime
import matplotlib.pyplot as plt
from os import listdir
import os.path
from os.path import isfile, join, abspath
from sys import exit
from matplotlib.dates import MonthLocator, DateFormatter
import matplotlib.ticker as mticker

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
    def __init__(self, path, results_path="", label_contains=None, ignore_pull_requests=False):
        self.fname = path.split('.')[0]

        with open(path) as data_file:
            self.json = json.load(data_file)

        if label_contains is not None:
            self.json = filter(label_is(label_contains), self.json)

        if ignore_pull_requests:
            self.json = filter(lambda x: "pull_request" not in x, self.json)

        self.cache = {}

        self.results_path = results_path

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

    def save_issue_data(self):
        with open(self.results_path + "/comments_per_issue.json", 'w') as outfile:
            json.dump(self.get_comments_per_issue(), outfile, sort_keys=True, indent=4, separators=(',', ': '))

        with open(self.results_path + "/days_to_close_issue.json", 'w') as outfile:
            json.dump(self.get_days_to_close_issue(), outfile, sort_keys=True, indent=4, separators=(',', ': '))

        with open(self.results_path + "/assignees_per_issue.json", 'w') as outfile:
            json.dump(self.get_assignees_per_issue(), outfile, sort_keys=True, indent=4, separators=(',', ': '))

        with open(self.results_path + "/issues_assigned_to_contributor.json", 'w') as outfile:
            json.dump(self.get_issues_assigned_to_contributor(), outfile, sort_keys=True, indent=4,
                      separators=(',', ': '))

        with open(self.results_path + "/issues_raised_by_contributor.json", 'w') as outfile:
            json.dump(self.get_issues_raised_by_contributor(), outfile, sort_keys=True, indent=4,
                      separators=(',', ': '))

        with open(self.results_path + "/issues_per_label.json", 'w') as outfile:
            json.dump(self.get_issues_per_label(), outfile, sort_keys=True, indent=4, separators=(',', ': '))

        with open(self.results_path + "/rates_monthly.json", 'w') as outfile:
            d = self.get_daily_rates().copy()
            d["dates"] = map(str, d["dates"])
            json.dump(d, outfile, sort_keys=True, indent=4, separators=(',', ': '))

        with open(self.results_path + "/rates_daily.json", 'w') as outfile:
            d = self.get_daily_rates().copy()
            d["dates"] = map(str, d["dates"])
            json.dump(d, outfile, sort_keys=True, indent=4, separators=(',', ': '))

    def get_comments_per_issue(self):
        """ Number Of Comments Per Issue """
        return self.get_issue_data()["comment_count"]

    def get_days_to_close_issue(self):
        """ Number Of Days To Close Issue """
        return self.get_issue_data()["days_to_close_issue"]

    def get_assignees_per_issue(self):
        """ Number Of Assignees Per Issue """
        return self.get_issue_data()["assignee_count"]

    def get_issues_assigned_to_contributor(self):
        return self.get_issue_data()["issues_per_assignee"]

    def get_issues_raised_by_contributor(self):
        """ Number Of Issues Per Author """
        return self.get_issue_data()["issues_per_author"]

    def get_issues_per_label(self):
        """ Number Of Issues Per Label """
        return self.get_issue_data()["issues_per_label"]

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
        for date, val in sorted(self._get_issue_rates(by_month).iteritems()):
            dates.append(date)
            open.append(val["open"])
            clsd.append(val["closed"])

        cm_open = list(accumulate(open))
        cm_clsd = list(accumulate(clsd))

        return {
            "dates": dates,
            "rates": {"open": open, "closed": clsd},
            "cumulative": {"open": cm_open, "closed": cm_clsd},
            "count": map(operator.sub, cm_open, cm_clsd)
        }

    @cachemethod
    def get_daily_rates(self):
        return self.get_issue_rates(by_month=False)

    @cachemethod
    def get_monthly_rates(self):
        return self.get_issue_rates(by_month=True)


class Plot(object):
    def __init__(self, path, results_path = "", label_contains=None, ignore_pull_requests=False):
        self.file_title = path
        self.data = Data(path, label_contains=label_contains, results_path= result_path, ignore_pull_requests=ignore_pull_requests)

    @staticmethod
    def show_plots():
        """ Show Plots """
        plt.show()

    def _label_current_plot(self, title, xlabel=None, ylabel=None):
        plt.title("{0.file_title}\n{1}".format(self, title))

        if xlabel is not None:
            plt.xlabel(xlabel)

        if ylabel is not None:
            plt.ylabel(ylabel)

    def _save_current_plot(self, f, name):
        full_path = join(self.data.results_path, name)
        f.set_size_inches(16, 9)
        f.savefig(full_path, dpi=199)

    def plot_comments_per_issues(self, n_bins=40):
        """ Plot Number Of Comments Per Issue
        Graph Type: Histogram
        """
        f = plt.figure()
        self._label_current_plot("Comments Per Issue (Histogram)", "# Of Comments", '# Of Issues')
        data = self.data.get_comments_per_issue()
        plt.hist([data['closed'], data['open']], bins=n_bins, stacked=True, histtype='barstacked',
                 color=["green", "red"], label=['closed', 'open'])
        plt.legend()
        self._save_current_plot(f, "comments_per_issue")

    def plot_days_to_close_issue(self, n_bins=40):
        """ Plot Days To Close Issue
        Graph Type: Histogram
        """
        f = plt.figure()
        self._label_current_plot("Days To Close Issue (Histogram)", "# Of Days", '# Of Issues')
        plt.hist(self.data.get_days_to_close_issue(), bins=n_bins, color="green")
        self._save_current_plot(f, "days_to_close_issue")
        f.clf()

    def plot_assignees_per_issues(self):
        """ Plot Assignees Per Issue
        Graph Type: Bar
        """
        f = plt.figure()
        self._label_current_plot("Assignees Per Issue (Bar)", "# Of Assignees", '# Of Issues')
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
        self._save_current_plot(f, "assignees_per_issue")
        f.clf()

    def plot_issues_assigned_to_contributor(self, n_bins=40):
        """ Plot Number of Issues Assigned To Contributor
        Graph Type: Histogram
        """
        f = plt.figure()
        self._label_current_plot("Issues Assigned To Contributor (Histogram)", '# Of Issues', '# Of Contributors')
        data = list(self.data.get_issues_assigned_to_contributor().itervalues())
        plt.hist(data, bins=n_bins, color="green")
        self._save_current_plot(f, "issues_assigned_to_contributor")
        f.clf()

    def plot_issues_raised_by_contributor(self, n_bins=40):
        """ Plot Number of Issues Raised By Contributor
        Graph Type: Histogram
        """
        f = plt.figure()
        self._label_current_plot("Issues Raised By Contributor (Histogram)", '# Of Issues', '# Of Contributors')
        data = list(self.data.get_issues_raised_by_contributor().itervalues())
        plt.hist(data, bins=n_bins, color="red")
        self._save_current_plot(f, "issues_raised_by_contributor")
        f.clf()

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

        f = plt.figure()
        f.set_size_inches(16, 9)
        self._label_current_plot("Open Issues Per Label", "# Of Issues")
        plt.barh(pos, open_counts, align='center', color="red", label="open")
        plt.yticks(pos, labels)
        plt.axis('tight')
        plt.tick_params(axis='y', labelsize=8)
        self._save_current_plot(f, "issues_per_label (Open)")
        f.clf()

        f = plt.figure()
        f.set_size_inches(14, 9)
        self._label_current_plot("Closed Issues Per Label", "# Of Issues")
        plt.barh(pos, closed_counts, align='center', color="green", label="closed")
        plt.yticks(pos, labels)
        plt.axis('tight')
        plt.tick_params(axis='y', labelsize=8)
        self._save_current_plot(f, "issues_per_label (Closed)")
        f.clf()

    def plot_issue_rates(self, by_month=True, show_cumulative=False, show_count=False):
        d = self.data.get_monthly_rates() if by_month else self.data.get_daily_rates()

        fig, ax = plt.subplots()
        fig.set_size_inches(14, 9)

        ax.plot_date(d["dates"], d["rates"]["open"], '-', color="red", label="Arrival")
        ax.plot_date(d["dates"], d["rates"]["closed"], '-', color="green", label="Removal")

        if show_cumulative:
            ax.plot_date(d["dates"], d["cumulative"]["open"], '--', color="red", label="Arrival (cumulative)")
            ax.plot_date(d["dates"], d["cumulative"]["closed"], '--', color="green", label="Removal (cumulative)")

        if show_count:
            ax.plot_date(d["dates"], d["count"], '-', color="blue", label="Count")

        # ax.xaxis.set_major_locator(MonthLocator())
        ax.xaxis.set_major_formatter(DateFormatter('%Y'))
        ax.autoscale_view()
        ax.grid(True)
        fig.autofmt_xdate()
        plt.xlabel("Dates")
        plt.ylabel("Issues")

        plt.legend(loc='upper center', bbox_to_anchor=(0.5, -.1), fancybox=True, shadow=True, ncol=5)
        #plt.legend(loc='upper left', fancybox=True,)

        if by_month:
            if show_cumulative:
                self._label_current_plot("Issues Rates Cumulative (Monthly) ", "Dates", "Issues")
                self._save_current_plot(fig, "rates_monthly_cumulative")
            else:
                self._label_current_plot("Issues Rates (Monthly)", "Dates", "Issues")
                self._save_current_plot(fig, "rates_monthly")
        else:
            if show_cumulative:
                self._label_current_plot("Issues Rates Cumulative (Daily)", "Dates", "Issues")
                self._save_current_plot(fig, "rates_daily_cumulative")
            else:
                self._label_current_plot("Issues Rates (Daily)", "Dates", "Issues")
                self._save_current_plot(fig, "rates_daily")

        fig.clf()


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
    repo_data_list = [("Angular", "angular_angular_issues_1479782810.json"),
                      ("Material Design Lite", "google_material-design-lite_issues_1478412302.json"),
                      ("Emby", "MediaBrowser_Emby_issues_1478411769.json"),
                      ("YouTube-DL", "rg3_youtube-dl_issues_1479788479.json")]

    for repo_name, data_file in repo_data_list:
        # Make sure results folders exist
        data_path = "data/{0}".format(data_file)
        result_path = "results/{0}".format(repo_name)

        if not os.path.exists(result_path):
            os.makedirs(result_path)

        # Load in issues the have a label that contain the word bug.
        plt.clf()
        plotter = Plot(data_path, results_path=result_path, label_contains="bug")

        plotter.data.save_issue_data()
        plotter.plot_comments_per_issues()
        plotter.plot_days_to_close_issue()
        plotter.plot_assignees_per_issues()
        plotter.plot_issues_assigned_to_contributor()
        plotter.plot_issues_raised_by_contributor()
        plotter.plot_issues_per_label()

        plotter.plot_issue_rates(show_count=True, by_month=False)
        plotter.plot_issue_rates(show_count=True, by_month=False, show_cumulative=True)
        plotter.plot_issue_rates(show_count=True, by_month=True)
        plotter.plot_issue_rates(show_count=True, by_month=True, show_cumulative=True)
