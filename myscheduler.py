import threading
import time
from datetime import datetime, timedelta
from math import floor

DAYS = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
DAYSS = dict((v, k) for k, v in DAYS.iteritems())

class Job():
    def __init__(self, start_time, end_time, days, interval, job, jobArgs=[], now=None):
        self.now = now
        self.job_thread = None

        if isinstance(start_time, basestring):
            try:
                start_time = datetime.strptime(start_time, "%H:%M:%S")
            except ValueError as e:
                print "start time not in HH:MM:SS format."
        self.start_time = start_time
        if isinstance(end_time, basestring):
            try:
                end_time = datetime.strptime(end_time, "%H:%M:%S")
            except ValueError as e:
                print "end time not in HH:MM:SS format."
        self.end_time = end_time
        if isinstance(days, basestring):
            days = days.split(",")

        self.dayss = []
        self.days = []
        self.id = None

        for day in days:
            if isinstance(day, int):
                self.dayss.append(DAYSS[day])
                self.days.append(day)
            elif isinstance(day, basestring):
                self.dayss.append(day)
                self.days.append(DAYS[day])

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
        interval = str(self.interval)
        today_num = datetime.now().weekday()

        dummy = "[%s] %s from %s till %s every %s sec run job %s(%s)" % (
        self.group, ", ".join(self.dayss), st, et, interval, self.job.__name__, str(self.jobArgs))
        dummy += ", Next run: %s (%s)" % (
        self.next_run.strftime("%a %d-%m-%Y %H:%M:%S"), "this week" if today_num <= self.next_day else "next week")

        if datetime.now().replace(year=1900, day=1, month=1) > self.start_time and self.next_day == datetime.now().weekday():
            dummy += " [ACTIVE]"
        else:
            dummy += " [PENDING]"

        if self.now is not None:
            dummy += " TEST with now as %s" % (self.now)

        return dummy

    def calc_next_run(self):
        now = datetime.now()
        self.next_run = now
        nowtime = datetime.now().replace(year=1900, day=1, month=1)
        today_num = now.weekday()

        if nowtime > self.start_time:
            dt = nowtime - self.start_time
            dtr = self.interval * (1 + floor(dt.total_seconds() / self.interval))
            nr = self.start_time + timedelta(seconds=dtr)
            # if nr > self.end_time:
            #     print "WARN: next run overshoots end time"
            self.next_run = nr
        else:
            self.next_run = self.start_time

        d2c_thisWeek = [d for d in self.days if d >= today_num]
        d2c_nextWeek = [d for d in self.days if d < today_num]
        self.next_day = None

        def calc_day(day, next_week=False):
            self.next_day = day
            today = datetime.today()
            if next_week:
                _day = today + timedelta((day - today.weekday()) % 7)
                self.next_run = self.next_run.replace(year=_day.year, day=_day.day, month=_day.month)
            else:
                _day = today + timedelta((day - today.weekday()) % 7)
                self.next_run = self.next_run.replace(year=_day.year, day=_day.day, month=_day.month)

        if len(d2c_thisWeek) > 0:
            if nowtime > self.end_time:
                if len(d2c_thisWeek) > 1:
                    calc_day(next_week=False, day=d2c_thisWeek[1])
                else:
                    if len(d2c_nextWeek) > 0:
                        calc_day(next_week=True, day=d2c_nextWeek[0])
                    else:
                        print "No valid days"
            else:
                calc_day(next_week=False, day=d2c_thisWeek[0])
        else:
            if len(d2c_nextWeek) > 0:
                calc_day(next_week=True, day=d2c_nextWeek[0])
            else:
                print "No valid days"

    def run(self):
        self.job(self.jobArgs)


class MyScheduler:
    def __init__(self, threaded=False, skip_unfinished_jobs=True):
        self.jobIndex = 0
        self.threaded = threaded
        self.jobs = {}
        self.jobsByGroups = {}
        self.skip_unfinished_jobs = skip_unfinished_jobs

    def schedule(self, job, group=None):
        jobIndex = self.jobIndex
        job.id = jobIndex

        if group is None:
            group = "default"

        job.group = group

        self.jobs[jobIndex] = job
        self.jobIndex += 1
        if group is not None:
            if group in self.jobsByGroups:
                self.jobsByGroups[group].append(job)
            else:
                self.jobsByGroups[group] = [job]

        return jobIndex

    def run_job(self, id):
        if self.skip_unfinished_jobs:
            if self.jobs[id].job_thread is None:
                self.jobs[id].job_thread = threading.Thread(target=self.jobs[id].job, args=[self.jobs[id].jobArgs])
                self.jobs[id].job_thread.start()
            else:
                if not self.jobs[id].job_thread.isAlive():
                    self.jobs[id].job_thread = threading.Thread(target=self.jobs[id].job, args=[self.jobs[id].jobArgs])
                    self.jobs[id].job_thread.start()
                else:
                    print "WARN: Skipping job.id", id
        else:
            dontcare = threading.Thread(target=self.jobs[id].job, args=[self.jobs[id].jobArgs])
            dontcare.start()

    def clear(self, group=None, id=None):
        if id is not None and id in self.jobs:
            del self.jobs[id]
        elif group is not None and group in self.jobsByGroups:
            for job in self.jobsByGroups[group]:
                if job.id in self.jobs:
                    del self.jobs[job.id]
            self.jobsByGroups[group]=[]

    def start(self):
        if self.threaded:
            self._mainThread = threading.Thread(target=self._threaded)
            self._mainThread.start()
        else:
            self._threaded()

    def stop(self):
        self.running=False
        if self.threaded:
            self._mainThread.join()

    def check_jobs(self):
        for id, job in self.jobs.iteritems():
            # print id,job.next_run, datetime.now(), job.next_run < datetime.now()
            if job.next_run < datetime.now():
                self.run_job(id)
                job.calc_next_run()

    def _threaded(self):
        self.running = 1
        while self.running:
            time.sleep(1)
            self.check_jobs()

    def run_pending(self):
        for i, job in self.jobs.iteritems():
            print i, job.start

    def info(self):
        if len(self.jobs):
            print "[ JOBS at %s]" % datetime.now().strftime("%a %d-%m-%Y %H:%M:%S")
            for id, job in self.jobs.iteritems():
                if id != job.id:
                    print "! %3d %s" % (id, job.info())
                else:
                    print "  %3d %s" % (id, job.info())
        else:
            print "No jobs."

def test_job(param):
    print ">> starting %s"%param

if __name__ == '__main__':
    schedular = MyScheduler(threaded=True, skip_unfinished_jobs = True)
    job1 = Job(start_time="9:50:00", end_time="11:33:00", days=["thu", "tue"], interval="3s", job=test_job, jobArgs="3sec job", now="09-25-2018 17:50:00")
    job2 = Job(start_time="11:33:00", end_time="11:34:00", days=["thu", "tue"], interval="5s", job=test_job, jobArgs="5sec job", now="09-25-2018 17:50:00")
    job3 = Job(start_time="11:34:00", end_time="11:35:00", days=["thu", "tue"], interval="8s", job=test_job, jobArgs="8sec job", now="09-25-2018 17:50:00")
    schedular.schedule(job1, group="camera1")
    schedular.schedule(job2, group="camera1")
    schedular.schedule(job3, group="camera1")
    schedular.info()
    schedular.start()
    time.sleep(3000000)
    schedular.stop()
    print "Done."
