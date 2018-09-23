from datetime import datetime, timedelta
import time
from math import floor, ceil

# DAYS={1:"mon",2:"tue",3:"wed",4:"thu",5:"fri",6:"sat",7:"sun"}
DAYS = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
DAYSS = dict((v, k) for k, v in DAYS.iteritems())


class Job():
    def __init__(self, start_time, end_time, days, interval, job, jobArgs=[]):
        if isinstance(start_time, basestring):
            try:
                start_time = datetime.strptime(start_time, "%H:%M:%S")
                # start_time=time.strptime(start_time, "%H:%M:%S")
            except ValueError as e:
                print "start time not in HH:MM:SS format."
        self.start_time = start_time
        if isinstance(end_time, basestring):
            try:
                end_time = datetime.strptime(end_time, "%H:%M:%S")
                # end_time=time.strptime(end_time, "%H:%M:%S")
            except ValueError as e:
                print "end time not in HH:MM:SS format."
        self.end_time = end_time
        if isinstance(days, basestring):
            days = days.split(",")

        self.days = days
        self.dayss = []
        for day in days:
            self.dayss.append(DAYSS[day])

        print "dayss:", self.dayss

        if isinstance(interval, basestring):
            if interval.endswith("m"):
                interval = interval.replace("m", "")
                interval = 60 * int(interval)
            elif interval.endswith("s"):
                interval = interval.replace("s", "")
                interval = int(interval)
            elif interval.endswith("h"):
                interval = interval.replace("h", "")
                interval = 60 * 60 * int(interval)
            else:
                interval = int(interval)

        self.interval = interval
        self.job = job
        self.jobArgs = jobArgs
        self.calc_next_run()

    def get_days_as_string(self):
        days = []
        for day in self.days:
            days.append(DAYS[day])
        return ",".join(days)

    def info(self):
        st = self.start_time.strftime("%H:%M:%S")
        et = self.end_time.strftime("%H:%M:%S")
        nr = self.next_run.strftime("%d/%m/%Y %H:%M:%S")
        # st=time.strftime("%H:%M:%S", self.start_time)
        # et=time.strftime("%H:%M:%S", self.end_time)
        interval = str(self.interval)
        # days = ",".join(self.days)
        # days=self.get_days_as_string()
        print "On %s from %s till %s every %s sec." % (self.days, st, et, interval)
        print "Next run:", nr, "on day",self.next_day

    def calc_next_run(self):
        now = datetime.now()
        self.next_run = now
        nowtime = datetime.now().replace(year=1900, day=1, month=1)
        today = now.strftime("%a").lower()
        today_num = now.weekday()

        # print "now:",nowtime
        # print "st :",self.start_time
        # print "et :",self.end_time
        # print "int:",self.interval/60

        # if today_num in self.days:
        #     if nowtime > self.end_time:
        #         print "already over"
        #         return

        ##################

        if nowtime > self.start_time:
            print "already started"
            dt = nowtime - self.start_time
            # print "dt:",dt.total_seconds()
            dtr = self.interval * (1 + floor(dt.total_seconds() / self.interval))
            nr = self.start_time + timedelta(seconds=dtr)
            print "Next run %s:" % today, nr
            # print "overshot in sec:",dt.total_seconds()
            # print "overshot round down:",dtr
            if nr > self.end_time:
                print "next run overshoots end time"
            self.next_run = nr
        else:
            print "not yet"
            self.next_run = self.start_time
        # print "next run:", self.next_run

        print "days:",self.days
        print "today num:", today_num



        d2c_thisWeek = [d for d in self.days if d >= today_num]
        d2c_nextWeek = [d for d in self.days if d < today_num]

        self.next_day = None

        if len(d2c_thisWeek)>0:
            if nowtime > self.end_time:
                if len(d2c_thisWeek)>1:
                    self.next_day=d2c_thisWeek[1]
                else:
                    if len(d2c_nextWeek) > 0:
                        self.next_day = d2c_nextWeek[0]
                    else:
                        print "No valid days"

            else:
                self.next_day = d2c_thisWeek[0]
        else:
            if len(d2c_nextWeek)>0:
                self.next_day = d2c_nextWeek[0]
            else:
                print "No valid days"

    def run(self):
        self.job(self.jobArgs)


class MyScheduler:
    def __init__(self, threaded=False):
        self.jobIndex = 0
        self.threaded = threaded
        self.jobs = {}
        self.jobGroups = {}

    def schedule(self, job, group=None):
        jobIndex = self.jobIndex
        self.jobs[jobIndex] = job
        self.jobIndex += 1
        if group is not None:
            if group in self.jobGroups:
                self.jobGroups[group].append(group)
            else:
                self.jobGroups[group] = [group]

        return jobIndex

    def clear(self, group=None, jobIndex=None):
        if jobIndex is not None and jobIndex in self.jobs:
            del self.jobs[jobIndex]
            print "removed job Index", jobIndex
            return
        if group is not None and group in self.jobGroups:
            print "removing all jobs in group", group
            for job in self.jobGroups[group]:
                del self.jobs[job]
                print "removed job Index", jobIndex
            del self.jobGroups[group]

    def run_pending(self):
        for i, job in self.jobs.iteritems():
            print i, job.start

def test_job():
    print "run test job"

if __name__ == '__main__':
    schedular = MyScheduler()

    job1 = Job(start_time="17:50:00", end_time="22:50:00", days=[6, 0], interval="5m", job=test_job, jobArgs="aap")
    job1.info()
